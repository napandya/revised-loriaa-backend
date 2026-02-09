-- Initialize PostgreSQL with pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Grant all privileges to the database user
GRANT ALL PRIVILEGES ON DATABASE loriaa_db TO loriaa_user;
