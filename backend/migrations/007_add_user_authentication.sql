-- Migration 007: Add User Authentication and Sharing
-- This migration adds user authentication, dataset ownership, and sharing functionality

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR PRIMARY KEY,
    email VARCHAR NOT NULL UNIQUE,
    username VARCHAR NOT NULL UNIQUE,
    hashed_password VARCHAR NOT NULL,
    full_name VARCHAR,
    role VARCHAR NOT NULL DEFAULT 'USER',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_deleted_at ON users(deleted_at);

-- Add owner_id to datasets
ALTER TABLE datasets ADD COLUMN IF NOT EXISTS owner_id VARCHAR;
ALTER TABLE datasets ADD CONSTRAINT fk_datasets_owner
    FOREIGN KEY (owner_id) REFERENCES users(id);
CREATE INDEX idx_datasets_owner_id ON datasets(owner_id);

-- Add owner_id to dataset_groups
ALTER TABLE dataset_groups ADD COLUMN IF NOT EXISTS owner_id VARCHAR;
ALTER TABLE dataset_groups ADD CONSTRAINT fk_dataset_groups_owner
    FOREIGN KEY (owner_id) REFERENCES users(id);
CREATE INDEX idx_dataset_groups_owner_id ON dataset_groups(owner_id);

-- Create dataset_members table (team collaboration)
CREATE TABLE IF NOT EXISTS dataset_members (
    id VARCHAR PRIMARY KEY,
    dataset_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    role VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    removed_at TIMESTAMP,
    FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT uix_dataset_user UNIQUE (dataset_id, user_id)
);

CREATE INDEX idx_dataset_members_dataset_id ON dataset_members(dataset_id);
CREATE INDEX idx_dataset_members_user_id ON dataset_members(user_id);
CREATE INDEX idx_dataset_members_removed_at ON dataset_members(removed_at);

-- Create dataset_group_members table (team collaboration)
CREATE TABLE IF NOT EXISTS dataset_group_members (
    id VARCHAR PRIMARY KEY,
    group_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    role VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    removed_at TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES dataset_groups(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT uix_group_user UNIQUE (group_id, user_id)
);

CREATE INDEX idx_dataset_group_members_group_id ON dataset_group_members(group_id);
CREATE INDEX idx_dataset_group_members_user_id ON dataset_group_members(user_id);
CREATE INDEX idx_dataset_group_members_removed_at ON dataset_group_members(removed_at);

-- Create dataset_shares table (external sharing)
CREATE TABLE IF NOT EXISTS dataset_shares (
    id VARCHAR PRIMARY KEY,
    dataset_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    permission VARCHAR NOT NULL DEFAULT 'VIEW',
    expires_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP,
    FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_dataset_shares_dataset_id ON dataset_shares(dataset_id);
CREATE INDEX idx_dataset_shares_user_id ON dataset_shares(user_id);
CREATE INDEX idx_dataset_shares_revoked_at ON dataset_shares(revoked_at);

-- Create dataset_group_shares table
CREATE TABLE IF NOT EXISTS dataset_group_shares (
    id VARCHAR PRIMARY KEY,
    group_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    permission VARCHAR NOT NULL DEFAULT 'VIEW',
    expires_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES dataset_groups(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_dataset_group_shares_group_id ON dataset_group_shares(group_id);
CREATE INDEX idx_dataset_group_shares_user_id ON dataset_group_shares(user_id);
CREATE INDEX idx_dataset_group_shares_revoked_at ON dataset_group_shares(revoked_at);

-- Create public_datasets table
CREATE TABLE IF NOT EXISTS public_datasets (
    id VARCHAR PRIMARY KEY,
    dataset_id VARCHAR NOT NULL UNIQUE,
    allow_download BOOLEAN NOT NULL DEFAULT FALSE,
    allow_query BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    revoked_at TIMESTAMP,
    FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
);

CREATE INDEX idx_public_datasets_dataset_id ON public_datasets(dataset_id);
CREATE INDEX idx_public_datasets_revoked_at ON public_datasets(revoked_at);

-- Update audit_logs table to include user tracking
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS user_id VARCHAR;
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS ip_address VARCHAR;
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS user_agent VARCHAR;
ALTER TABLE audit_logs ADD CONSTRAINT fk_audit_logs_user
    FOREIGN KEY (user_id) REFERENCES users(id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);

COMMENT ON TABLE users IS 'User accounts and authentication';
COMMENT ON TABLE dataset_members IS 'Team members with roles (OWNER, ADMIN, EDITOR, ANALYST, VIEWER)';
COMMENT ON TABLE dataset_group_members IS 'Team members for dataset groups with roles';
COMMENT ON TABLE dataset_shares IS 'External sharing with specific users (temporary or limited access)';
COMMENT ON TABLE dataset_group_shares IS 'External sharing for dataset groups';
COMMENT ON TABLE public_datasets IS 'Publicly accessible datasets';
