import hmac
import hashlib
import json
import pytest
from app.config import settings
from app.models import Repository, WorkflowRun

# Helper to generate signature
def generate_signature(payload_bytes: bytes, secret: str) -> str:
    mac = hmac.new(secret.encode('utf-8'), payload_bytes, hashlib.sha256)
    return f"sha256={mac.hexdigest()}"

def test_webhook_root_health(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_webhook_missing_signature(client):
    payload = {"action": "completed"}
    response = client.post(
        "/webhooks/github",
        json=payload,
        headers={"X-GitHub-Event": "workflow_run"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid signature"

def test_webhook_invalid_signature(client):
    payload = {"action": "completed"}
    response = client.post(
        "/webhooks/github",
        json=payload,
        headers={
            "X-GitHub-Event": "workflow_run",
            "X-Hub-Signature-256": "sha256=invalid_signature_value"
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid signature"

def test_webhook_unhandled_event(client):
    payload = {"action": "completed"}
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    sig = generate_signature(payload_bytes, settings.GITHUB_WEBHOOK_SECRET)
    
    response = client.post(
        "/webhooks/github",
        content=payload_bytes,
        headers={
            "X-GitHub-Event": "push",
            "X-Hub-Signature-256": sig,
            "Content-Type": "application/json"
        }
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    assert "Unhandled event type" in response.json()["reason"]

def test_webhook_workflow_run_ignored_not_completed(client):
    payload = {
        "action": "requested",
        "workflow_run": {
            "id": 12345,
            "run_number": 1,
            "event": "push",
            "status": "queued",
            "conclusion": None,
            "html_url": "https://github.com/owner/repo/actions/runs/12345",
            "created_at": "2026-07-29T17:11:55Z",
            "updated_at": "2026-07-29T17:11:55Z"
        },
        "repository": {
            "id": 98765,
            "name": "deeptrace",
            "owner": {
                "login": "owner_username"
            }
        }
    }
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    sig = generate_signature(payload_bytes, settings.GITHUB_WEBHOOK_SECRET)
    
    response = client.post(
        "/webhooks/github",
        content=payload_bytes,
        headers={
            "X-GitHub-Event": "workflow_run",
            "X-Hub-Signature-256": sig,
            "Content-Type": "application/json"
        }
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    assert "not completed" in response.json()["reason"]

def test_webhook_workflow_run_ignored_success(client):
    payload = {
        "action": "completed",
        "workflow_run": {
            "id": 12345,
            "run_number": 1,
            "event": "push",
            "status": "completed",
            "conclusion": "success",
            "html_url": "https://github.com/owner/repo/actions/runs/12345",
            "created_at": "2026-07-29T17:11:55Z",
            "updated_at": "2026-07-29T17:11:55Z"
        },
        "repository": {
            "id": 98765,
            "name": "deeptrace",
            "owner": {
                "login": "owner_username"
            }
        }
    }
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    sig = generate_signature(payload_bytes, settings.GITHUB_WEBHOOK_SECRET)
    
    response = client.post(
        "/webhooks/github",
        content=payload_bytes,
        headers={
            "X-GitHub-Event": "workflow_run",
            "X-Hub-Signature-256": sig,
            "Content-Type": "application/json"
        }
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    assert "not failure" in response.json()["reason"]

def test_webhook_workflow_run_failure_ingested(client, db):
    payload = {
        "action": "completed",
        "workflow_run": {
            "id": 12345,
            "run_number": 1,
            "event": "push",
            "status": "completed",
            "conclusion": "failure",
            "html_url": "https://github.com/owner/repo/actions/runs/12345",
            "created_at": "2026-07-29T17:11:55Z",
            "updated_at": "2026-07-29T17:11:55Z"
        },
        "repository": {
            "id": 98765,
            "name": "deeptrace",
            "owner": {
                "login": "owner_username"
            }
        }
    }
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    sig = generate_signature(payload_bytes, settings.GITHUB_WEBHOOK_SECRET)
    
    response = client.post(
        "/webhooks/github",
        content=payload_bytes,
        headers={
            "X-GitHub-Event": "workflow_run",
            "X-Hub-Signature-256": sig,
            "Content-Type": "application/json"
        }
    )
    assert response.status_code == 200
    assert response.json()["status"] == "processed"
    assert response.json()["workflow_run_id"] == 12345
    
    # Verify DB records
    repo = db.query(Repository).filter(Repository.github_id == 98765).first()
    assert repo is not None
    assert repo.name == "deeptrace"
    assert repo.owner == "owner_username"
    
    run = db.query(WorkflowRun).filter(WorkflowRun.github_id == 12345).first()
    assert run is not None
    assert run.run_number == 1
    assert run.conclusion == "failure"
    assert run.repository_id == repo.id
