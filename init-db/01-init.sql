-- Create the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the collections table
CREATE TABLE IF NOT EXISTS collections (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR NOT NULL,
    collection_id INTEGER REFERENCES collections(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chunks_ollama (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    content_vector vector(768),
    chunk_index INTEGER NOT NULL,
    page_number INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chunks_openai (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    content_vector vector(1536),
    chunk_index INTEGER NOT NULL,
    page_number INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add comments to remind about the vector dimensions
COMMENT ON COLUMN chunks_ollama.content_vector IS 'Vector dimension for Ollama embeddings (768)';
COMMENT ON COLUMN chunks_openai.content_vector IS 'Vector dimension for OpenAI embeddings (1536)';

-- Insert default collection
INSERT INTO collections (name) VALUES ('Default') ON CONFLICT (name) DO NOTHING;

