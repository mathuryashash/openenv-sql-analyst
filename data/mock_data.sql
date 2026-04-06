-- OpenEnv SQL Analyst - Mock Data
-- Tables: users, products, purchases
-- Approximately 50 rows total for lightweight operation

-- =============================================
-- TABLE: users
-- =============================================
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    email TEXT NOT NULL,
    country TEXT NOT NULL,
    created_at TEXT NOT NULL
);

INSERT INTO users (user_id, username, email, country, created_at) VALUES
(1, 'alice', 'alice@example.com', 'USA', '2023-01-15'),
(2, 'bob', 'bob@example.com', 'Canada', '2023-02-20'),
(3, 'charlie', 'charlie@example.com', 'UK', '2023-03-10'),
(4, 'diana', 'diana@example.com', 'USA', '2023-04-05'),
(5, 'eve', 'eve@example.com', 'Germany', '2023-05-12'),
(6, 'frank', 'frank@example.com', 'France', '2023-06-18'),
(7, 'grace', 'grace@example.com', 'USA', '2023-07-22'),
(8, 'henry', 'henry@example.com', 'Canada', '2023-08-30'),
(9, 'iris', 'iris@example.com', 'UK', '2023-09-14'),
(10, 'jack', 'jack@example.com', 'USA', '2023-10-01'),
(11, 'karen', 'karen@example.com', 'Germany', '2023-10-15'),
(12, 'leo', 'leo@example.com', 'France', '2023-11-02'),
(13, 'maria', 'maria@example.com', 'Spain', '2023-11-20'),
(14, 'nathan', 'nathan@example.com', 'USA', '2023-12-05'),
(15, 'olivia', 'olivia@example.com', 'Canada', '2023-12-18');

-- =============================================
-- TABLE: products
-- =============================================
CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL,
    stock INTEGER NOT NULL
);

INSERT INTO products (product_id, product_name, category, price, stock) VALUES
(1, 'Laptop Pro', 'Electronics', 1299.99, 50),
(2, 'Wireless Mouse', 'Electronics', 29.99, 200),
(3, 'USB-C Hub', 'Electronics', 49.99, 150),
(4, 'Mechanical Keyboard', 'Electronics', 89.99, 100),
(5, 'Monitor 27"', 'Electronics', 349.99, 75),
(6, 'Desk Chair', 'Furniture', 199.99, 40),
(7, 'Standing Desk', 'Furniture', 449.99, 25),
(8, 'Desk Lamp', 'Furniture', 34.99, 120),
(9, 'Notebook Pack', 'Office', 12.99, 300),
(10, 'Pen Set', 'Office', 8.99, 500),
(11, 'Headphones', 'Electronics', 149.99, 80),
(12, 'Webcam HD', 'Electronics', 79.99, 90),
(13, 'Mousepad XL', 'Electronics', 19.99, 250),
(14, 'Cable Organizer', 'Office', 14.99, 180),
(15, 'Monitor Stand', 'Furniture', 59.99, 60);

-- =============================================
-- TABLE: purchases
-- =============================================
CREATE TABLE IF NOT EXISTS purchases (
    purchase_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    purchase_date TEXT NOT NULL,
    total_amount REAL NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

INSERT INTO purchases (purchase_id, user_id, product_id, quantity, purchase_date, total_amount) VALUES
(1, 1, 1, 1, '2023-06-01', 1299.99),
(2, 1, 2, 2, '2023-06-01', 59.98),
(3, 2, 4, 1, '2023-06-15', 89.99),
(4, 3, 5, 1, '2023-07-01', 349.99),
(5, 4, 6, 1, '2023-07-10', 199.99),
(6, 5, 7, 1, '2023-07-20', 449.99),
(7, 1, 11, 1, '2023-08-01', 149.99),
(8, 6, 3, 2, '2023-08-05', 99.98),
(9, 7, 9, 5, '2023-08-10', 64.95),
(10, 8, 10, 10, '2023-08-15', 89.90),
(11, 2, 12, 1, '2023-09-01', 79.99),
(12, 9, 8, 2, '2023-09-10', 69.98),
(13, 10, 13, 1, '2023-09-15', 19.99),
(14, 3, 14, 3, '2023-09-20', 44.97),
(15, 4, 15, 1, '2023-10-01', 59.99),
(16, 11, 1, 1, '2023-10-05', 1299.99),
(17, 12, 2, 3, '2023-10-10', 89.97),
(18, 5, 4, 1, '2023-10-15', 89.99),
(19, 13, 11, 2, '2023-10-20', 299.98),
(20, 14, 5, 1, '2023-11-01', 349.99);
