import pytest
from unittest.mock import patch
import numpy as np

from app.models import Repository, WorkflowRun, PipelineFailure, FailureCluster, TestHistory
from app.clustering import EmbeddingClient

# Mock embedding for test suite
def mock_embed_function(self, texts):
    results = []
    np.random.seed(42)
    for text in texts:
        if "python" in text.lower():
            v = np.ones(384) * 1.0 + np.random.normal(0, 0.01, 384)
            results.append(v.tolist())
        else:
            v = np.ones(384) * -1.0 + np.random.normal(0, 0.01, 384)
            results.append(v.tolist())
    return results

@pytest.fixture(autouse=True)
def mock_embedding():
    with patch.object(EmbeddingClient, 'embed', new=mock_embed_function):
        yield

def test_analytics_clusters_empty(client):
    response = client.get("/analytics/clusters")
    assert response.status_code == 200
    assert response.json() == []

def test_analytics_clusters_with_data(client, db):
    cluster = FailureCluster(title="Python Syntax Error", summary="Group of syntax errors")
    db.add(cluster)
    db.commit()
    db.refresh(cluster)

    run = WorkflowRun(github_id=200, repository_id=1, run_number=1, event="push", status="completed", conclusion="failure")
    db.add(run)
    db.commit()

    f1 = PipelineFailure(workflow_run_id=run.id, job_name="test", failure_reason="SyntaxError", cluster_id=cluster.id)
    f2 = PipelineFailure(workflow_run_id=run.id, job_name="test", failure_reason="SyntaxError", cluster_id=cluster.id)
    db.add(f1)
    db.add(f2)
    db.commit()

    response = client.get("/analytics/clusters")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == cluster.id
    assert data[0]["title"] == "Python Syntax Error"
    assert data[0]["failure_count"] == 2

def test_analytics_cluster_detail(client, db):
    cluster = FailureCluster(title="Node Module Error", summary="Missing packages")
    db.add(cluster)
    db.commit()
    db.refresh(cluster)

    repo = Repository(github_id=300, name="analytics-demo", owner="demo-owner")
    db.add(repo)
    db.commit()

    run = WorkflowRun(github_id=400, repository_id=repo.id, run_number=5, event="push", status="completed", conclusion="failure")
    db.add(run)
    db.commit()

    failure = PipelineFailure(workflow_run_id=run.id, job_name="build-node", step_name="npm test", failure_reason="Module not found", log_summary="Error: Cannot find module 'express'", cluster_id=cluster.id)
    db.add(failure)
    db.commit()

    # Get details
    response = client.get(f"/analytics/clusters/{cluster.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == cluster.id
    assert data["title"] == "Node Module Error"
    assert data["failure_count"] == 1
    assert len(data["failures"]) == 1
    assert data["failures"][0]["job_name"] == "build-node"
    assert data["failures"][0]["repository"] == "analytics-demo"

def test_analytics_cluster_detail_not_found(client):
    response = client.get("/analytics/clusters/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Failure cluster with ID 99999 not found"

def test_analytics_patterns(client, db):
    run = WorkflowRun(github_id=500, repository_id=1, run_number=1, event="push", status="completed", conclusion="failure")
    db.add(run)
    db.commit()

    # 3 occurrences of Pattern A, 1 occurrence of Pattern B
    for _ in range(3):
        db.add(PipelineFailure(workflow_run_id=run.id, job_name="test", step_name="pytest", failure_reason="TimeoutError"))
    db.add(PipelineFailure(workflow_run_id=run.id, job_name="lint", step_name="flake8", failure_reason="FormattingError"))
    db.commit()

    response = client.get("/analytics/patterns?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["job_name"] == "test"
    assert data[0]["step_name"] == "pytest"
    assert data[0]["failure_reason"] == "TimeoutError"
    assert data[0]["occurrence_count"] == 3

def test_analytics_flaky_tests_api(client, db):
    repo = Repository(github_id=700, name="flaky-repo", owner="demo")
    db.add(repo)
    db.commit()

    run = WorkflowRun(github_id=800, repository_id=repo.id, run_number=1, event="push", status="completed", conclusion="failure")
    db.add(run)
    db.commit()

    db.add(TestHistory(repository_id=repo.id, workflow_run_id=run.id, test_suite="unit", test_name="FlakyTest", status="passed"))
    db.add(TestHistory(repository_id=repo.id, workflow_run_id=run.id, test_suite="unit", test_name="FlakyTest", status="failed"))
    db.commit()

    response = client.get(f"/analytics/flaky-tests?repository_id={repo.id}&min_runs=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["test_name"] == "FlakyTest"
    assert data[0]["flakiness_score"] == 1.0
