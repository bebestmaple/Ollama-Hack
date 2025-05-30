import asyncio
from typing import List, Optional

from pydantic import BaseModel

from src.ai_model.models import AIModelDB, AIModelPerformanceDB, AIModelStatusEnum
from src.endpoint.models import EndpointDB, EndpointPerformanceDB, EndpointStatusEnum
from src.endpoint.utils import get_token_count
from src.logging import get_logger
from src.ollama.client import OllamaClient

logger = get_logger(__name__)


class ModelPerformance(BaseModel):
    ai_model: AIModelDB
    performance: AIModelPerformanceDB


class EndpointTestResult(BaseModel):
    endpoint_performance: Optional[EndpointPerformanceDB] = None
    model_performances: List[ModelPerformance] = []


async def get_ai_models(
    ollama_client: OllamaClient,
) -> List[AIModelDB]:
    """
    Get the list of models from the endpoint.
    """
    result = []
    try:
        models_raw = await ollama_client.tags()
        for model_raw in models_raw.models:
            name, tag = model_raw.model.split(":", 1)
            model = AIModelDB(
                name=name,
                tag=tag,
            )
            result.append(model)
            logger.debug(f"Model: {model.name}, Tag: {model.tag}, Size: {model_raw.size}")
        return result
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        return result


async def test_ai_model(
    ollama_client: OllamaClient,
    ai_model: AIModelDB,
    prompt: str = "将以下内容，翻译成现代汉语：先帝创业未半而中道崩殂，今天下三分，益州疲弊，此诚危急存亡之秋也。",
    timeout: int = 60,
) -> AIModelPerformanceDB:
    """
    Test the performance of the AI model by making a request to the /generate endpoint.

    Return False when the endpoint is fake.
    """
    try:
        output = ""
        output_tokens = 0
        connection_time = 0
        total_time = 0
        token_per_second = 0
        response = None
        try:
            async with asyncio.timeout(timeout):
                start_time = asyncio.get_event_loop().time()
                async for response in await ollama_client.generate(
                    model=f"{ai_model.name}:{ai_model.tag}",
                    prompt=prompt,
                    stream=True,
                ):
                    if not connection_time:
                        connection_time = asyncio.get_event_loop().time() - start_time
                        logger.debug(
                            f"Connection time: {connection_time}, "
                            f"Model: {ai_model.name}:{ai_model.tag}"
                        )
                    output += response.response
                    if "fake-ollama" in output or "服务器繁忙" in output:
                        logger.error(f"Fake endpoint detected: {ai_model.name}:{ai_model.tag}")
                        return AIModelPerformanceDB(
                            status=AIModelStatusEnum.FAKE,
                        )
                    if response.done:
                        break
        except asyncio.TimeoutError:
            logger.debug(f"Timeout error: {timeout} seconds")
        except Exception as e:
            logger.debug(f"Error testing model {ai_model.name}:{ai_model.tag}: {e}")

        if not response:
            logger.debug(f"No response from model {ai_model.name}:{ai_model.tag}")
            raise Exception("No response from model")

        logger.debug(f"Response: {output}, " f"Model: {ai_model.name}:{ai_model.tag}")
        end_time = asyncio.get_event_loop().time()
        if response.done and response.eval_count:
            output_tokens = response.eval_count
        else:
            output_tokens = get_token_count(output)

        total_time = end_time - start_time
        token_per_second = output_tokens / total_time
        # token_per_second = output_tokens / (total_time - connection_time)
        performance = AIModelPerformanceDB(
            status=AIModelStatusEnum.AVAILABLE,
            token_per_second=token_per_second,
            connection_time=connection_time,
            total_time=total_time,
            output=output,
            output_tokens=output_tokens,
        )
        return performance
    except Exception as e:
        logger.debug(f"Error testing model {ai_model.name}:{ai_model.tag}: {e}")
        return AIModelPerformanceDB(
            status=AIModelStatusEnum.UNAVAILABLE,
        )


async def test_endpoint(
    endpoint: EndpointDB,
) -> EndpointTestResult:
    """
    Test the endpoint by checking its availability and testing each AI model.
    """
    test_reuslt = EndpointTestResult()
    async with OllamaClient(endpoint.url).connect() as ollama_client:
        try:
            version = await ollama_client.version()
            test_reuslt.endpoint_performance = EndpointPerformanceDB(
                status=EndpointStatusEnum.AVAILABLE,
                ollama_version=version.version,
            )
            logger.info(f"Endpoint version: {version.version}")
        except Exception as e:
            logger.debug(f"Error checking endpoint {endpoint.name}: {e}")
            test_reuslt.endpoint_performance = EndpointPerformanceDB(
                status=EndpointStatusEnum.UNAVAILABLE,
            )
            return test_reuslt

        ai_models = await get_ai_models(ollama_client)

        for ai_model in ai_models:
            if test_reuslt.endpoint_performance.status == EndpointStatusEnum.FAKE:
                model_performance = ModelPerformance(
                    ai_model=ai_model,
                    performance=AIModelPerformanceDB(
                        status=AIModelStatusEnum.FAKE,
                    ),
                )
                test_reuslt.model_performances.append(model_performance)
                logger.debug(
                    f"Fake endpoint {endpoint.name}, skipping model {ai_model.name}:{ai_model.tag}"
                )
                continue

            performance = await test_ai_model(ollama_client, ai_model)
            match performance.status:
                case AIModelStatusEnum.AVAILABLE:
                    logger.info(
                        f"Performance: {performance.token_per_second:.2f} tps "
                        f"({performance.output_tokens} tokens in {performance.total_time:.2f} s), "
                        f"Model: {ai_model.name}:{ai_model.tag} @ "
                        f"{endpoint.name},"
                    )
                case AIModelStatusEnum.UNAVAILABLE:
                    logger.debug(f"Model {ai_model.name}:{ai_model.tag} is not available, skipping")
                case AIModelStatusEnum.FAKE:
                    logger.debug(f"Fake endpoint detected: {endpoint.name}")
                    # set endpoint status to fake
                    test_reuslt.endpoint_performance = EndpointPerformanceDB(
                        status=EndpointStatusEnum.FAKE,
                    )
                case _:
                    logger.debug(f"Model {ai_model.name}:{ai_model.tag} is not available, skipping")

            model_performance = ModelPerformance(ai_model=ai_model, performance=performance)
            test_reuslt.model_performances.append(model_performance)

        return test_reuslt


if __name__ == "__main__":
    import os

    async def main():
        endpoint = EndpointDB(
            url=os.getenv("ENDPOINT", "http://localhost:11434"),
            name=os.getenv("ENDPOINT_NAME", "ollama"),
        )

        test_result = await test_endpoint(endpoint)
        logger.info(f"Test result: {test_result.model_dump_json(indent=2)}")

    asyncio.run(main())
