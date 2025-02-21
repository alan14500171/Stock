-- 创建数据库
CREATE DATABASE IF NOT EXISTS Stock DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE stock;

-- 修改数据库字符集
ALTER DATABASE Stock CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 修改表字符集
ALTER TABLE users CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE stocks CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE stock_transactions CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE stock_transaction_details CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE exchange_rates CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE COMMENT '用户名',
    password_hash VARCHAR(255) COMMENT '密码哈希',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否激活',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    last_login DATETIME COMMENT '最后登录时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 股票表
CREATE TABLE IF NOT EXISTS stocks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(20) NOT NULL COMMENT '股票代码',
    market VARCHAR(10) NOT NULL COMMENT '市场(HK/USA)',
    name VARCHAR(100) NOT NULL COMMENT '股票名称',
    full_name VARCHAR(200) COMMENT '股票全称',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_code_market (code, market) COMMENT '股票代码和市场唯一索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票表';

-- 股票交易表
CREATE TABLE IF NOT EXISTS stock_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID',
    transaction_code VARCHAR(20) NOT NULL COMMENT '交易编号',
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    market VARCHAR(10) NOT NULL COMMENT '市场',
    transaction_type VARCHAR(10) NOT NULL COMMENT '交易类型(buy/sell)',
    transaction_date DATETIME NOT NULL COMMENT '交易日期',
    total_amount FLOAT COMMENT '交易总额',
    total_quantity INT COMMENT '交易数量',
    exchange_rate FLOAT COMMENT '汇率',
    broker_fee FLOAT COMMENT '经纪佣金',
    stamp_duty FLOAT COMMENT '印花税',
    transaction_levy FLOAT COMMENT '交易征费',
    trading_fee FLOAT COMMENT '交易费',
    clearing_fee FLOAT COMMENT '结算费',
    deposit_fee FLOAT COMMENT '存入证券费',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_stock (user_id, stock_code, market) COMMENT '用户股票索引',
    INDEX idx_transaction_date (transaction_date) COMMENT '交易日期索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票交易表';

-- 交易明细表
CREATE TABLE IF NOT EXISTS stock_transaction_details (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transaction_id INT NOT NULL COMMENT '交易ID',
    quantity INT NOT NULL COMMENT '数量',
    price FLOAT NOT NULL COMMENT '价格',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (transaction_id) REFERENCES stock_transactions(id) ON DELETE CASCADE,
    INDEX idx_transaction (transaction_id) COMMENT '交易ID索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='交易明细表';

-- 汇率表
CREATE TABLE IF NOT EXISTS exchange_rates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    currency VARCHAR(10) NOT NULL COMMENT '货币代码',
    rate_date DATE NOT NULL COMMENT '汇率日期',
    rate FLOAT NOT NULL COMMENT '汇率',
    source VARCHAR(20) NOT NULL COMMENT '数据来源',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_currency_date (currency, rate_date) COMMENT '货币和日期唯一索引'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='汇率表';

-- 添加注释
ALTER TABLE users COMMENT '用户管理表';
ALTER TABLE stocks COMMENT '股票基础信息表';
ALTER TABLE stock_transactions COMMENT '股票交易记录表';
ALTER TABLE stock_transaction_details COMMENT '交易明细表';
ALTER TABLE exchange_rates COMMENT '汇率记录表'; 