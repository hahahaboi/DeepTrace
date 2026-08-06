import pytest
from app.flakiness import calculate_flakiness_score, get_flaky_tests
from app.models import Repository, WorkflowRun, TestHistory

def test_calculate_flakiness_score():
    # 0 runs or zero in pass/fail
    assert calculate_flakiness_score(0, 0) == 0.0
    assert calculate_flakiness_score(10, 0) == 0.0 # 100% pass rate -> not flaky
    assert calculate_flakiness_score(0, 10) == 0.0 # 100% fail rate -> consistent failure, not flaky

    # 50-50 split -> maximum flakiness score (1.0)
    assert calculate_flakiness_score(5, 5) == 1.0
    assert calculate_flakiness_score(10, 10) == 1.0

    # Intermittent passes/fails
    # 8 pass, 2 fail -> 2 * min(8, 2) / 10 = 4 / 10 = 0.4
    assert calculate_flakiness_score(8, 2) == 0.4
    # 9 pass, 1 fail -> 2 * 1 / 10 = 0.2
    assert calculate_flakiness_score(9, 1) == 0.2

def test_get_flaky_tests_database(db):
    repo = Repository(github_id=500, name="demo-repo", owner="demo-owner")
    db.add(repo)
    db.commit()

    run = WorkflowRun(github_id=600, repository_id=repo.id, run_number=1, event="push", status="completed", conclusion="failure")
    db.add(run)
    db.commit()

    # Insert test histories:
    # Test A: 5 passes, 5 fails -> flaky_score = 1.0
    for _ in range(5):
        db.add(TestHistory(repository_id=repo.id, workflow_run_id=run.id, test_suite="unit", test_name="TestA", status="passed"))
        db.add(TestHistory(repository_id=repo.id, workflow_run_id=run.id, test_suite="unit", test_name="TestA", status="failed"))

    # Test B: 10 passes, 0 fails -> flaky_score = 0.0
    for _ in range(10):
        db.add(TestHistory(repository_id=repo.id, workflow_run_id=run.id, test_suite="unit", test_name="TestB", status="passed"))

    # Test C: 1 pass, 0 fail -> total_runs < min_runs (min_runs=2)
    db.add(TestHistory(repository_id=repo.id, workflow_run_id=run.id, test_suite="unit", test_name="TestC", status="passed"))

    db.commit()

    flaky = get_flaky_tests(db, repository_id=repo.id, min_runs=2, threshold=0.2)
    assert len(flaky) == 2 # TestA and TestB (TestC filtered out by min_runs)
    
    top_flaky = flaky[0]
    assert top_flaky["test_name"] == "TestA"
    assert top_flaky["flakiness_score"] == 1.0
    assert top_flaky["is_flaky"] is True
    assert top_flaky["total_runs"] == 10

    stable_test = flaky[1]
    assert stable_test["test_name"] == "TestB"
    assert stable_test["flakiness_score"] == 0.0
    assert stable_test["is_flaky"] is False
