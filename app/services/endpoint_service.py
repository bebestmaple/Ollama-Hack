import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Tuple

import httpx
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.crud import crud_endpoint, crud_model, crud_performance
from app.db.database import SessionLocal
from app.models.models import Endpoint
from app.schemas.schemas import PerformanceTestCreate

logger = get_logger(__name__)

# 创建一个全局的数据库锁
db_lock = threading.Lock()


def check_endpoint_availability(url: str, timeout: int = 10) -> Tuple[bool, float]:
    start_time = time.time()
    try:
        with httpx.Client(timeout=timeout, verify=False) as client:
            response = client.get(f"{url}/api/tags")
            elapsed = (time.time() - start_time) * 1000  # 转换为毫秒
            if response.status_code == 200:
                return True, elapsed
    except Exception as e:
        logger.error(f"Error checking endpoint {url}: {str(e)}")
    return False, 0


def get_endpoint_models(url: str, timeout: int = 10) -> List[str]:
    try:
        with httpx.Client(timeout=timeout, verify=False) as client:
            response = client.get(f"{url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [model["name"] for model in models]
    except Exception as e:
        logger.error(f"Error getting models from endpoint {url}: {str(e)}")
    return []


def test_endpoint_performance(
    endpoint_id: int,
    model_name: str,
    prompt: str = """将以下内容，翻译成现代汉语：先帝创业未半而中道崩殂，今天下三分，益州疲弊，此诚危急存亡之秋也。""",
    timeout: int = 30,
) -> Optional[Dict[str, float]]:
    db = SessionLocal()
    try:
        logger.info(
            f"Testing performance for model {model_name} on endpoint {endpoint_id}"
        )
        endpoint = crud_endpoint.get_endpoint_by_id(db, endpoint_id)
        if not endpoint or not endpoint.is_available:
            return None

        url = endpoint.url

        # 测试生成速度
        start_time = time.time()
        tokens_generated = 0
        with httpx.Client(timeout=timeout, verify=False) as client:
            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "max_tokens": 100,
            }
            response = client.post(f"{url}/api/generate", json=payload)
            if response.status_code == 200:
                result = response.json()
                if "fake" in result.get("response", "") or "models" in result:
                    logger.warning(f"Endpoint {endpoint_id} is fake")
                    logger.debug(f"Fake Response from ep {endpoint_id}@{url}: {result}")
                    crud_endpoint.update_endpoint_status(
                        db, endpoint_id, False, 0, True
                    )
                    return None
                tokens_generated = result.get("eval_count", 0) or len(
                    result.get("response", "").split()
                )
                elapsed = time.time() - start_time
                tokens_per_second = tokens_generated / elapsed if elapsed > 0 else 0
                response_time = elapsed * 1000  # 转换为毫秒
                logger.info(
                    f"Performance test completed: {tokens_generated} tokens in {elapsed:.2f} seconds ({tokens_per_second:.2f} tps)"
                )
                return {
                    "tokens_per_second": tokens_per_second,
                    "response_time": response_time,
                }
    except Exception as e:
        logger.error(f"Error testing endpoint performance: {str(e)}")
    finally:
        db.close()

    return None


def check_single_endpoint(endpoint: Endpoint, db: Session):
    try:
        is_available, response_time = check_endpoint_availability(endpoint.url)
        with db_lock:
            crud_endpoint.update_endpoint_status(
                db, endpoint.id, is_available, response_time
            )

        # 如果端点可用，获取并更新支持的模型
        if is_available:
            model_names = get_endpoint_models(endpoint.url)
            with db_lock:
                for model_name in model_names:
                    model = crud_model.get_or_create_model(db, model_name)
                    crud_endpoint.associate_endpoint_with_model(
                        db, endpoint.id, model.id
                    )

            # 创建并发测试模型性能的任务
            performance_tasks = []
            with db_lock:
                for model_name in model_names:
                    model = crud_model.get_model_by_name(db, model_name)
                    if model:
                        performance_tasks.append((endpoint.id, model_name, model.id))

            # 并发执行所有模型的性能测试（最大 5 个线程）
            if performance_tasks:
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = [
                        executor.submit(
                            test_and_update_model_performance,
                            endpoint.id,
                            task[1],
                            task[2],
                        )
                        for task in performance_tasks
                    ]
                    for future in futures:
                        future.result()
    except Exception as e:
        logger.error(f"Error checking endpoint: {str(e)}")


def test_and_update_model_performance(endpoint_id: int, model_name: str, model_id: int):
    db = SessionLocal()
    try:
        performance = test_endpoint_performance(endpoint_id, model_name)
        with db_lock:
            if performance:
                test_data = PerformanceTestCreate(
                    endpoint_id=endpoint_id,
                    model_id=model_id,
                    tokens_per_second=performance["tokens_per_second"],
                    response_time=performance["response_time"],
                )
                crud_performance.create_performance_test(db, test_data)

                # 更新首选端点（如果尚未手动设置）
                if not crud_model.get_model_by_id(db, model_id).preferred_endpoint_id:
                    best_endpoint = crud_performance.get_best_endpoint_for_model(
                        db, model_id
                    )
                    if best_endpoint:
                        crud_model.update_preferred_endpoint(
                            db, model_id, best_endpoint.id
                        )
            else:
                crud_performance.delete_performance_test_if_exists(
                    db, model_id, endpoint_id
                )
    except Exception as e:
        logger.error(
            f"Error testing performance for model {model_name} on endpoint {endpoint_id}: {str(e)}"
        )
    finally:
        db.close()


def check_endpoints(endpoint_ids: List[int]):
    """检查所有端点的可用性"""
    try:
        if endpoint_ids:
            db = SessionLocal()
            try:
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = []
                    for endpoint_id in endpoint_ids:
                        with db_lock:
                            endpoint = crud_endpoint.get_endpoint_by_id(db, endpoint_id)
                        if endpoint:
                            futures.append(
                                executor.submit(check_single_endpoint, endpoint, db)
                            )
                    for future in futures:
                        future.result()
            finally:
                db.close()
    except Exception as e:
        logger.error(f"Error in check_endpoints: {str(e)}")
        raise e


def check_all_endpoints():
    db = SessionLocal()
    try:
        with db_lock:
            endpoints = crud_endpoint.get_active_endpoints(db)
        if endpoints:
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(check_single_endpoint, endpoint, db)
                    for endpoint in endpoints
                ]
                for future in futures:
                    future.result()
    except Exception as e:
        logger.error(f"Error in check_all_endpoints: {str(e)}")
    finally:
        db.close()


def refresh_available_models(db: Session):
    """单独刷新所有可用端点的模型列表"""
    try:
        with db_lock:
            endpoints = crud_endpoint.get_available_endpoints(db)
        if endpoints:
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(refresh_endpoint_models, endpoint)
                    for endpoint in endpoints
                ]
                count = len(futures)
                index = 0
                for future in futures:
                    index += 1
                    logger.info(f"Refreshing models for endpoint {index}/{count}")
                    future.result()
    except Exception as e:
        logger.error(f"Error in refresh_available_models: {str(e)}")
        raise e


def refresh_endpoint_models(endpoint: Endpoint):
    db = SessionLocal()
    try:
        # 获取端点支持的模型列表
        model_names = get_endpoint_models(endpoint.url)
        logger.info(f"Found models {model_names} for endpoint {endpoint.url}")
        model_tasks = []

        with db_lock:
            for model_name in model_names:
                model = crud_model.get_or_create_model(db, model_name)
                crud_endpoint.associate_endpoint_with_model(db, endpoint.id, model.id)
                model_tasks.append((endpoint.id, model_name, model.id))

        # 并发执行所有模型的性能测试（最大 5 个线程）
        if model_tasks:
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(
                        test_and_update_model_performance_for_refresh, *args
                    )
                    for args in model_tasks
                ]
                for future in futures:
                    future.result()
    except Exception as e:
        logger.error(f"Error refreshing models for endpoint {endpoint.url}: {str(e)}")
    finally:
        db.close()


def test_and_update_model_performance_for_refresh(
    endpoint_id: int, model_name: str, model_id: int
):
    db = SessionLocal()
    try:
        performance = test_endpoint_performance(endpoint_id, model_name)
        with db_lock:
            if performance:
                test_data = PerformanceTestCreate(
                    endpoint_id=endpoint_id,
                    model_id=model_id,
                    tokens_per_second=performance["tokens_per_second"],
                    response_time=performance["response_time"],
                )
                crud_performance.create_performance_test(db, test_data)

                # 更新首选端点（如果尚未手动设置）
                model = crud_model.get_model_by_id(db, model_id)
                if model and not model.preferred_endpoint_id:
                    best_endpoint = crud_performance.get_best_endpoint_for_model(
                        db, model_id
                    )
                    if best_endpoint:
                        crud_model.update_preferred_endpoint(
                            db, model_id, best_endpoint.id
                        )
    except Exception as e:
        logger.error(
            f"Error testing performance for model {model_name} on endpoint {endpoint_id}: {str(e)}"
        )
    finally:
        db.close()


def refresh_model_performance(db: Session, model_id: int):
    """刷新单个模型在所有支持的端点上的性能测试"""
    try:
        # 获取模型信息
        with db_lock:
            model = crud_model.get_model_by_id(db, model_id)
            if not model:
                logger.error(f"找不到ID为 {model_id} 的模型")
                return

            # 查找支持该模型的所有端点
            supporting_endpoints = []
            for endpoint in model.endpoints:
                if endpoint.is_active and endpoint.is_available:
                    supporting_endpoints.append(endpoint)

        if not supporting_endpoints:
            logger.warning(f"模型 {model.name} 没有支持的可用端点")
            return

        logger.info(
            f"开始为模型 {model.name} 在 {len(supporting_endpoints)} 个端点上进行性能测试"
        )

        # 为每个端点创建性能测试任务
        test_tasks = []
        for endpoint in supporting_endpoints:
            test_tasks.append((endpoint.id, model.name, model.id))

        # 使用线程池并发执行所有端点的性能测试（最大5个线程）
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(test_and_update_model_performance, *args)
                for args in test_tasks
            ]
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"执行性能测试时发生错误: {str(e)}")

        # 更新首选端点（如果尚未手动设置）
        with db_lock:
            if not model.user_assigned_preference:
                best_endpoint = crud_performance.get_best_endpoint_for_model(
                    db, model.id
                )
                if best_endpoint:
                    crud_model.update_preferred_endpoint(db, model.id, best_endpoint.id)
                    logger.info(
                        f"已为模型 {model.name} 更新首选端点为 {best_endpoint.name}"
                    )

        logger.info(f"已完成模型 {model.name} 的性能测试刷新")

    except Exception as e:
        logger.error(f"刷新模型 {model_id} 性能测试时出错: {str(e)}")
