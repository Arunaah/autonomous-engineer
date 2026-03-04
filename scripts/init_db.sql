-- Autonomous Engineer Memory Layer Schema

CREATE TABLE IF NOT EXISTS failures (
    id SERIAL PRIMARY KEY,
    iteration INTEGER NOT NULL,
    pr_number INTEGER,
    error_type VARCHAR(255),
    stack_trace TEXT,
    stage VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fixes (
    id SERIAL PRIMARY KEY,
    failure_id INTEGER REFERENCES failures(id),
    patch_diff TEXT,
    confidence_before FLOAT,
    confidence_after FLOAT,
    success BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS runs (
    id SERIAL PRIMARY KEY,
    request TEXT NOT NULL,
    pr_number INTEGER,
    final_confidence FLOAT,
    iterations_used INTEGER,
    status VARCHAR(50) DEFAULT 'running',
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX idx_failures_error_type ON failures(error_type);
CREATE INDEX idx_runs_status ON runs(status);
