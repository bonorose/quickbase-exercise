-- ******************************************************************************
-- * @file    02_seed.sql
-- * @brief   Initial seed data. Run by the postgres entrypoint on first start only.
-- ******************************************************************************

-- Local dev login: admin@quickbase.local / admin123 (bcrypt, cost 12)
INSERT INTO users (email, password_hash, full_name) VALUES
    ('admin@quickbase.local', '$2b$12$t5WxNRcJHPppW3wf..Sjf.ysNJ9VjDH1qpKXvVw11qP5Q.xOPDQ/.', 'Admin User')
ON CONFLICT (email) DO NOTHING;

INSERT INTO items (name, description) VALUES
    ('First item',  'Seeded placeholder item #1'),
    ('Second item', 'Seeded placeholder item #2'),
    ('Third item',  NULL)
ON CONFLICT (name) DO NOTHING;
