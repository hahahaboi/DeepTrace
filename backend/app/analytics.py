from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any

from .database import get_db
from . import models, schemas
from .flakiness import get_flaky_tests

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/clusters", response_model=List[Dict[str, Any]])
def get_failure_clusters(
    db: Session = Depends(get_db)
):
    """
    Fetch all failure clusters along with total failure count per cluster.
    """
    clusters = db.query(models.FailureCluster).all()
    results = []
    
    for c in clusters:
        failure_count = db.query(models.PipelineFailure).filter(
            models.PipelineFailure.cluster_id == c.id
        ).count()
        
        results.append({
            "id": c.id,
            "title": c.title,
            "summary": c.summary,
            "failure_count": failure_count,
            "created_at": c.created_at,
            "updated_at": c.updated_at
        })
        
    results.sort(key=lambda x: x["failure_count"], reverse=True)
    return results


@router.get("/clusters/{cluster_id}", response_model=Dict[str, Any])
def get_failure_cluster_detail(
    cluster_id: int,
    db: Session = Depends(get_db)
):
    """
    Fetch detailed information for a specific failure cluster and all associated failures.
    """
    cluster = db.query(models.FailureCluster).filter(models.FailureCluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failure cluster with ID {cluster_id} not found"
        )
        
    failures = db.query(models.PipelineFailure).filter(
        models.PipelineFailure.cluster_id == cluster_id
    ).all()
    
    failure_list = []
    for f in failures:
        run = db.query(models.WorkflowRun).filter(models.WorkflowRun.id == f.workflow_run_id).first()
        repo = db.query(models.Repository).filter(models.Repository.id == run.repository_id).first() if run else None
        
        failure_list.append({
            "id": f.id,
            "job_name": f.job_name,
            "step_name": f.step_name,
            "failure_reason": f.failure_reason,
            "log_summary": f.log_summary,
            "workflow_run_id": f.workflow_run_id,
            "run_number": run.run_number if run else None,
            "repository": repo.name if repo else None,
            "created_at": f.created_at
        })
        
    return {
        "id": cluster.id,
        "title": cluster.title,
        "summary": cluster.summary,
        "failure_count": len(failure_list),
        "failures": failure_list,
        "created_at": cluster.created_at,
        "updated_at": cluster.updated_at
    }


@router.get("/patterns", response_model=List[Dict[str, Any]])
def get_failure_patterns(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Fetch top recurring failure patterns grouped by job name, step name, and failure reason.
    """
    patterns = db.query(
        models.PipelineFailure.job_name,
        models.PipelineFailure.step_name,
        models.PipelineFailure.failure_reason,
        func.count(models.PipelineFailure.id).label("occurrence_count")
    ).group_by(
        models.PipelineFailure.job_name,
        models.PipelineFailure.step_name,
        models.PipelineFailure.failure_reason
    ).order_by(
        func.count(models.PipelineFailure.id).desc()
    ).limit(limit).all()
    
    results = []
    for p in patterns:
        job, step, reason, count = p
        results.append({
            "job_name": job,
            "step_name": step,
            "failure_reason": reason,
            "occurrence_count": count
        })
        
    return results


@router.get("/flaky-tests", response_model=List[Dict[str, Any]])
def get_flaky_test_analytics(
    repository_id: Optional[int] = Query(None),
    min_runs: int = Query(2, ge=1),
    threshold: float = Query(0.2, ge=0.0, le=1.0),
    db: Session = Depends(get_db)
):
    """
    Fetch top flaky tests across repositories calculated by historical pass/fail ratios.
    """
    flaky_tests = get_flaky_tests(
        db,
        repository_id=repository_id,
        min_runs=min_runs,
        threshold=threshold
    )
    return flaky_tests
