CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS filings(
    id SERIAL PRIMARY KEY,
    company TEXT NOT NULL,
    fiscal_year INT NOT NULL,
    source_url TEXT NOT NULL,
    UNIQUE(company, fiscal_year)
);

CREATE TABLE IF NOT EXISTS chunks(
    id SERIAL PRIMARY KEY,
    filing_id INT NOT NULL REFERENCES filings(id) ON DELETE CASCADE,
    section TEXT NOT NULL,
    chunk_index INT NOT NULL,
    text TEXT NOT NULL,
    embedding vector(384) NOT NULL
);
    