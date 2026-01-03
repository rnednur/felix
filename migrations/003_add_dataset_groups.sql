-- Migration: Add dataset groups for multi-dataset queries
-- Created: 2025-11-25

-- Create dataset_groups table
CREATE TABLE IF NOT EXISTS dataset_groups (
    id VARCHAR PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Create dataset_group_memberships table (many-to-many relationship)
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

-- Add comments
COMMENT ON TABLE dataset_groups IS 'Groups of datasets that can be queried together';
COMMENT ON TABLE dataset_group_memberships IS 'Membership table linking datasets to groups';
COMMENT ON COLUMN dataset_group_memberships.alias IS 'Optional alias for the dataset when used in queries (e.g., "sales", "customers")';
COMMENT ON COLUMN dataset_group_memberships.display_order IS 'Order in which datasets are displayed/processed within the group';
