CREATE TABLE IF NOT EXISTS customers (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders (
  id SERIAL PRIMARY KEY,
  customer_id INT NOT NULL REFERENCES customers(id),
  amount NUMERIC(10,2) NOT NULL,
  status TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO customers (name, email)
VALUES
  ('Alice', 'alice@example.com'),
  ('Bob', 'bob@example.com'),
  ('Carol', 'carol@example.com')
ON CONFLICT DO NOTHING;

INSERT INTO orders (customer_id, amount, status)
VALUES
  (1, 123.45, 'paid'),
  (1, 49.99, 'refunded'),
  (2, 200.00, 'paid'),
  (3, 13.37, 'pending')
ON CONFLICT DO NOTHING;
