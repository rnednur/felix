-- Migration: Add spatial/map fields to datasets table
-- Date: 2025-12-15
-- Description: Adds fields to support Talk2Map functionality

-- Add spatial data flag
ALTER TABLE datasets
ADD COLUMN has_spatial_data BOOLEAN NOT NULL DEFAULT FALSE;

-- Add spatial configuration (stores detected columns and Kepler.gl config)
ALTER TABLE datasets
ADD COLUMN spatial_config JSONB NULL;

-- Create index for faster spatial dataset queries
CREATE INDEX idx_datasets_has_spatial_data ON datasets(has_spatial_data) WHERE has_spatial_data = TRUE;

-- Add comment
COMMENT ON COLUMN datasets.has_spatial_data IS 'Indicates if dataset contains spatial data (lat/lng, addresses, etc.)';
COMMENT ON COLUMN datasets.spatial_config IS 'Stores spatial column metadata and Kepler.gl configuration as JSON';
