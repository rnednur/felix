-- Migration 005: Add group_id to queries table
-- This allows queries to be associated with dataset groups for multi-table queries

-- Add group_id column to queries table
ALTER TABLE queries
ADD COLUMN group_id VARCHAR REFERENCES dataset_groups(id);

-- Create index for faster lookups
CREATE INDEX idx_queries_group_id ON queries(group_id);

-- Add comment explaining the column
COMMENT ON COLUMN queries.group_id IS 'References a dataset group for multi-table queries. Mutually exclusive with dataset_id.';
