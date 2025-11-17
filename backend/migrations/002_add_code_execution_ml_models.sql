-- Migration: Add code execution and ML models support
-- Created: 2025-11-10

-- Create enum types for code execution
CREATE TYPE execution_mode AS ENUM ('sql', 'python', 'ml', 'workflow', 'stats');
CREATE TYPE execution_status AS ENUM ('PENDING', 'RUNNING', 'SUCCESS', 'FAILED', 'TIMEOUT');

-- Create code_executions table
CREATE TABLE IF NOT EXISTS code_executions (
    id VARCHAR(255) PRIMARY KEY,
    dataset_id VARCHAR(255) NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,

    -- Input
    nl_input TEXT NOT NULL,
    mode execution_mode NOT NULL,

    -- Generated code
    generated_code TEXT,
    generated_sql TEXT,

    -- Execution details
    execution_status execution_status NOT NULL DEFAULT 'PENDING',
    execution_time_ms INTEGER,

    -- Results
    result_path VARCHAR(500),
    result_summary JSONB,
    visualizations JSONB,

    -- Error handling
    error_message TEXT,
    error_trace TEXT,

    -- Code metadata
    code_metadata JSONB,

    -- Workflow info
    workflow_id VARCHAR(255),
    step_number INTEGER,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Create indexes for code_executions
CREATE INDEX idx_code_executions_dataset_id ON code_executions(dataset_id);
CREATE INDEX idx_code_executions_mode ON code_executions(mode);
CREATE INDEX idx_code_executions_status ON code_executions(execution_status);
CREATE INDEX idx_code_executions_workflow_id ON code_executions(workflow_id);
CREATE INDEX idx_code_executions_created_at ON code_executions(created_at DESC);

-- Create ml_models table
CREATE TABLE IF NOT EXISTS ml_models (
    id VARCHAR(255) PRIMARY KEY,
    dataset_id VARCHAR(255) NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    code_execution_id VARCHAR(255) REFERENCES code_executions(id) ON DELETE SET NULL,

    -- Model info
    name VARCHAR(255),
    model_type VARCHAR(100) NOT NULL,
    framework VARCHAR(100),

    -- Training details
    features JSONB NOT NULL,
    target_column VARCHAR(255),
    training_info JSONB,

    -- Model performance
    metrics JSONB NOT NULL,
    feature_importance JSONB,

    -- Persistence
    model_artifact_path VARCHAR(500) NOT NULL,
    model_metadata_path VARCHAR(500),

    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'active',

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for ml_models
CREATE INDEX idx_ml_models_dataset_id ON ml_models(dataset_id);
CREATE INDEX idx_ml_models_code_execution_id ON ml_models(code_execution_id);
CREATE INDEX idx_ml_models_model_type ON ml_models(model_type);
CREATE INDEX idx_ml_models_status ON ml_models(status);
CREATE INDEX idx_ml_models_created_at ON ml_models(created_at DESC);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_ml_models_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_ml_models_updated_at
    BEFORE UPDATE ON ml_models
    FOR EACH ROW
    EXECUTE FUNCTION update_ml_models_updated_at();

-- Add comments for documentation
COMMENT ON TABLE code_executions IS 'Stores Python/ML code execution history and results';
COMMENT ON TABLE ml_models IS 'Stores trained ML models with metadata and performance metrics';
COMMENT ON COLUMN code_executions.mode IS 'Execution mode: sql, python, ml, workflow, or stats';
COMMENT ON COLUMN code_executions.code_metadata IS 'Metadata including retrieved columns, confidence scores, workflow steps';
COMMENT ON COLUMN ml_models.features IS 'JSON array of feature column names used for training';
COMMENT ON COLUMN ml_models.metrics IS 'Performance metrics: R², RMSE, accuracy, precision, recall, etc.';
