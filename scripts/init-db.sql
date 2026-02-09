-- =============================================================
-- Loriaa AI CRM - Database Initialization Script
-- PostgreSQL with pgvector extension
-- =============================================================

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Loriaa AI database initialized successfully';
    RAISE NOTICE 'pgvector extension enabled';
    RAISE NOTICE 'uuid-ossp extension enabled';
END $$;
