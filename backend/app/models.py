import json
from sqlalchemy import Column, Integer, BigInteger, String, Text, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator
from pgvector.sqlalchemy import Vector
from .database import Base

class VectorType(TypeDecorator):
    """
    Dialect-aware Vector type:
    - On PostgreSQL: Uses native pgvector type.
    - On SQLite/Other DBs: Fallbacks to Text storing JSON strings for testing compatibility.
    """
    impl = Text
    cache_ok = True

    def __init__(self, dim=None):
        super().__init__()
        self.dim = dim
        self.vector_impl = Vector(dim)

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(self.vector_impl)
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'postgresql':
            return value
        if isinstance(value, (list, tuple)):
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == 'postgresql':
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return value
        return value


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    github_id = Column(BigInteger, unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    owner = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    workflow_runs = relationship("WorkflowRun", back_populates="repository", cascade="all, delete-orphan")
    test_histories = relationship("TestHistory", back_populates="repository", cascade="all, delete-orphan")


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id = Column(Integer, primary_key=True, index=True)
    github_id = Column(BigInteger, unique=True, index=True, nullable=False)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    run_number = Column(Integer, nullable=False)
    event = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)
    conclusion = Column(String(50), nullable=True)
    html_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    repository = relationship("Repository", back_populates="workflow_runs")
    failures = relationship("PipelineFailure", back_populates="workflow_run", cascade="all, delete-orphan")
    test_histories = relationship("TestHistory", back_populates="workflow_run", cascade="all, delete-orphan")


class FailureCluster(Base):
    __tablename__ = "failure_clusters"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)
    representative_embedding = Column(VectorType(384), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    failures = relationship("PipelineFailure", back_populates="cluster")


class PipelineFailure(Base):
    __tablename__ = "pipeline_failures"

    id = Column(Integer, primary_key=True, index=True)
    workflow_run_id = Column(Integer, ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(BigInteger, nullable=True)
    job_name = Column(String(255), nullable=False)
    step_name = Column(String(255), nullable=True)
    failure_reason = Column(Text, nullable=True)
    log_summary = Column(Text, nullable=True)
    log_embedding = Column(VectorType(384), nullable=True)
    cluster_id = Column(Integer, ForeignKey("failure_clusters.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    workflow_run = relationship("WorkflowRun", back_populates="failures")
    cluster = relationship("FailureCluster", back_populates="failures")


class TestHistory(Base):
    __tablename__ = "test_history"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    workflow_run_id = Column(Integer, ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False)
    test_suite = Column(String(255), nullable=True)
    test_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    duration = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    failure_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    repository = relationship("Repository", back_populates="test_histories")
    workflow_run = relationship("WorkflowRun", back_populates="test_histories")
