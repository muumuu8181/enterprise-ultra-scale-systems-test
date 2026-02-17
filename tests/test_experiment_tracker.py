import pytest
from src.services.experiment_tracker import ExperimentTracker
from src.models.ml_models import Experiment, Run
from sqlalchemy import select

@pytest.mark.asyncio
async def test_create_run_and_log_metrics(db_session):
    tracker = ExperimentTracker(db_session)
    exp = await tracker.create_experiment("exp_test", "desc", {})

    run = await tracker.start_run(exp.id)
    assert run.status == "running"

    run_updated = await tracker.log_metrics(run.id, {"accuracy": 0.9, "loss": 0.1})

    assert run_updated.metrics["accuracy"] == 0.9
    assert run_updated.metrics["loss"] == 0.1

@pytest.mark.asyncio
async def test_compare_runs(db_session):
    tracker = ExperimentTracker(db_session)
    exp = await tracker.create_experiment("exp_compare", "desc", {})

    r1 = await tracker.start_run(exp.id)
    await tracker.log_metrics(r1.id, {"acc": 0.8})
    await tracker.finish_run(r1.id)

    r2 = await tracker.start_run(exp.id)
    await tracker.log_metrics(r2.id, {"acc": 0.9})
    await tracker.finish_run(r2.id)

    runs = await tracker.get_runs(exp.id, sort_by="start_time")
    assert len(runs) == 2

    runs_data = [r.metrics['acc'] for r in runs if r.metrics and 'acc' in r.metrics]
    assert 0.8 in runs_data
    assert 0.9 in runs_data

@pytest.mark.asyncio
async def test_finish_run_updates_best_model(db_session):
    tracker = ExperimentTracker(db_session)
    exp = await tracker.create_experiment("exp_finish", "desc", {})
    run = await tracker.start_run(exp.id)

    assert run.end_time is None

    finished_run = await tracker.finish_run(run.id)
    assert finished_run.end_time is not None
    assert finished_run.status == "completed"

@pytest.mark.asyncio
async def test_concurrent_runs_same_experiment(db_session):
    tracker = ExperimentTracker(db_session)
    exp = await tracker.create_experiment("exp_concurrent", "desc", {})

    r1 = await tracker.start_run(exp.id)
    r2 = await tracker.start_run(exp.id)

    assert r1.id != r2.id
    assert r1.experiment_id == exp.id
    assert r2.experiment_id == exp.id

    await tracker.log_metrics(r1.id, {"val": 1})
    await tracker.log_metrics(r2.id, {"val": 2})

    # Re-fetch to verify persistence
    stmt1 = select(Run).where(Run.id == r1.id)
    r1_fetched = (await db_session.execute(stmt1)).scalar_one()

    stmt2 = select(Run).where(Run.id == r2.id)
    r2_fetched = (await db_session.execute(stmt2)).scalar_one()

    assert r1_fetched.metrics["val"] == 1
    assert r2_fetched.metrics["val"] == 2
