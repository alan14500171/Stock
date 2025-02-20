-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME
);

-- 股票表
CREATE TABLE IF NOT EXISTS stocks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(20) NOT NULL,
    market VARCHAR(10) NOT NULL,
    name VARCHAR(100) NOT NULL,
    full_name VARCHAR(200),
    industry VARCHAR(50),
    currency VARCHAR(3),
    current_price DECIMAL(15,4),
    price_updated_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uix_code_market (code, market)
);

-- 交易记录表
CREATE TABLE IF NOT EXISTS stock_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    stock_code VARCHAR(20) NOT NULL,
    stock_name VARCHAR(100),
    market VARCHAR(10) NOT NULL,
    currency VARCHAR(3),
    transaction_date DATE NOT NULL,
    transaction_type ENUM('buy', 'sell') NOT NULL,
    transaction_code VARCHAR(50) NOT NULL UNIQUE,
    total_amount DECIMAL(15,2) NOT NULL,
    total_quantity INT NOT NULL,
    broker_fee DECIMAL(10,2) DEFAULT 0,
    transaction_levy DECIMAL(10,2) DEFAULT 0,
    stamp_duty DECIMAL(10,2) DEFAULT 0,
    trading_fee DECIMAL(10,2) DEFAULT 0,
    deposit_fee DECIMAL(10,2) DEFAULT 0,
    exchange_rate DECIMAL(10,4) DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 汇率表
CREATE TABLE IF NOT EXISTS exchange_rates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    currency VARCHAR(10) NOT NULL,
    rate DECIMAL(10,4) NOT NULL,
    rate_date DATE NOT NULL,
    source VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uix_currency_date (currency, rate_date)
); 