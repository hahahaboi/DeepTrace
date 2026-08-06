-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create Repositories Table
CREATE TABLE IF NOT EXISTS repositories (
    id SERIAL PRIMARY KEY,
    github_id BIGINT UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    owner VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create Index on github_id for fast lookup
CREATE INDEX IF NOT EXISTS idx_repositories_github_id ON repositories(github_id);

-- Create Workflow Runs Table
CREATE TABLE IF NOT EXISTS workflow_runs (
    id SERIAL PRIMARY KEY,
    github_id BIGINT UNIQUE NOT NULL,
    repository_id INTEGER REFERENCES repositories(id) ON DELETE CASCADE,
    run_number INTEGER NOT NULL,
    event VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    conclusion VARCHAR(50),
    html_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create Index on github_id for fast lookup
CREATE INDEX IF NOT EXISTS idx_workflow_runs_github_id ON workflow_runs(github_id);

-- Create Failure Clusters Table
CREATE TABLE IF NOT EXISTS failure_clusters (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    summary TEXT,
    representative_embedding vector(384), -- 384-dimensional vector for all-MiniLM-L6-v2 embeddings
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create Pipeline Failures Table
CREATE TABLE IF NOT EXISTS pipeline_failures (
    id SERIAL PRIMARY KEY,
    workflow_run_id INTEGER REFERENCES workflow_runs(id) ON DELETE CASCADE,
    job_id BIGINT,
    job_name VARCHAR(255) NOT NULL,
    step_name VARCHAR(255),
    failure_reason TEXT,
    log_summary TEXT,
    log_embedding vector(384), -- Updated 384-dimensional vector
    cluster_id INTEGER REFERENCES failure_clusters(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create Test History Table
CREATE TABLE IF NOT EXISTS test_history (
    id SERIAL PRIMARY KEY,
    repository_id INTEGER REFERENCES repositories(id) ON DELETE CASCADE,
    workflow_run_id INTEGER REFERENCES workflow_runs(id) ON DELETE CASCADE,
    test_suite VARCHAR(255),
    test_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL, -- 'passed', 'failed', 'skipped'
    duration DOUBLE PRECISION, -- duration in seconds
    error_message TEXT,
    failure_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
