-- Migration to implement new geopolitical risk technical specification
-- This creates the new schema while preserving existing data

-- First, create new tables according to the technical spec

-- Raw events from GDELT and other sources
CREATE TABLE IF NOT EXISTS raw_events (
    id SERIAL PRIMARY KEY,
    country_id INTEGER REFERENCES countries(id),
    event_date DATE NOT NULL,
    title TEXT,
    source_url TEXT,
    domain VARCHAR(100),
    language VARCHAR(10),
    tone DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_raw_events_country_date ON raw_events(country_id, event_date);

-- Processed events with NLP classification
CREATE TABLE IF NOT EXISTS processed_events (
    id SERIAL PRIMARY KEY,
    raw_event_id INTEGER REFERENCES raw_events(id),
    risk_category VARCHAR(20), -- conflict, protest, diplomatic, economic
    sentiment_score DECIMAL(5,2), -- -1 to 1
    severity_score DECIMAL(5,2), -- 0 to 1
    confidence DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Economic indicators from World Bank
CREATE TABLE IF NOT EXISTS economic_indicators (
    id SERIAL PRIMARY KEY,
    country_id INTEGER REFERENCES countries(id),
    indicator_code VARCHAR(20),
    year INTEGER,
    value DECIMAL(15,4),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(country_id, indicator_code, year)
);

-- Engineered features for ML pipeline
CREATE TABLE IF NOT EXISTS feature_vectors (
    id SERIAL PRIMARY KEY,
    country_id INTEGER REFERENCES countries(id),
    feature_date DATE NOT NULL,
    features JSONB, -- All engineered features as JSON
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feature_vectors_country_date ON feature_vectors(country_id, feature_date);

-- New risk scores table with ML model outputs
CREATE TABLE IF NOT EXISTS risk_scores_v2 (
    id SERIAL PRIMARY KEY,
    country_id INTEGER REFERENCES countries(id),
    score_date DATE NOT NULL,
    overall_score DECIMAL(5,2),
    political_stability_score DECIMAL(5,2),
    conflict_risk_score DECIMAL(5,2),
    economic_risk_score DECIMAL(5,2),
    institutional_quality_score DECIMAL(5,2),
    spillover_risk_score DECIMAL(5,2),
    confidence_lower DECIMAL(5,2),
    confidence_upper DECIMAL(5,2),
    model_version VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(country_id, score_date)
);

-- Update countries table to match spec
ALTER TABLE countries 
ADD COLUMN IF NOT EXISTS iso_code VARCHAR(3),
ADD COLUMN IF NOT EXISTS income_group VARCHAR(50);

-- Create unique constraint on iso_code if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'countries_iso_code_key'
    ) THEN
        ALTER TABLE countries ADD CONSTRAINT countries_iso_code_key UNIQUE (iso_code);
    END IF;
END
$$;

-- Update existing countries with ISO codes based on country codes
UPDATE countries SET iso_code = code WHERE iso_code IS NULL;

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_economic_indicators_country_indicator ON economic_indicators(country_id, indicator_code);
CREATE INDEX IF NOT EXISTS idx_risk_scores_v2_country_date ON risk_scores_v2(country_id, score_date);
CREATE INDEX IF NOT EXISTS idx_processed_events_category ON processed_events(risk_category);