import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from app.clustering import cluster_failures, generate_cluster_metadata, process_and_cluster_failures, EmbeddingClient
from app.models import PipelineFailure, FailureCluster, Repository, WorkflowRun

# Deterministic mock embedder to test clustering without network or model loading
def mock_embed_function(self, texts):
    results = []
    # Seed numpy for deterministic random noise
    np.random.seed(42)
    for text in texts:
        if "python" in text.lower():
            # Cluster A: Centered around +1.0
            vector = np.ones(384) * 1.0 + np.random.normal(0, 0.05, 384)
            results.append(vector.tolist())
        elif "node" in text.lower():
            # Cluster B: Centered around -1.0
            vector = np.ones(384) * -1.0 + np.random.normal(0, 0.05, 384)
            results.append(vector.tolist())
        else:
            # Noise points: Random far-away vectors
            vector = np.random.normal(0, 10.0, 384)
            results.append(vector.tolist())
    return results

@pytest.fixture(autouse=True)
def mock_embedding():
    with patch.object(EmbeddingClient, 'embed', new=mock_embed_function):
        yield

def test_cluster_failures_simple():
    # Construct 4 points: 2 close to 1.0, 2 close to -1.0
    embeddings = [
        [1.0] * 384,
        [1.05] * 384,
        [-1.0] * 384,
        [-1.05] * 384
    ]
    labels = cluster_failures(embeddings, min_cluster_size=2)
    assert len(labels) == 4
    # The first two should share a label, the second two should share a different label
    assert labels[0] == labels[1]
    assert labels[2] == labels[3]
    assert labels[0] != labels[2]
    # Check they are not -1 (noise)
    assert labels[0] != -1
    assert labels[2] != -1

def test_cluster_failures_noise():
    # If we only have 1 item, it should return noise label -1
    embeddings = [[1.0] * 384]
    labels = cluster_failures(embeddings, min_cluster_size=2)
    assert labels == [-1]

def test_generate_cluster_metadata():
    failures = [
        PipelineFailure(job_name="build", step_name="test", failure_reason="AssertionError"),
        PipelineFailure(job_name="build", step_name="test", failure_reason="Timeout"),
        PipelineFailure(job_name="deploy", step_name="test", failure_reason="AssertionError")
    ]
    title, summary = generate_cluster_metadata(failures)
    assert "build" in title
    assert "test" in title
    assert "3 failures" in summary
    assert "AssertionError" in summary
    assert "Timeout" in summary

def test_process_and_cluster_failures_pipeline(db):
    # Set up basic repo and run objects
    repo = Repository(github_id=1, name="test-repo", owner="test-owner")
    db.add(repo)
    db.commit()
    db.refresh(repo)
    
    run = WorkflowRun(github_id=101, repository_id=repo.id, run_number=1, event="push", status="completed", conclusion="failure")
    db.add(run)
    db.commit()
    db.refresh(run)

    # Insert unclustered failures:
    # 2 Python failures (should cluster together)
    # 2 Node failures (should cluster together)
    # 1 general failure (noise)
    failures = [
        PipelineFailure(workflow_run_id=run.id, job_name="test-python", step_name="lint", failure_reason="Python SyntaxError", log_summary="python line 1 error"),
        PipelineFailure(workflow_run_id=run.id, job_name="test-python", step_name="test", failure_reason="Python AssertionError", log_summary="python assert failed"),
        PipelineFailure(workflow_run_id=run.id, job_name="test-node", step_name="build", failure_reason="Node package missing", log_summary="node module error"),
        PipelineFailure(workflow_run_id=run.id, job_name="test-node", step_name="test", failure_reason="Node TypeError", log_summary="node stack trace"),
        PipelineFailure(workflow_run_id=run.id, job_name="test-go", step_name="compile", failure_reason="Go compiler panic", log_summary="go panic traceback")
    ]
    for f in failures:
        db.add(f)
    db.commit()

    # Run clustering pipeline
    new_clusters = process_and_cluster_failures(db, min_cluster_size=2)
    assert new_clusters == 2 # 1 Python cluster, 1 Node cluster
    
    # Reload failures from DB
    db_failures = db.query(PipelineFailure).order_by(PipelineFailure.id).all()
    
    # Verify embeddings are generated
    for f in db_failures:
        assert f.log_embedding is not None
        assert len(f.log_embedding) == 384

    # Python failures (ids 1 and 2, index 0 and 1) should have the same cluster ID
    assert db_failures[0].cluster_id is not None
    assert db_failures[0].cluster_id == db_failures[1].cluster_id
    
    # Node failures (ids 3 and 4, index 2 and 3) should have the same cluster ID
    assert db_failures[2].cluster_id is not None
    assert db_failures[2].cluster_id == db_failures[3].cluster_id
    
    # Python and Node cluster IDs should be different
    assert db_failures[0].cluster_id != db_failures[2].cluster_id
    
    # Go failure (noise) should have cluster_id as None
    assert db_failures[4].cluster_id is None
    
    # Verify cluster records
    python_cluster = db.query(FailureCluster).filter(FailureCluster.id == db_failures[0].cluster_id).first()
    assert python_cluster is not None
    assert "test-python" in python_cluster.title
    assert "SyntaxError" in python_cluster.summary or "AssertionError" in python_cluster.summary
    assert python_cluster.representative_embedding is not None
    assert len(python_cluster.representative_embedding) == 384
