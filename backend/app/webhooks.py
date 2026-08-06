import hmac
import hashlib
import logging
from typing import Optional
from fastapi import APIRouter, Request, Header, HTTPException, Depends, status
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db
from . import models, schemas
from .parser import parse_error_log
from .clustering import process_and_cluster_failures

# Configure logger
logger = logging.getLogger("deeptrace.webhooks")
logging.basicConfig(level=logging.INFO)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

def verify_signature(payload_body: bytes, signature_header: Optional[str], secret: str) -> bool:
    if not signature_header:
        logger.warning("Missing signature header")
        return False
    
    parts = signature_header.split('=', 1)
    if len(parts) != 2 or parts[0] != 'sha256':
        logger.warning(f"Invalid signature header format: {signature_header}")
        return False
    
    signature = parts[1]
    mac = hmac.new(secret.encode('utf-8'), msg=payload_body, digestmod=hashlib.sha256)
    return hmac.compare_digest(mac.hexdigest(), signature)

@router.post("/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    body = await request.body()
    
    # Verify GitHub HMAC signature
    if not verify_signature(body, x_hub_signature_256, settings.GITHUB_WEBHOOK_SECRET):
        logger.error("Signature verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )
    
    # Read and log event type
    event_type = request.headers.get("X-GitHub-Event")
    logger.info(f"Received GitHub webhook event: {event_type}")
    
    if event_type != "workflow_run":
        return {"status": "ignored", "reason": f"Unhandled event type: {event_type}"}
        
    try:
        payload = await request.json()
        payload_data = schemas.GitHubWorkflowRunPayload(**payload)
    except Exception as e:
        logger.error(f"Error parsing payload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid payload structure: {str(e)}"
        )
        
    # Check if action is completed
    if payload_data.action != "completed":
        logger.info(f"Workflow run action is {payload_data.action}, not completed. Ignored.")
        return {"status": "ignored", "reason": f"Action is {payload_data.action}, not completed"}
        
    run = payload_data.workflow_run
    repo = payload_data.repository
    
    # Filter for failures
    if run.conclusion != "failure":
        logger.info(f"Workflow run conclusion is {run.conclusion}, not failure. Ignored.")
        return {"status": "ignored", "reason": f"Workflow run conclusion is {run.conclusion}, not failure"}
        
    logger.info(f"Processing failure for repository {repo.owner.login}/{repo.name}, run {run.run_number}")

    # Find or create repository
    db_repo = db.query(models.Repository).filter(models.Repository.github_id == repo.id).first()
    if not db_repo:
        db_repo = models.Repository(
            github_id=repo.id,
            name=repo.name,
            owner=repo.owner.login
        )
        db.add(db_repo)
        db.commit()
        db.refresh(db_repo)
    else:
        db_repo.name = repo.name
        db_repo.owner = repo.owner.login
        db.commit()
        db.refresh(db_repo)
        
    # Find or create workflow run
    db_run = db.query(models.WorkflowRun).filter(models.WorkflowRun.github_id == run.id).first()
    if not db_run:
        db_run = models.WorkflowRun(
            github_id=run.id,
            repository_id=db_repo.id,
            run_number=run.run_number,
            event=run.event,
            status=run.status,
            conclusion=run.conclusion,
            html_url=run.html_url,
            created_at=run.created_at,
            updated_at=run.updated_at
        )
        db.add(db_run)
    else:
        db_run.status = run.status
        db_run.conclusion = run.conclusion
        db_run.html_url = run.html_url
        db_run.updated_at = run.updated_at
        
    db.commit()
    db.refresh(db_run)
    
    # Automatic failure parsing and extraction
    raw_logs = payload.get("raw_logs", "") or payload.get("log", "")
    parsed_summary = parse_error_log(raw_logs) if raw_logs else None
    
    existing_failure = db.query(models.PipelineFailure).filter(
        models.PipelineFailure.workflow_run_id == db_run.id
    ).first()
    
    if not existing_failure:
        failure_entry = models.PipelineFailure(
            workflow_run_id=db_run.id,
            job_name=payload.get("failed_job_name", "workflow_run_failure"),
            step_name=payload.get("failed_step_name", None),
            failure_reason=payload.get("failure_reason", f"Workflow run {run.run_number} failed"),
            log_summary=parsed_summary or f"Workflow run {run.run_number} failed with status {run.conclusion}"
        )
        db.add(failure_entry)
        db.commit()
        
    # Automatic trigger of vector embedding generation and cluster assignment
    new_clusters = process_and_cluster_failures(db, min_cluster_size=2)
    logger.info(f"Automated ingestion & clustering complete. New clusters created: {new_clusters}")
    
    return {
        "status": "processed",
        "repository": db_repo.name,
        "workflow_run_id": db_run.github_id,
        "conclusion": db_run.conclusion,
        "new_clusters_created": new_clusters
    }
