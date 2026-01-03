-- Migration: Add agent tables for multi-agent architecture
-- Created: 2026-01-03

-- Agent Sessions table
CREATE TABLE IF NOT EXISTS agent_sessions (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR,
    dataset_id VARCHAR NOT NULL REFERENCES datasets(id),
    name VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Create indexes for agent_sessions
CREATE INDEX IF NOT EXISTS idx_agent_sessions_user_id ON agent_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_dataset_id ON agent_sessions(dataset_id);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_created_at ON agent_sessions(created_at);

-- Agent Messages table
CREATE TABLE IF NOT EXISTS agent_messages (
    id VARCHAR PRIMARY KEY,
    session_id VARCHAR NOT NULL REFERENCES agent_sessions(id) ON DELETE CASCADE,
    role VARCHAR NOT NULL,
    content TEXT NOT NULL,
    agent_name VARCHAR,
    code TEXT,
    result_data JSONB,
    tokens_used INTEGER DEFAULT 0,
    execution_time_ms INTEGER DEFAULT 0,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for agent_messages
CREATE INDEX IF NOT EXISTS idx_agent_messages_session_id ON agent_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_messages_timestamp ON agent_messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_agent_messages_role ON agent_messages(role);

-- Agent Executions table
CREATE TABLE IF NOT EXISTS agent_executions (
    id VARCHAR PRIMARY KEY,
    session_id VARCHAR REFERENCES agent_sessions(id) ON DELETE CASCADE,
    agent_name VARCHAR NOT NULL,
    query TEXT NOT NULL,
    dataset_id VARCHAR NOT NULL REFERENCES datasets(id),
    execution_mode VARCHAR,
    status VARCHAR NOT NULL,
    execution_time_ms INTEGER,
    tokens_used INTEGER,
    cost_usd FLOAT,
    result_summary TEXT,
    error_message TEXT,
    result_data JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for agent_executions
CREATE INDEX IF NOT EXISTS idx_agent_executions_session_id ON agent_executions(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_executions_agent_name ON agent_executions(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_executions_dataset_id ON agent_executions(dataset_id);
CREATE INDEX IF NOT EXISTS idx_agent_executions_status ON agent_executions(status);
CREATE INDEX IF NOT EXISTS idx_agent_executions_created_at ON agent_executions(created_at);

-- Comments
COMMENT ON TABLE agent_sessions IS 'Stores agent chat sessions';
COMMENT ON TABLE agent_messages IS 'Stores messages in agent conversations';
COMMENT ON TABLE agent_executions IS 'Tracks agent execution metrics and results';
