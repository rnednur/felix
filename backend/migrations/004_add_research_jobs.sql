-- Migration: Add research jobs table for async deep research
-- Date: 2024-11-27
--
-- Usage with custom schema:
--   psql -v schema_name=myapp -f 004_add_research_jobs.sql
-- Usage with default schema (public):
--   psql -f 004_add_research_jobs.sql

-- Set schema (defaults to public if not provided)
SET search_path TO :schema_name, public;

-- Create enum for research job status
CREATE TYPE research_job_status AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');

-- Create research_jobs table
CREATE TABLE IF NOT EXISTS research_jobs (
    id VARCHAR PRIMARY KEY,
    dataset_id VARCHAR NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    main_question TEXT NOT NULL,
    verbose_mode INTEGER DEFAULT 0 NOT NULL,

    celery_task_id VARCHAR,

    status research_job_status DEFAULT 'pending' NOT NULL,
    current_stage VARCHAR,
    progress_percentage INTEGER DEFAULT 0,

    result JSONB,
    error_message TEXT,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    execution_time_seconds INTEGER,

    job_metadata JSONB
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_research_jobs_dataset_id ON research_jobs(dataset_id);
CREATE INDEX IF NOT EXISTS idx_research_jobs_status ON research_jobs(status);
CREATE INDEX IF NOT EXISTS idx_research_jobs_celery_task_id ON research_jobs(celery_task_id);
CREATE INDEX IF NOT EXISTS idx_research_jobs_created_at ON research_jobs(created_at DESC);

-- Add comments
COMMENT ON TABLE research_jobs IS 'Async deep research job tracking';
COMMENT ON COLUMN research_jobs.verbose_mode IS 'Verbose mode: 0=off, 1=on';
COMMENT ON COLUMN research_jobs.progress_percentage IS 'Progress: 0-100';
COMMENT ON COLUMN research_jobs.result IS 'Full DeepResearchResponse JSON';
