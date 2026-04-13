-- Dopemux Unified Database Initialization
-- Creates multiple databases in a single PostgreSQL instance
-- This eliminates the need for multiple PostgreSQL containers
--
-- !! LOCAL DEV ONLY !!
-- Production credentials are injected via docker-compose environment variables.
-- These defaults are used only for local docker-compose.unified.yml development.

-- Create databases for different services
CREATE DATABASE dopemux_memory;
CREATE DATABASE conport;
CREATE DATABASE metamcp;

-- Create users with appropriate permissions
CREATE USER conport_user WITH PASSWORD 'dev_conport';
CREATE USER metamcp_user WITH PASSWORD 'dev_metamcp';
CREATE USER memory_user WITH PASSWORD 'dev_memory';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE dopemux_memory TO memory_user;
GRANT ALL PRIVILEGES ON DATABASE conport TO conport_user;
GRANT ALL PRIVILEGES ON DATABASE metamcp TO metamcp_user;

-- Grant permissions to main dopemux user as well (for admin access)
GRANT ALL PRIVILEGES ON DATABASE dopemux_memory TO dopemux;
GRANT ALL PRIVILEGES ON DATABASE conport TO dopemux;
GRANT ALL PRIVILEGES ON DATABASE metamcp TO dopemux;

-- Create schemas for organization
\c dopemux_memory;
CREATE SCHEMA IF NOT EXISTS public;
CREATE SCHEMA IF NOT EXISTS vector_store;
CREATE SCHEMA IF NOT EXISTS embeddings;

\c conport;
CREATE SCHEMA IF NOT EXISTS public;
CREATE SCHEMA IF NOT EXISTS decisions;
CREATE SCHEMA IF NOT EXISTS context;
CREATE SCHEMA IF NOT EXISTS memory;

\c metamcp;
CREATE SCHEMA IF NOT EXISTS public;
CREATE SCHEMA IF NOT EXISTS mcp_registry;
CREATE SCHEMA IF NOT EXISTS monitoring;
