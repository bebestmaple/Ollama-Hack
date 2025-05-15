from fastapi import BackgroundTasks, Depends, HTTPException, status
from fastapi_pagination import Page, Params, set_page
from fastapi_pagination.ext.sqlmodel import apaginate
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from sqlmodel import col, select

from src.ai_model.models import (
    AIModelDB,
    AIModelPerformanceDB,
    AIModelStatusEnum,
    EndpointAIModelDB,
)
from src.core.dependencies import DBSessionDep
from src.database import sessionmanager
from src.logging import get_logger
from src.ollama.performance_test import EndpointTestResult, test_endpoint

from .models import EndpointDB
from .schemas import (
    EndpointAIModelInfo,
    EndpointBatchCreate,
    EndpointCreate,
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
) -> list[EndpointDB]:
    """
    Create or update multiple endpoints.
    """

    result_endpoints: list[EndpointDB] = []

    for endpoint_create in endpoint_batch.endpoints:
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

        result_endpoints.append(endpoint)

    await session.commit()

    # Refresh all endpoints to get their IDs
    for endpoint in result_endpoints:
        await session.refresh(endpoint)
        if endpoint.id is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate endpoint ID",
            )
        # Add background task to test each endpoint
        background_tasks.add_task(test_and_update_endpoint_and_models, endpoint.id)

    return result_endpoints


async def get_models_by_endpoint_id(
    session: DBSessionDep,
    endpoint_id: int,
    params: Params = Depends(),
) -> Page[AIModelDB]:
    """
    Get all AI models associated with an endpoint.
    """
    set_page(Page[AIModelDB])

    # Query AI Models through the association table
    query = (
        select(AIModelDB)
        .options(selectinload(AIModelDB.performances))  # type: ignore
        .join(EndpointAIModelDB)
        .where(
            (EndpointAIModelDB.ai_model_id == AIModelDB.id)
            & (EndpointAIModelDB.endpoint_id == endpoint_id)
        )
    )

    return await apaginate(session, query, params)


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
    params: Params = Depends(),
) -> Page[EndpointDB]:
    """
    Get all endpoints. If user is admin, get all endpoints, otherwise get only user's endpoints.
    """
    set_page(Page[EndpointDB])
    query = select(EndpointDB).options(selectinload(EndpointDB.performances))  # type: ignore
    return await apaginate(session, query, params)


async def create_or_update_endpoint(
    session: DBSessionDep,
    endpoint_create: EndpointCreate,
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

    await session.delete(endpoint)
    await session.commit()


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
        try:
            # 创建或获取模型
            model = await create_ai_model_if_not_exists(session, model_performance.ai_model)

            if model.id is None:
                continue

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
        recent_performances=endpoint_performances,
        ai_models=Page(
            items=ai_models,
            total=links.total,
            page=links.page,
            size=links.size,
        ),
    )


async def get_endpoints_with_ai_model_counts(
    session: DBSessionDep, endpoints_page: Page[EndpointDB] = Depends(get_endpoints)
) -> Page[EndpointWithAIModelCount]:
    """
    Get all endpoints with AI model counts.
    """
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
        query = query.where(EndpointAIModelDB.status == AIModelStatusEnum.AVAILABLE)
        result = await session.execute(query)
        avaliable_ai_model_count = result.scalar_one()

        # Create the endpoint with counts
        endpoints_with_counts.append(
            EndpointWithAIModelCount(
                id=endpoint.id,
                url=endpoint.url,
                name=endpoint.name,
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
    )
