-- Enable UUID generation if available
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS analysis_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code_hash TEXT NOT NULL,
    code_snippet TEXT,
    suggestions JSONB NOT NULL,
    analysis_time_ms INTEGER,
    language_version VARCHAR(32),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_analysis_history_created_at ON analysis_history (created_at);
CREATE INDEX IF NOT EXISTS ix_analysis_history_code_hash ON analysis_history USING BTREE (code_hash);
CREATE INDEX IF NOT EXISTS ix_analysis_history_suggestions ON analysis_history USING GIN (suggestions);
