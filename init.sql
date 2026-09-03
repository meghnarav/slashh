CREATE TABLE IF NOT EXISTS banks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS cards (
    id SERIAL PRIMARY KEY,
    bank_id INT REFERENCES banks(id),
    card_name VARCHAR(150) NOT NULL,
    affiliate_apply_url TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS merchants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS offers (
    id SERIAL PRIMARY KEY,
    card_id INT REFERENCES cards(id) ON DELETE CASCADE,
    merchant_id INT REFERENCES merchants(id) ON DELETE CASCADE,
    discount_type VARCHAR(20) NOT NULL,
    discount_value NUMERIC(10, 2) NOT NULL,
    min_spend NUMERIC(10, 2) DEFAULT 0,
    max_cap NUMERIC(10, 2),
    promo_code VARCHAR(50),
    valid_until DATE
);

-- Seed Initial Banks
INSERT INTO banks (name) VALUES 
('HDFC Bank'), 
('ICICI Bank'), 
('SBI Card'), 
('Axis Bank') 
ON CONFLICT DO NOTHING;

-- Seed Initial Cards
INSERT INTO cards (bank_id, card_name, affiliate_apply_url) VALUES 
(1, 'HDFC Millennia', 'https://example.com/apply/hdfc-millennia'),
(2, 'ICICI Amazon Pay', 'https://example.com/apply/icici-amazon-pay'),
(3, 'SBI Cashback', 'https://example.com/apply/sbi-cashback'),
(4, 'Axis Airtel', 'https://example.com/apply/axis-airtel');

-- Seed Merchants
INSERT INTO merchants (name, category) VALUES 
('Swiggy', 'Food'),
('Zomato', 'Food'),
('Blinkit', 'Quick Commerce'),
('Amazon', 'Ecommerce')
ON CONFLICT DO NOTHING;

-- Seed Offers
INSERT INTO offers (card_id, merchant_id, discount_type, discount_value, min_spend, max_cap, promo_code, valid_until) VALUES
(1, 1, 'PERCENTAGE', 10.00, 500.00, 100.00, 'HDFC100', '2026-12-31'),
(2, 4, 'PERCENTAGE', 5.00, 0.00, NULL, 'APAY5', '2026-12-31'),
(3, 1, 'PERCENTAGE', 15.00, 400.00, 150.00, 'SBISAVE', '2026-12-31'),
(4, 3, 'PERCENTAGE', 10.00, 600.00, 120.00, 'AIRTEL10', '2026-12-31');