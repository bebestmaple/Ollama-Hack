from fastapi import BackgroundTasks, Depends, HTTPException, status
from fastapi_pagination import Page, Params, set_page
from fastapi_pagination.ext.sqlmodel import apaginate
from sqlalchemy import func, or_
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import selectinload
from sqlmodel import col, select

from src.ai_model.models import (
    AIModelDB,
    AIModelPerformanceDB,
    AIModelStatusEnum,
    EndpointAIModelDB,
)
from src.database import DBSessionDep, sessionmanager
from src.logging import get_logger
from src.ollama.performance_test import EndpointTestResult, test_endpoint
from src.schema import SortOrder

from .models import EndpointDB
from .schemas import (
    EndpointAIModelInfo,
    EndpointBatchCreate,
    EndpointCreateWithName,
    EndpointFilterParams,
    EndpointPerformanceInfo,
    EndpointUpdate,
    EndpointWithAIModelCount,
    EndpointWithAIModels,
    EndpointWithAIModelsRequest,
)

logger = get_logger(__name__)


async def get_endpoint_by_id(session: DBSessionDep, endpoint_id: int) -> EndpointDB:
    """
    Get an endpoint by ID.
    """
    query = select(EndpointDB).options(selectinload(EndpointDB.performances))  # type: ignore

    query = query.where(EndpointDB.id == endpoint_id)

    result = await session.execute(query)
    endpoint = result.scalars().first()
    if endpoint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint not found")
    return endpoint


async def batch_create_or_update_endpoints(
    session: DBSessionDep,
    endpoint_batch: EndpointBatchCreate,
    background_tasks: BackgroundTasks,
) -> None:
    """
    Create or update multiple endpoints.
    """
    # 提取所有 URL
    urls = [ep.url for ep in endpoint_batch.endpoints]

    # 1. 查询已存在的 URL
    result = await session.execute(
        select(EndpointDB.url, EndpointDB.id).where(col(EndpointDB.url).in_(urls))
    )
    existing = {row[0]: row[1] for row in result.all()}

    # 2. 过滤出未存在的 URL
    new_urls = [url for url in urls if url not in existing]

    # 3. 批量插入新 URL
    new_ids = []
    if new_urls:
        # 构建插入数据
        to_insert = [{"url": url} for url in new_urls]
        await session.execute(insert(EndpointDB).values(to_insert))
        await session.commit()

        # 查询新插入的记录的 ID
        result = await session.execute(
            select(EndpointDB.url, EndpointDB.id).where(col(EndpointDB.url).in_(new_urls))
        )
        new_ids = [row[1] for row in result.all()]

    # 4. 合并所有 ID
    all_ids = list(existing.values()) + new_ids

    # 添加后台任务
    for eid in all_ids:
        background_tasks.add_task(test_and_update_endpoint_and_models, eid)


async def get_endpoint_by_url(session: DBSessionDep, url: str) -> EndpointDB:
    """
    Get an endpoint by URL.
    """
    result = await session.execute(select(EndpointDB).where(EndpointDB.url == url))
    endpoint = result.scalars().first()
    if endpoint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint not found")
    return endpoint


async def get_endpoints(
    session: DBSessionDep,
    params: EndpointFilterParams = Depends(),
) -> Page[EndpointDB]:
    """
    Get all endpoints with filtering, searching and sorting.

    params:
        - search: Optional search string for name or URL
        - order_by: Field to sort by
        - order: Sort order (asc or desc)
    """
    set_page(Page[EndpointDB])
    query = select(EndpointDB).options(selectinload(EndpointDB.performances))  # type: ignore

    # 添加搜索条件
    if params.search:
        search_term = f"%{params.search}%"
        query = query.where(
            or_(col(EndpointDB.name).ilike(search_term), col(EndpointDB.url).ilike(search_term))
        )

    # 添加排序
    if params.order_by:
        # 处理基本字段排序
        order_column = getattr(EndpointDB, params.order_by.value)
        if params.order == SortOrder.DESC:
            order_column = order_column.desc()
        query = query.order_by(order_column)

    if params.status:
        query = query.where(EndpointDB.status == params.status)

    return await apaginate(session, query, params)


async def create_or_update_endpoint(
    session: DBSessionDep,
    endpoint_create: EndpointCreateWithName,
    background_tasks: BackgroundTasks,
) -> EndpointDB:
    """
    Create a new endpoint.
    """
    # Check if the endpoint already exists
    try:
        endpoint = await get_endpoint_by_url(session, endpoint_create.url)
    except HTTPException:
        endpoint = None
    if endpoint:
        # Update the endpoint
        endpoint_data = endpoint_create.model_dump()
        for key, value in endpoint_data.items():
            setattr(endpoint, key, value)
    else:
        # Create a new endpoint
        endpoint = EndpointDB(**endpoint_create.model_dump())
        session.add(endpoint)
    await session.commit()
    await session.refresh(endpoint)
    if endpoint.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate endpoint ID",
        )
    background_tasks.add_task(test_and_update_endpoint_and_models, endpoint.id)
    return endpoint


async def update_endpoint(
    session: DBSessionDep,
    endpoint_id: int,
    endpoint_update: EndpointUpdate,
) -> EndpointDB:
    """
    Update an endpoint. Only admin or the owner can update it.
    """
    endpoint = await get_endpoint_by_id(session, endpoint_id)

    # Update fields
    update_data = endpoint_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(endpoint, key, value)

    await session.commit()
    await session.refresh(endpoint)
    return endpoint


async def delete_endpoint(
    session: DBSessionDep,
    endpoint_id: int,
) -> None:
    """
    Delete an endpoint. Only admin or the owner can delete it.
    """
    endpoint = await get_endpoint_by_id(session, endpoint_id)

    # 确保加载关联数据以激活级联删除
    await session.refresh(endpoint, ["ai_model_links", "performances"])

    logger.info(f"Deleting endpoint {endpoint.id} ({endpoint.name}) with all its relations")

    await session.delete(endpoint)
    await session.commit()
    logger.info(f"Endpoint {endpoint_id} deleted successfully")


async def get_ai_model_by_name_and_tag(
    session: DBSessionDep,
    name: str,
    tag: str,
) -> AIModelDB:
    """
    Get an AI model by name and tag.
    """
    result = await session.execute(
        select(AIModelDB).where(AIModelDB.name == name, AIModelDB.tag == tag)
    )
    ai_model = result.scalars().first()
    if ai_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI model not found")
    return ai_model


async def create_ai_model_if_not_exists(
    session: DBSessionDep,
    ai_model: AIModelDB,
) -> AIModelDB:
    """
    Create an AI model if it does not exist.
    """
    try:
        return await get_ai_model_by_name_and_tag(session, ai_model.name, ai_model.tag)
    except HTTPException:
        # If the AI model does not exist, create it
        pass

    session.add(ai_model)
    await session.commit()
    await session.refresh(ai_model)
    return ai_model


async def process_endpoint_test_result(
    session: DBSessionDep,
    endpoint_id: int,
    results: EndpointTestResult,
) -> None:
    """
    Process the endpoint test result.
    """
    if results.endpoint_performance:
        endpoint = await get_endpoint_by_id(session, endpoint_id)
        endpoint.status = results.endpoint_performance.status
        session.add(endpoint)
        results.endpoint_performance.endpoint_id = endpoint_id
        session.add(results.endpoint_performance)
        await session.commit()
        await session.refresh(results.endpoint_performance)


async def process_models_test_results(
    session: DBSessionDep,
    endpoint_id: int,
    results: EndpointTestResult,
) -> None:
    """
    Test all models of an endpoint and update their performance metrics.
    """
    performances = []
    links = []

    existing_associations = (
        select(EndpointAIModelDB)
        .where(EndpointAIModelDB.endpoint_id == endpoint_id)
        .options(
            selectinload(EndpointAIModelDB.ai_model),  # type: ignore
            selectinload(EndpointAIModelDB.performances),  # type: ignore
        )
    )
    existing_result = await session.execute(existing_associations)
    existing_link_map = {row.ai_model.id: row for row in existing_result.scalars().all()}

    mission_model_ids = list(existing_link_map.keys())
    for model_performance in results.model_performances:
        # 创建或获取模型
        model = await create_ai_model_if_not_exists(session, model_performance.ai_model)

        if model.id is None:
            continue

        try:
            performance = model_performance.performance
            if performance:
                performance.ai_model_id = model.id
                performance.endpoint_id = endpoint_id
                performances.append(performance)

            # 如果关系不存在且ID有效，则创建关联表条目
            if model.id not in existing_link_map:
                link = EndpointAIModelDB(endpoint_id=endpoint_id, ai_model_id=model.id)
                existing_link_map[model.id] = link
            # 如果关系存在，则更新关联表条目
            else:
                link = existing_link_map[model.id]
                await session.refresh(link)

            # 添加性能数据
            if performance:
                link.performances.append(performance)
                link.status = performance.status
                link.token_per_second = performance.token_per_second
                if performance.connection_time is not None and link.max_connection_time is not None:
                    link.max_connection_time = max(
                        link.max_connection_time,
                        performance.connection_time,
                    )
                else:
                    link.max_connection_time = performance.connection_time

            # 添加关联表条目
            links.append(link)
            mission_model_ids.remove(model.id)
        except Exception as e:
            logger.error(
                f"Error processing model {model_performance.ai_model.name}:{model_performance.ai_model.tag}: {e}"
            )
            continue

    for model_id in mission_model_ids:
        link = existing_link_map[model_id]
        link.status = AIModelStatusEnum.MISSING
        links.append(link)
        performance = AIModelPerformanceDB(
            endpoint_id=endpoint_id,
            ai_model_id=model_id,
            status=AIModelStatusEnum.MISSING,
        )
        performances.append(performance)

    # 批量添加所有关联和性能数据
    if links:
        session.add_all(links)
    if performances:
        session.add_all(performances)


async def test_and_update_endpoint_and_models(
    endpoint_id: int,
) -> None:
    """
    Test an endpoint and update its performance metrics.
    """
    async with sessionmanager.session() as session:
        endpoint_query = select(EndpointDB).where(EndpointDB.id == endpoint_id)
        result = await session.execute(endpoint_query)
        endpoint = result.scalars().first()

        if endpoint is None:
            logger.error(f"Endpoint with ID {endpoint_id} not found")
            return None

        results = await test_endpoint(endpoint)

        await process_endpoint_test_result(session, endpoint_id, results)
        await process_models_test_results(session, endpoint_id, results)

        await session.commit()

        return


async def get_best_endpoint_for_model(
    session: DBSessionDep,
    model_id: int,
) -> EndpointDB:
    """
    Get the best endpoint for a model.
    """
    query = (
        select(EndpointAIModelDB)
        .options(selectinload(EndpointAIModelDB.endpoint))  # type: ignore
        .where(
            EndpointAIModelDB.ai_model_id == model_id,
            EndpointAIModelDB.status == AIModelStatusEnum.AVAILABLE,
        )
    )
    query = query.order_by(col(EndpointAIModelDB.token_per_second).desc())
    result = await session.execute(query)
    endpoint_model_association = result.scalars().first()
    if endpoint_model_association is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endpoint not found")
    return endpoint_model_association.endpoint


async def get_ai_model_links_by_endpoint_id(
    session: DBSessionDep,
    endpoint_id: int,
    params: Params = Depends(),
) -> Page[EndpointAIModelDB]:
    """
    Get all AI model links for an endpoint with pagination.
    """
    await get_endpoint_by_id(session, endpoint_id)

    set_page(Page[EndpointAIModelDB])

    # Base query to get AI models through the association table
    query = (
        select(EndpointAIModelDB)
        .options(
            selectinload(EndpointAIModelDB.ai_model),  # type: ignore
            selectinload(EndpointAIModelDB.performances),  # type: ignore
        )
        .where(EndpointAIModelDB.endpoint_id == endpoint_id)
    )

    return await apaginate(session, query, params)


async def get_endpoint_with_ai_models(
    session: DBSessionDep,
    request: EndpointWithAIModelsRequest = Depends(),
) -> EndpointWithAIModels:
    """
    Get an endpoint by ID with its associated AI models.
    """
    endpoint = await get_endpoint_by_id(session, request.endpoint_id)
    links = await get_ai_model_links_by_endpoint_id(session, request.endpoint_id, request)

    # Get recent performances
    recent_performances = endpoint.performances[:10] if endpoint.performances else []
    endpoint_performances = [
        EndpointPerformanceInfo(
            id=perf.id,
            status=perf.status,
            ollama_version=perf.ollama_version,
            created_at=perf.created_at,
        )
        for perf in recent_performances
    ]

    # Transform the AI models
    ai_models = []
    for link in links.items:
        if not link.ai_model:
            continue

        # Ensure ID is not None
        model_id = link.ai_model.id
        if model_id is None:
            continue

        ai_models.append(
            EndpointAIModelInfo(
                id=model_id,
                name=link.ai_model.name,
                tag=link.ai_model.tag,
                created_at=link.ai_model.created_at,
                status=link.status,
                token_per_second=link.token_per_second,
                max_connection_time=link.max_connection_time,
            )
        )

    # Create the response object
    return EndpointWithAIModels(
        id=endpoint.id,
        url=endpoint.url,
        name=endpoint.name,
        created_at=endpoint.created_at,
        status=endpoint.status,
        recent_performances=endpoint_performances,
        ai_models=Page(
            items=ai_models,
            total=links.total,
            page=links.page,
            size=links.size,
            pages=links.pages,
        ),
    )


async def get_endpoints_with_ai_model_counts(
    session: DBSessionDep, filter_params: EndpointFilterParams = Depends()
) -> Page[EndpointWithAIModelCount]:
    """
    Get all endpoints with AI model counts, with support for filtering, searching and sorting.
    """
    endpoints_page = await get_endpoints(session, filter_params)

    endpoints_with_counts = []

    for endpoint in endpoints_page.items:
        # Get the recent performances
        recent_performances = endpoint.performances[:1] if endpoint.performances else []
        endpoint_performances = [
            EndpointPerformanceInfo(
                id=perf.id,
                status=perf.status,
                ollama_version=perf.ollama_version,
                created_at=perf.created_at,
            )
            for perf in recent_performances
        ]

        # Count total AI models
        query = select(func.count()).where(EndpointAIModelDB.endpoint_id == endpoint.id)
        result = await session.execute(query)
        total_ai_model_count = result.scalar_one()

        # Count available AI models
        query = select(func.count()).where(
            EndpointAIModelDB.endpoint_id == endpoint.id,
            EndpointAIModelDB.status == AIModelStatusEnum.AVAILABLE,
        )
        result = await session.execute(query)
        avaliable_ai_model_count = result.scalar_one()

        # Create the endpoint with counts
        endpoints_with_counts.append(
            EndpointWithAIModelCount(
                id=endpoint.id,
                url=endpoint.url,
                name=endpoint.name,
                created_at=endpoint.created_at,
                status=endpoint.status,
                recent_performances=endpoint_performances,
                total_ai_model_count=total_ai_model_count,
                avaliable_ai_model_count=avaliable_ai_model_count,
            )
        )

    # Return paginated results
    return Page(
        items=endpoints_with_counts,
        total=endpoints_page.total,
        page=endpoints_page.page,
        size=endpoints_page.size,
        pages=endpoints_page.pages,
    )
