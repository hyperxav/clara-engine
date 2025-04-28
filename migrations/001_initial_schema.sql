-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create clients table
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    persona_prompt TEXT NOT NULL,
    twitter_key TEXT NOT NULL,
    twitter_secret TEXT NOT NULL,
    access_token TEXT NOT NULL,
    access_secret TEXT NOT NULL,
    posting_hours JSONB NOT NULL DEFAULT '[]'::JSONB,
    timezone TEXT NOT NULL DEFAULT 'UTC',
    vector_index_name TEXT,
    last_posted_at TIMESTAMP WITH TIME ZONE,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_timezone CHECK (timezone IN (SELECT name FROM pg_timezone_names))
);

-- Create tweets table
CREATE TABLE tweets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    tweet_text TEXT NOT NULL,
    tweet_url TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    posted_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT valid_status CHECK (status IN ('pending', 'posted', 'failed'))
);

-- Create indexes
CREATE INDEX idx_tweets_client_id ON tweets(client_id);
CREATE INDEX idx_tweets_status ON tweets(status);
CREATE INDEX idx_tweets_created_at ON tweets(created_at);
CREATE INDEX idx_clients_active ON clients(active);
CREATE INDEX idx_clients_last_posted_at ON clients(last_posted_at) WHERE active = true;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for clients table
CREATE TRIGGER update_clients_updated_at
    BEFORE UPDATE ON clients
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add row level security policies
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE tweets ENABLE ROW LEVEL SECURITY;

-- Create policies for clients table
CREATE POLICY "Enable read access for authenticated users only" ON clients
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Enable insert for authenticated users only" ON clients
    FOR INSERT
    TO authenticated
    WITH CHECK (true);

CREATE POLICY "Enable update for authenticated users only" ON clients
    FOR UPDATE
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- Create policies for tweets table
CREATE POLICY "Enable read access for authenticated users only" ON tweets
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Enable insert for authenticated users only" ON tweets
    FOR INSERT
    TO authenticated
    WITH CHECK (true);

CREATE POLICY "Enable update for authenticated users only" ON tweets
    FOR UPDATE
    TO authenticated
    USING (true)
    WITH CHECK (true); 