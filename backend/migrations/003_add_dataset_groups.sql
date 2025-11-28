-- Migration: Add dataset groups and memberships tables
-- Date: 2024-11-26
--
-- Usage with custom schema:
--   psql -v schema_name=myapp -f 003_add_dataset_groups.sql
-- Usage with default schema (public):
--   psql -f 003_add_dataset_groups.sql

-- Set schema (defaults to public if not provided)
SET search_path TO :schema_name, public;

-- Create dataset_groups table
CREATE TABLE IF NOT EXISTS dataset_groups (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    description VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Create dataset_group_memberships table
CREATE TABLE IF NOT EXISTS dataset_group_memberships (
    id VARCHAR PRIMARY KEY,
    group_id VARCHAR NOT NULL REFERENCES dataset_groups(id) ON DELETE CASCADE,
    dataset_id VARCHAR NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    alias VARCHAR,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(group_id, dataset_id)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_dataset_group_memberships_group_id ON dataset_group_memberships(group_id);
CREATE INDEX IF NOT EXISTS idx_dataset_group_memberships_dataset_id ON dataset_group_memberships(dataset_id);
CREATE INDEX IF NOT EXISTS idx_dataset_groups_deleted_at ON dataset_groups(deleted_at);
