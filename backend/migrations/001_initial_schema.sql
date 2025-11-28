-- Initial database schema for AI Analytics Platform
-- Run this if you prefer SQL migrations over Python setup script
--
-- Usage with custom schema:
--   psql -v schema_name=myapp -f 001_initial_schema.sql
-- Usage with default schema (public):
--   psql -f 001_initial_schema.sql

-- Set schema (defaults to public if not provided)
SET search_path TO :schema_name, public;

-- Datasets table
CREATE TABLE IF NOT EXISTS datasets (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    description VARCHAR,
    parquet_path VARCHAR NOT NULL,
    schema_path VARCHAR NOT NULL,
    embedding_path VARCHAR,
    source_type VARCHAR NOT NULL,
    source_url VARCHAR,
    status VARCHAR NOT NULL,
    row_count INTEGER DEFAULT 0,
    size_bytes BIGINT DEFAULT 0,
    dataset_version INTEGER DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Dataset versions table
CREATE TABLE IF NOT EXISTS dataset_versions (
    id VARCHAR PRIMARY KEY,
    dataset_id VARCHAR NOT NULL REFERENCES datasets(id),
    version INTEGER NOT NULL,
    parquet_path VARCHAR NOT NULL,
    schema_path VARCHAR NOT NULL,
    checksum VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Queries table
CREATE TABLE IF NOT EXISTS queries (
    id VARCHAR PRIMARY KEY,
    dataset_id VARCHAR REFERENCES datasets(id),
    nl_input TEXT,
    generated_sql TEXT NOT NULL,
    execution_time_ms INTEGER,
    result_rows INTEGER DEFAULT 0,
    result_bytes BIGINT DEFAULT 0,
    result_path VARCHAR,
    status VARCHAR NOT NULL,
    error_message TEXT,
    query_metadata JSON,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Visualizations table
CREATE TABLE IF NOT EXISTS visualizations (
    id VARCHAR PRIMARY KEY,
    query_id VARCHAR NOT NULL REFERENCES queries(id),
    name VARCHAR NOT NULL,
    chart_type VARCHAR NOT NULL,
    vega_spec JSON NOT NULL,
    thumbnail_path VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Semantic metrics table
CREATE TABLE IF NOT EXISTS semantic_metrics (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE,
    description TEXT,
    formula TEXT NOT NULL,
    grain JSON,
    allowed_aggs JSON,
    default_filters JSON,
    embedding_bytes BYTEA,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Audit logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id VARCHAR PRIMARY KEY,
    action VARCHAR NOT NULL,
    resource_type VARCHAR NOT NULL,
    resource_id VARCHAR,
    audit_metadata JSON,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_datasets_status ON datasets(status);
CREATE INDEX IF NOT EXISTS idx_datasets_created_at ON datasets(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_datasets_deleted_at ON datasets(deleted_at) WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_queries_dataset_id ON queries(dataset_id);
CREATE INDEX IF NOT EXISTS idx_queries_status ON queries(status);
CREATE INDEX IF NOT EXISTS idx_queries_created_at ON queries(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_visualizations_query_id ON visualizations(query_id);

CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);

-- Comments
COMMENT ON TABLE datasets IS 'Uploaded datasets with metadata';
COMMENT ON TABLE queries IS 'Query history with NL input and generated SQL';
COMMENT ON TABLE visualizations IS 'Saved visualizations with Vega-Lite specs';
COMMENT ON TABLE semantic_metrics IS 'User-defined metrics for semantic layer';
COMMENT ON TABLE audit_logs IS 'Audit trail for all operations';
