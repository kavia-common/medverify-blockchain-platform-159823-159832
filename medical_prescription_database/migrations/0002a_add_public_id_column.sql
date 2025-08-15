-- 0002a_add_public_id_column.sql
-- Purpose: Ensure users.public_id column exists before indices/triggers reference it.
-- This supports upgrading older databases that may not have had the column,
-- and is a no-op for fresh databases initialized with 0001_create_schema.sql.

PRAGMA foreign_keys = OFF;

-- Add the public_id column if it does not already exist.
-- Note: Requires SQLite 3.35+ for IF NOT EXISTS. On modern Python 3.11 images,
-- SQLite is sufficiently recent. This remains a no-op if the column is present.
ALTER TABLE users ADD COLUMN IF NOT EXISTS public_id TEXT;

PRAGMA foreign_keys = ON;

-- Create an index on public_id if missing. 0003_indices.sql also attempts to
-- create this index but uses IF NOT EXISTS, so this remains idempotent.
CREATE INDEX IF NOT EXISTS idx_users_public_id ON users(public_id);
