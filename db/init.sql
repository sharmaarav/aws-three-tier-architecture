CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO customers (name, email)
VALUES
    ('Alice Morgan', 'alice@example.com'),
    ('Ben Carter', 'ben@example.com'),
    ('Charlie Singh', 'charlie@example.com')
ON CONFLICT (email) DO NOTHING;
