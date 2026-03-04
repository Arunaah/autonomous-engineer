-- ============================================================
-- AUTONOMOUS ENGINEER — PostgreSQL Schema
-- Memory Layer: failures + fixes tables
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Failures table: stores CI failure patterns
CREATE TABLE IF NOT EXISTS failures (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    repo            TEXT NOT NULL,
    pr_number       INT,
    iteration       INT NOT NULL DEFAULT 1,
    error_type      TEXT NOT NULL,
    stage           TEXT NOT NULL,  -- static|testing|simulation|stress|reviewer
    stack_trace     TEXT,
    file_path       TEXT,
    line_number     INT,
    raw_output      TEXT,
    confidence_before FLOAT,
    confidence_after  FLOAT
);

-- Fixes table: stores successful patches
CREATE TABLE IF NOT EXISTS fixes (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    failure_id      UUID REFERENCES failures(id),
    repo            TEXT NOT NULL,
    pr_number       INT,
    iteration       INT NOT NULL,
    patch_diff      TEXT NOT NULL,
    fix_strategy    TEXT,
    confidence_delta FLOAT,
    success         BOOLEAN NOT NULL DEFAULT FALSE
);

-- Index for fast failure pattern lookups
CREATE INDEX IF NOT EXISTS idx_failures_error_type ON failures(error_type);
CREATE INDEX IF NOT EXISTS idx_failures_repo ON failures(repo);
CREATE INDEX IF NOT EXISTS idx_failures_stage ON failures(stage);
CREATE INDEX IF NOT EXISTS idx_fixes_failure_id ON fixes(failure_id);
CREATE INDEX IF NOT EXISTS idx_fixes_success ON fixes(success);

-- View: successful fix patterns (used for prompt injection)
CREATE OR REPLACE VIEW successful_fix_patterns AS
SELECT
    f.error_type,
    f.stage,
    f.stack_trace,
    fx.patch_diff,
    fx.fix_strategy,
    fx.confidence_delta,
    COUNT(*) AS usage_count
FROM failures f
JOIN fixes fx ON f.id = fx.failure_id
WHERE fx.success = TRUE
GROUP BY f.error_type, f.stage, f.stack_trace, fx.patch_diff, fx.fix_strategy, fx.confidence_delta
ORDER BY usage_count DESC;
