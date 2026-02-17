import pytest
import time
import asyncio
from src.services.model_registry import ModelRegistryService
from src.services.inference_engine import InferenceEngine

@pytest.mark.asyncio
async def test_single_prediction_under_100ms(db_session, redis_client):
    registry = ModelRegistryService(db_session)
    engine = InferenceEngine(db_session, redis_client)

    # Setup model
    model = await registry.register_model("PerfModel", "v1", "sklearn", "uri")

    start_time = time.perf_counter()
    await engine.predict(model.id, {"input": 1})
    end_time = time.perf_counter()

    duration = (end_time - start_time) * 1000 # ms
    print(f"Single prediction duration: {duration:.2f}ms")
    assert duration < 100, f"Prediction took {duration}ms, expected < 100ms"

@pytest.mark.asyncio
async def test_batch_1000_predictions(db_session, redis_client):
    registry = ModelRegistryService(db_session)
    engine = InferenceEngine(db_session, redis_client)

    model = await registry.register_model("PerfModelBatch", "v1", "sklearn", "uri")

    inputs = [{"input": i} for i in range(1000)]

    start_time = time.perf_counter()
    results = await engine.batch_predict(model.id, inputs)
    end_time = time.perf_counter()

    duration = (end_time - start_time) * 1000
    print(f"Batch 1000 prediction duration: {duration:.2f}ms")

    assert len(results) == 1000
    # Ideally, with asyncio.gather, it should be close to single prediction time + overhead.
    # 1000 tasks overhead might be significant but should be well under 1000 * 10ms = 10s.
    # Let's say under 2 seconds to be safe (allowing for massive overhead).
    assert duration < 2000, f"Batch prediction took {duration}ms"

@pytest.mark.asyncio
async def test_concurrent_100_requests(db_session, redis_client):
    registry = ModelRegistryService(db_session)
    engine = InferenceEngine(db_session, redis_client)

    model = await registry.register_model("PerfModelConcurrent", "v1", "sklearn", "uri")

    # Pre-fetch (or use existing) model to avoid concurrent session usage in tasks
    # model is already attached to session from register_model, but let's be explicit
    # passing model=model avoids DB lookup in predict

    async def make_request():
        return await engine.predict(model.id, {"input": 1}, model=model)

    tasks = [make_request() for _ in range(100)]

    start_time = time.perf_counter()
    results = await asyncio.gather(*tasks)
    end_time = time.perf_counter()

    duration = (end_time - start_time) * 1000
    print(f"Concurrent 100 requests duration: {duration:.2f}ms")

    assert len(results) == 100
    # Similar logic, should be fast.
    assert duration < 1000, f"Concurrent requests took {duration}ms"
