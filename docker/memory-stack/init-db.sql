-- Dopemux Unified Memory Graph Database Schema
-- Supports both ConPort project memory and Zep conversational memory

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Graph nodes table
CREATE TABLE IF NOT EXISTS nodes (
    id VARCHAR(255) PRIMARY KEY,
    type VARCHAR(50) NOT NULL, -- decision, task, file, endpoint, message, agent, thread, run
    text TEXT,
    metadata JSONB DEFAULT '{}',
    repo VARCHAR(255),
    author VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Graph edges table
CREATE TABLE IF NOT EXISTS edges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_id VARCHAR(255) NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    to_id VARCHAR(255) NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    relation VARCHAR(100) NOT NULL, -- affects, depends_on, implements, discussed_in, produced_by, belongs_to_thread
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(from_id, to_id, relation)
);

-- Conversation threads for ConPort integration
CREATE TABLE IF NOT EXISTS conversation_threads (
    id VARCHAR(255) PRIMARY KEY,
    title VARCHAR(500),
    repo VARCHAR(255),
    participants TEXT[],
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Messages within threads
CREATE TABLE IF NOT EXISTS messages (
    id VARCHAR(255) PRIMARY KEY,
    thread_id VARCHAR(255) REFERENCES conversation_threads(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- user, assistant, tool
    content TEXT NOT NULL,
    tool_calls JSONB,
    metadata JSONB DEFAULT '{}',
    source VARCHAR(50), -- claude-code, codex-cli, multi-llm-chat
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Memory embeddings mapping (references to Milvus)
CREATE TABLE IF NOT EXISTS embeddings_refs (
    node_id VARCHAR(255) NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    milvus_collection VARCHAR(100) NOT NULL,
    milvus_id VARCHAR(255) NOT NULL,
    embedding_model VARCHAR(100) DEFAULT 'voyage-code-3',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (node_id, milvus_collection)
);

-- Import tracking for Claude Code & Codex CLI histories
CREATE TABLE IF NOT EXISTS import_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source VARCHAR(50) NOT NULL, -- claude-code, codex-cli
    file_path TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'running', -- running, completed, failed
    items_processed INTEGER DEFAULT 0,
    items_total INTEGER,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type);
CREATE INDEX IF NOT EXISTS idx_nodes_repo ON nodes(repo);
CREATE INDEX IF NOT EXISTS idx_nodes_created_at ON nodes(created_at);
CREATE INDEX IF NOT EXISTS idx_edges_from_id ON edges(from_id);
CREATE INDEX IF NOT EXISTS idx_edges_to_id ON edges(to_id);
CREATE INDEX IF NOT EXISTS idx_edges_relation ON edges(relation);
CREATE INDEX IF NOT EXISTS idx_messages_thread_id ON messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_messages_source ON messages(source);

-- Updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers
CREATE TRIGGER update_nodes_updated_at BEFORE UPDATE ON nodes FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_conversation_threads_updated_at BEFORE UPDATE ON conversation_threads FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- Sample data for testing
INSERT INTO nodes (id, type, text, repo, author, metadata) VALUES
('dec_001', 'decision', 'Adopt Milvus for vector embeddings storage', 'dopemux-mvp', 'hue', '{"priority": "high", "status": "implemented"}'),
('file_001', 'file', 'src/conport/memory_server.py', 'dopemux-mvp', 'system', '{"path": "src/conport/memory_server.py", "size": 2048}'),
('task_001', 'task', 'Implement unified memory graph architecture', 'dopemux-mvp', 'hue', '{"status": "in_progress", "assignee": "hue"}')
ON CONFLICT (id) DO NOTHING;

INSERT INTO edges (from_id, to_id, relation, metadata) VALUES
('dec_001', 'file_001', 'affects', '{"reason": "Implementation of Milvus integration"}'),
('dec_001', 'task_001', 'implements', '{"phase": "week1"}')
ON CONFLICT (from_id, to_id, relation) DO NOTHING;

-- Grant permissions for ConPort service
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO dopemux;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO dopemux;