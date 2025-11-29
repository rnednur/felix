-- Migration 006: Add dataset group relationships
-- This allows users to define JOIN conditions between tables in a group

CREATE TABLE IF NOT EXISTS dataset_group_relationships (
    id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
    group_id VARCHAR NOT NULL REFERENCES dataset_groups(id) ON DELETE CASCADE,

    -- From table/column
    from_dataset_id VARCHAR NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    from_column VARCHAR NOT NULL,

    -- To table/column
    to_dataset_id VARCHAR NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    to_column VARCHAR NOT NULL,

    -- JOIN type
    join_type VARCHAR NOT NULL DEFAULT 'INNER' CHECK (join_type IN ('INNER', 'LEFT', 'RIGHT', 'FULL')),

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Prevent duplicate relationships
    UNIQUE(group_id, from_dataset_id, from_column, to_dataset_id, to_column)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_relationships_group_id ON dataset_group_relationships(group_id);
CREATE INDEX IF NOT EXISTS idx_relationships_from_dataset ON dataset_group_relationships(from_dataset_id);
CREATE INDEX IF NOT EXISTS idx_relationships_to_dataset ON dataset_group_relationships(to_dataset_id);

-- Add comment
COMMENT ON TABLE dataset_group_relationships IS 'Defines relationships (JOIN conditions) between datasets in a group';
COMMENT ON COLUMN dataset_group_relationships.join_type IS 'Type of JOIN: INNER, LEFT, RIGHT, or FULL';
