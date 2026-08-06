from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# GitHub webhook payload schemas
class GitHubUser(BaseModel):
    login: str

class GitHubRepository(BaseModel):
    id: int
    name: str
    owner: GitHubUser

class GitHubWorkflowRun(BaseModel):
    id: int
    run_number: int
    event: str
    status: str
    conclusion: Optional[str] = None
    html_url: str
    created_at: datetime
    updated_at: datetime

class GitHubWorkflowRunPayload(BaseModel):
    action: str
    workflow_run: GitHubWorkflowRun
    repository: GitHubRepository

# API Response schemas
class RepositoryBase(BaseModel):
    github_id: int
    name: str
    owner: str

class RepositoryResponse(RepositoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class WorkflowRunBase(BaseModel):
    github_id: int
    run_number: int
    event: str
    status: str
    conclusion: Optional[str] = None
    html_url: str

class WorkflowRunResponse(WorkflowRunBase):
    id: int
    repository_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Failure Cluster schemas
class FailureClusterBase(BaseModel):
    title: str
    summary: Optional[str] = None

class FailureClusterResponse(FailureClusterBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Pipeline Failure response schema
class PipelineFailureBase(BaseModel):
    job_name: str
    step_name: Optional[str] = None
    failure_reason: Optional[str] = None
    log_summary: Optional[str] = None

class PipelineFailureResponse(PipelineFailureBase):
    id: int
    workflow_run_id: int
    cluster_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
