-- 创建数据库
CREATE DATABASE IF NOT EXISTS stock DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE stock;

-- 修改数据库字符集
ALTER DATABASE stock CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 修改表字符集
ALTER TABLE users CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE stocks CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE stock_transactions CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE stock_transaction_details CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE exchange_rates CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE transaction_splits CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE permissions_backup CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT NOT NULL AUTO_INCREMENT COMMENT '用户ID',
    username VARCHAR(80) NOT NULL COMMENT '用户名',
    display_name VARCHAR(100) DEFAULT NULL COMMENT '显示名称',
    email VARCHAR(100) DEFAULT NULL COMMENT '电子邮箱（不使用）',
    avatar VARCHAR(255) DEFAULT NULL COMMENT '头像',
    password_hash VARCHAR(255) DEFAULT NULL COMMENT '密码哈希值',
    phone VARCHAR(20) DEFAULT NULL COMMENT '手机号码',
    status TINYINT(1) DEFAULT 1 COMMENT '状态：0-禁用，1-启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否激活',
    last_login DATETIME DEFAULT NULL COMMENT '最后登录时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY username (username),
    INDEX idx_email (email),
    INDEX idx_phone (phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户管理表';

-- 角色表
CREATE TABLE IF NOT EXISTS roles (
    id INT NOT NULL AUTO_INCREMENT COMMENT '角色ID',
    name VARCHAR(50) NOT NULL COMMENT '角色名称',
    code VARCHAR(50) NOT NULL COMMENT '角色标识',
    description TEXT COMMENT '角色描述',
    status TINYINT(1) DEFAULT 1 COMMENT '状态：0-禁用，1-启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_name (name),
    UNIQUE KEY uk_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色管理表';

-- 权限表
CREATE TABLE IF NOT EXISTS permissions (
    id INT NOT NULL AUTO_INCREMENT COMMENT '权限ID',
    name VARCHAR(100) NOT NULL COMMENT '权限名称',
    code VARCHAR(100) NOT NULL COMMENT '权限标识',
    description TEXT COMMENT '权限描述',
    type TINYINT(1) DEFAULT 3 COMMENT '权限类型：1-模块，2-菜单，3-按钮，4-数据，5-接口',
    parent_id INT DEFAULT NULL COMMENT '父级权限ID',
    path VARCHAR(255) COMMENT '权限路径',
    level INT DEFAULT 0 COMMENT '权限层级',
    sort_order INT DEFAULT 0 COMMENT '排序号',
    is_menu TINYINT(1) DEFAULT 0 COMMENT '是否菜单：0-否，1-是',
    icon VARCHAR(50) COMMENT '图标',
    component VARCHAR(255) COMMENT '前端组件',
    route_path VARCHAR(255) COMMENT '路由路径',
    status TINYINT(1) DEFAULT 1 COMMENT '状态：0-禁用，1-启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_code (code),
    INDEX idx_parent_id (parent_id),
    INDEX idx_path (path),
    INDEX idx_type (type),
    CONSTRAINT fk_permission_parent FOREIGN KEY (parent_id) REFERENCES permissions (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='权限管理表';

-- 权限备份表
CREATE TABLE IF NOT EXISTS permissions_backup (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(100) NOT NULL,
    description TEXT,
    type TINYINT(1) DEFAULT 3 COMMENT '权限类型：1-模块，2-菜单，3-按钮，4-数据，5-接口',
    parent_id INT DEFAULT NULL,
    path VARCHAR(255) DEFAULT NULL,
    level INT NOT NULL DEFAULT 0,
    sort_order INT NOT NULL DEFAULT 0,
    is_menu TINYINT(1) NOT NULL DEFAULT 0,
    icon VARCHAR(50) DEFAULT NULL,
    component VARCHAR(255) DEFAULT NULL,
    route_path VARCHAR(255) DEFAULT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY code (code),
    KEY idx_permissions_parent_id (parent_id),
    KEY idx_permissions_path (path),
    KEY idx_permissions_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户角色关联表
CREATE TABLE IF NOT EXISTS user_roles (
    id INT NOT NULL AUTO_INCREMENT COMMENT '关联ID',
    user_id INT NOT NULL COMMENT '用户ID',
    role_id INT NOT NULL COMMENT '角色ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_user_role (user_id, role_id),
    INDEX idx_user_id (user_id),
    INDEX idx_role_id (role_id),
    CONSTRAINT fk_ur_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_ur_role_id FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户角色关联表';

-- 角色权限关联表
CREATE TABLE IF NOT EXISTS role_permissions (
    id INT NOT NULL AUTO_INCREMENT COMMENT '关联ID',
    role_id INT NOT NULL COMMENT '角色ID',
    permission_id INT NOT NULL COMMENT '权限ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_role_permission (role_id, permission_id),
    INDEX idx_role_id (role_id),
    INDEX idx_permission_id (permission_id),
    CONSTRAINT fk_rp_role_id FOREIGN KEY (role_id) REFERENCES roles (id) ON DELETE CASCADE,
    CONSTRAINT fk_rp_permission_id FOREIGN KEY (permission_id) REFERENCES permissions (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色权限关联表';

-- 股票表
CREATE TABLE IF NOT EXISTS stocks (
    id INT NOT NULL AUTO_INCREMENT COMMENT '股票ID',
    code VARCHAR(20) NOT NULL COMMENT '股票代码',
    market VARCHAR(10) NOT NULL COMMENT '市场',
    code_name VARCHAR(100) NOT NULL COMMENT '股票名称',
    google_name VARCHAR(200) DEFAULT NULL COMMENT '谷歌股票名称',
    industry VARCHAR(50) DEFAULT NULL COMMENT '行业',
    sector VARCHAR(50) DEFAULT NULL COMMENT '板块',
    status TINYINT(1) DEFAULT 1 COMMENT '状态：0-禁用，1-启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY uix_code_market (code, market),
    INDEX idx_market (market),
    INDEX idx_industry (industry),
    INDEX idx_sector (sector)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票基础信息表';

-- 股票交易表
CREATE TABLE IF NOT EXISTS stock_transactions (
    id INT NOT NULL AUTO_INCREMENT COMMENT '交易ID',
    user_id INT NOT NULL COMMENT '用户ID',
    transaction_code VARCHAR(20) NOT NULL COMMENT '交易代码',
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    market VARCHAR(10) NOT NULL COMMENT '市场',
    transaction_type VARCHAR(10) NOT NULL COMMENT '交易类型',
    transaction_date DATETIME NOT NULL COMMENT '交易日期',
    total_amount DECIMAL(20,5) DEFAULT NULL COMMENT '总金额',
    total_quantity INT DEFAULT NULL COMMENT '总数量',
    broker_fee DECIMAL(10,5) DEFAULT NULL COMMENT '佣金',
    stamp_duty DECIMAL(10,5) DEFAULT NULL COMMENT '印花税',
    transaction_levy DECIMAL(10,5) DEFAULT NULL COMMENT '交易征费',
    trading_fee DECIMAL(10,5) DEFAULT NULL COMMENT '交易费',
    deposit_fee DECIMAL(10,5) DEFAULT NULL COMMENT '存入证券费',
    prev_quantity INT DEFAULT NULL COMMENT '交易前持仓数量',
    prev_cost DECIMAL(20,5) DEFAULT NULL COMMENT '交易前总成本',
    prev_avg_cost DECIMAL(20,5) DEFAULT NULL COMMENT '交易前移动加权平均价',
    current_quantity INT DEFAULT NULL COMMENT '交易后持仓数量',
    current_cost DECIMAL(20,5) DEFAULT NULL COMMENT '交易后总成本',
    current_avg_cost DECIMAL(20,5) DEFAULT NULL COMMENT '交易后移动加权平均价',
    total_fees DECIMAL(20,5) DEFAULT NULL COMMENT '总费用',
    net_amount DECIMAL(20,5) DEFAULT NULL COMMENT '净金额',
    running_quantity INT DEFAULT NULL COMMENT '累计数量',
    running_cost DECIMAL(20,5) DEFAULT NULL COMMENT '累计成本',
    realized_profit DECIMAL(20,5) DEFAULT NULL COMMENT '已实现盈亏',
    profit_rate DECIMAL(10,5) DEFAULT NULL COMMENT '盈亏比率',
    realized_pnl DECIMAL(20,5) DEFAULT 0.00000 COMMENT '已实现盈亏',
    realized_pnl_ratio DECIMAL(10,5) DEFAULT 0.00000 COMMENT '盈亏比率（%）',
    currency VARCHAR(10) DEFAULT 'CNY' COMMENT '货币',
    remarks TEXT COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_transaction_code (transaction_code),
    INDEX idx_user_id (user_id),
    INDEX idx_stock_code (stock_code),
    INDEX idx_market (market),
    INDEX idx_transaction_date (transaction_date),
    INDEX idx_transaction_type (transaction_type),
    CONSTRAINT fk_st_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票交易记录表';

-- 交易明细表
CREATE TABLE IF NOT EXISTS stock_transaction_details (
    id INT NOT NULL AUTO_INCREMENT COMMENT '交易明细ID',
    transaction_id INT NOT NULL COMMENT '交易ID',
    quantity INT NOT NULL COMMENT '数量',
    price DECIMAL(20,5) NOT NULL COMMENT '价格',
    amount DECIMAL(20,5) NOT NULL COMMENT '金额',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    INDEX idx_transaction_id (transaction_id),
    CONSTRAINT fk_std_transaction_id FOREIGN KEY (transaction_id) REFERENCES stock_transactions (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='交易明细表';

-- 汇率表
CREATE TABLE IF NOT EXISTS exchange_rates (
    id INT NOT NULL AUTO_INCREMENT COMMENT '汇率ID',
    currency VARCHAR(10) NOT NULL COMMENT '货币',
    rate_date DATE NOT NULL COMMENT '汇率日期',
    rate DECIMAL(20,10) NOT NULL COMMENT '汇率',
    source VARCHAR(20) NOT NULL COMMENT '来源',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY uix_currency_date (currency, rate_date),
    INDEX idx_rate_date (rate_date),
    INDEX idx_currency (currency)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='汇率记录表';

-- 持有人表
CREATE TABLE IF NOT EXISTS holders (
    id INT NOT NULL AUTO_INCREMENT COMMENT '持有人ID',
    name VARCHAR(100) NOT NULL COMMENT '持有人姓名',
    type VARCHAR(20) DEFAULT 'individual' COMMENT '类型：individual-个人，institution-机构',
    user_id INT DEFAULT NULL COMMENT '关联的系统用户ID',
    status TINYINT(1) DEFAULT 1 COMMENT '状态：0-禁用，1-启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_name (name),
    INDEX idx_user_id (user_id),
    CONSTRAINT fk_holder_user_id FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='持有人表';

-- 交易分单表
CREATE TABLE IF NOT EXISTS transaction_splits (
    id INT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    original_transaction_id INT NOT NULL COMMENT '原始交易ID',
    holder_id INT DEFAULT NULL COMMENT '持有人ID',
    holder_name VARCHAR(100) DEFAULT NULL COMMENT '持有人名称',
    split_ratio DECIMAL(10,4) NOT NULL COMMENT '分摊比例',
    transaction_date DATE NOT NULL COMMENT '交易日期',
    stock_id INT DEFAULT NULL COMMENT '股票ID',
    stock_code VARCHAR(20) NOT NULL COMMENT '股票代码',
    stock_name VARCHAR(100) NOT NULL COMMENT '股票名称',
    market VARCHAR(20) NOT NULL COMMENT '市场',
    transaction_code VARCHAR(50) DEFAULT NULL COMMENT '交易编号',
    transaction_type VARCHAR(10) NOT NULL COMMENT '交易类型(买入/卖出)',
    total_amount FLOAT NOT NULL COMMENT '总金额',
    total_quantity INT NOT NULL COMMENT '总数量',
    broker_fee FLOAT DEFAULT NULL COMMENT '佣金',
    stamp_duty FLOAT DEFAULT NULL COMMENT '印花税',
    transaction_levy FLOAT DEFAULT NULL COMMENT '交易征费',
    trading_fee FLOAT DEFAULT NULL COMMENT '交易费',
    deposit_fee FLOAT DEFAULT NULL COMMENT '存入证券费',
    prev_quantity INT DEFAULT NULL COMMENT '交易前持仓数量',
    prev_cost DECIMAL(10,2) DEFAULT NULL COMMENT '交易前总成本',
    prev_avg_cost DECIMAL(10,2) DEFAULT NULL COMMENT '交易前移动加权平均价',
    current_quantity INT DEFAULT NULL COMMENT '交易后持仓数量',
    current_cost DECIMAL(10,2) DEFAULT NULL COMMENT '交易后总成本',
    current_avg_cost DECIMAL(10,2) DEFAULT NULL COMMENT '交易后移动加权平均价',
    total_fees DECIMAL(10,2) DEFAULT NULL COMMENT '总费用',
    net_amount DECIMAL(10,2) DEFAULT NULL COMMENT '净金额',
    running_quantity INT DEFAULT NULL COMMENT '累计数量',
    running_cost DECIMAL(10,2) DEFAULT NULL COMMENT '累计成本',
    realized_profit DECIMAL(10,2) DEFAULT NULL COMMENT '已实现盈亏',
    profit_rate DECIMAL(10,2) DEFAULT NULL COMMENT '盈亏比率',
    exchange_rate DECIMAL(10,4) DEFAULT '1.0000' COMMENT '汇率',
    remarks TEXT COMMENT '备注',
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    KEY idx_original_transaction (original_transaction_id),
    KEY idx_holder (holder_id),
    KEY idx_stock (stock_code, market),
    KEY idx_transaction_date (transaction_date),
    CONSTRAINT fk_ts_holder_id FOREIGN KEY (holder_id) REFERENCES holders (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='交易分单记录';

-- 插入默认角色
INSERT INTO roles (name, code, description) 
VALUES 
('超级管理员', 'admin', '系统超级管理员，拥有所有权限'),
('普通用户', 'user', '普通用户，拥有基本操作权限')
ON DUPLICATE KEY UPDATE name=name;

-- 插入基础权限
INSERT INTO permissions (name, code, description, type, parent_id, path, level, sort_order, is_menu, icon, component, route_path) 
VALUES 
-- 系统管理
('系统管理', 'system', '系统管理相关功能', 1, NULL, '1', 0, 1, 1, 'bi-gear', NULL, NULL),

-- 用户管理
('用户管理', 'system:user', '用户管理相关功能', 2, 1, '1/2', 1, 1, 1, 'bi-people', 'views/system/User.vue', '/system/user'),
('查看用户', 'system:user:view', '查看用户列表', 3, 2, '1/2/3', 2, 1, 0, NULL, NULL, NULL),
('添加用户', 'system:user:add', '添加新用户', 3, 2, '1/2/4', 2, 2, 0, NULL, NULL, NULL),
('编辑用户', 'system:user:edit', '编辑用户信息', 3, 2, '1/2/5', 2, 3, 0, NULL, NULL, NULL),
('删除用户', 'system:user:delete', '删除用户', 3, 2, '1/2/6', 2, 4, 0, NULL, NULL, NULL),
('分配角色', 'system:user:assign', '为用户分配角色', 3, 2, '1/2/7', 2, 5, 0, NULL, NULL, NULL),

-- 角色管理
('角色管理', 'system:role', '角色管理相关功能', 2, 1, '1/8', 1, 2, 1, 'bi-person-badge', 'views/system/Role.vue', '/system/role'),
('查看角色', 'system:role:view', '查看角色列表', 3, 8, '1/8/9', 2, 1, 0, NULL, NULL, NULL),
('添加角色', 'system:role:add', '添加新角色', 3, 8, '1/8/10', 2, 2, 0, NULL, NULL, NULL),
('编辑角色', 'system:role:edit', '编辑角色信息', 3, 8, '1/8/11', 2, 3, 0, NULL, NULL, NULL),
('删除角色', 'system:role:delete', '删除角色', 3, 8, '1/8/12', 2, 4, 0, NULL, NULL, NULL),
('分配权限', 'system:role:assign', '为角色分配权限', 3, 8, '1/8/13', 2, 5, 0, NULL, NULL, NULL),

-- 权限管理
('权限管理', 'system:permission', '权限管理相关功能', 2, 1, '1/14', 1, 3, 1, 'bi-shield-lock', 'views/system/Permission.vue', '/system/permission'),
('查看权限', 'system:permission:view', '查看权限列表', 3, 14, '1/14/15', 2, 1, 0, NULL, NULL, NULL),
('添加权限', 'system:permission:add', '添加新权限', 3, 14, '1/14/16', 2, 2, 0, NULL, NULL, NULL),
('编辑权限', 'system:permission:edit', '编辑权限信息', 3, 14, '1/14/17', 2, 3, 0, NULL, NULL, NULL),
('删除权限', 'system:permission:delete', '删除权限', 3, 14, '1/14/18', 2, 4, 0, NULL, NULL, NULL),

-- 持有人管理
('持有人管理', 'system:holder', '持有人管理相关功能', 2, 1, '1/19', 1, 4, 1, 'bi-person-vcard', 'views/system/Holder.vue', '/system/holder'),
('查看持有人', 'system:holder:view', '查看持有人列表', 3, 19, '1/19/20', 2, 1, 0, NULL, NULL, NULL),
('添加持有人', 'system:holder:add', '添加新持有人', 3, 19, '1/19/21', 2, 2, 0, NULL, NULL, NULL),
('编辑持有人', 'system:holder:edit', '编辑持有人信息', 3, 19, '1/19/22', 2, 3, 0, NULL, NULL, NULL),
('删除持有人', 'system:holder:delete', '删除持有人', 3, 19, '1/19/23', 2, 4, 0, NULL, NULL, NULL),

-- 系统配置
('系统配置', 'system:config', '系统配置相关功能', 2, 1, '1/24', 1, 5, 1, 'bi-sliders', 'views/system/Config.vue', '/system/config'),
('查看配置', 'system:config:view', '查看系统配置', 3, 24, '1/24/25', 2, 1, 0, NULL, NULL, NULL),
('修改配置', 'system:config:edit', '修改系统配置', 3, 24, '1/24/26', 2, 2, 0, NULL, NULL, NULL),

-- 日志管理
('日志管理', 'system:log', '日志管理相关功能', 2, 1, '1/27', 1, 6, 1, 'bi-journal-text', 'views/system/Log.vue', '/system/log'),
('查看日志', 'system:log:view', '查看操作日志', 3, 27, '1/27/28', 2, 1, 0, NULL, NULL, NULL),
('导出日志', 'system:log:export', '导出操作日志', 3, 27, '1/27/29', 2, 2, 0, NULL, NULL, NULL),

-- 交易分单
('交易分单', 'transaction:split', '交易分单相关功能', 2, NULL, '2', 1, 3, 1, 'bi-diagram-3', 'views/TransactionSplit.vue', '/transaction/split'),
('查看分单', 'transaction:split:view', '查看交易分单', 3, (SELECT id FROM (SELECT id FROM permissions WHERE code = 'transaction:split') AS p), '2/p.id/1', 2, 1, 0, NULL, NULL, NULL),
('创建分单', 'transaction:split:add', '创建交易分单', 3, (SELECT id FROM (SELECT id FROM permissions WHERE code = 'transaction:split') AS p), '2/p.id/2', 2, 2, 0, NULL, NULL, NULL),
('编辑分单', 'transaction:split:edit', '编辑交易分单', 3, (SELECT id FROM (SELECT id FROM permissions WHERE code = 'transaction:split') AS p), '2/p.id/3', 2, 3, 0, NULL, NULL, NULL),
('删除分单', 'transaction:split:delete', '删除交易分单', 3, (SELECT id FROM (SELECT id FROM permissions WHERE code = 'transaction:split') AS p), '2/p.id/4', 2, 4, 0, NULL, NULL, NULL)

ON DUPLICATE KEY UPDATE name=name;

-- 为超级管理员角色分配所有权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM roles WHERE code = 'admin'),
    id
FROM 
    permissions
ON DUPLICATE KEY UPDATE role_id=role_id;

-- 为普通用户角色分配基本权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM roles WHERE code = 'user'),
    id
FROM 
    permissions
WHERE 
    code IN (
        'system:user:view',
        'system:role:view',
        'system:permission:view',
        'system:holder:view',
        'stock:list:view',
        'stock:holdings:view',
        'transaction:records:view',
        'transaction:records:add',
        'transaction:stats:view',
        'transaction:split:view',
        'transaction:split:add',
        'profit:overview:view',
        'profit:details:view',
        'exchange:rates:view',
        'exchange:converter:use'
    )
ON DUPLICATE KEY UPDATE role_id=role_id; 