"""
创建RBAC相关数据库表的脚本
"""
import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).resolve().parent
root_dir = current_dir.parent
sys.path.append(str(root_dir))

from config.database import db
from config.logging import setup_logging

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)

def create_rbac_tables():
    """创建RBAC相关的数据库表"""
    try:
        # 确保数据库连接已初始化
        # 注意：这里不需要调用init_db，因为db实例已经在导入时创建
        
        # 创建角色表
        create_roles_table = """
        CREATE TABLE IF NOT EXISTS stock.roles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50) NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        # 创建权限表
        create_permissions_table = """
        CREATE TABLE IF NOT EXISTS stock.permissions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            code VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            parent_id INT,
            path VARCHAR(255),
            level INT NOT NULL DEFAULT 0,
            sort_order INT NOT NULL DEFAULT 0,
            is_menu BOOLEAN NOT NULL DEFAULT FALSE,
            icon VARCHAR(50),
            component VARCHAR(255),
            route_path VARCHAR(255),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES stock.permissions(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        # 创建用户角色关联表
        create_user_roles_table = """
        CREATE TABLE IF NOT EXISTS stock.user_roles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            role_id INT NOT NULL,
            UNIQUE(user_id, role_id),
            FOREIGN KEY (user_id) REFERENCES stock.users(id) ON DELETE CASCADE,
            FOREIGN KEY (role_id) REFERENCES stock.roles(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        # 创建角色权限关联表
        create_role_permissions_table = """
        CREATE TABLE IF NOT EXISTS stock.role_permissions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            role_id INT NOT NULL,
            permission_id INT NOT NULL,
            UNIQUE(role_id, permission_id),
            FOREIGN KEY (role_id) REFERENCES stock.roles(id) ON DELETE CASCADE,
            FOREIGN KEY (permission_id) REFERENCES stock.permissions(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        # 创建索引 - 使用MySQL支持的语法
        create_indexes = [
            # 检查索引是否存在，如果不存在则创建
            """
            SELECT COUNT(1) IndexIsThere FROM INFORMATION_SCHEMA.STATISTICS
            WHERE table_schema=DATABASE() AND table_name='permissions' AND index_name='idx_permissions_parent_id';
            """,
            """
            CREATE INDEX idx_permissions_parent_id ON stock.permissions(parent_id);
            """,
            
            """
            SELECT COUNT(1) IndexIsThere FROM INFORMATION_SCHEMA.STATISTICS
            WHERE table_schema=DATABASE() AND table_name='permissions' AND index_name='idx_permissions_path';
            """,
            """
            CREATE INDEX idx_permissions_path ON stock.permissions(path);
            """,
            
            """
            SELECT COUNT(1) IndexIsThere FROM INFORMATION_SCHEMA.STATISTICS
            WHERE table_schema=DATABASE() AND table_name='permissions' AND index_name='idx_permissions_code';
            """,
            """
            CREATE INDEX idx_permissions_code ON stock.permissions(code);
            """,
            
            """
            SELECT COUNT(1) IndexIsThere FROM INFORMATION_SCHEMA.STATISTICS
            WHERE table_schema=DATABASE() AND table_name='user_roles' AND index_name='idx_user_roles_user_id';
            """,
            """
            CREATE INDEX idx_user_roles_user_id ON stock.user_roles(user_id);
            """,
            
            """
            SELECT COUNT(1) IndexIsThere FROM INFORMATION_SCHEMA.STATISTICS
            WHERE table_schema=DATABASE() AND table_name='user_roles' AND index_name='idx_user_roles_role_id';
            """,
            """
            CREATE INDEX idx_user_roles_role_id ON stock.user_roles(role_id);
            """,
            
            """
            SELECT COUNT(1) IndexIsThere FROM INFORMATION_SCHEMA.STATISTICS
            WHERE table_schema=DATABASE() AND table_name='role_permissions' AND index_name='idx_role_permissions_role_id';
            """,
            """
            CREATE INDEX idx_role_permissions_role_id ON stock.role_permissions(role_id);
            """,
            
            """
            SELECT COUNT(1) IndexIsThere FROM INFORMATION_SCHEMA.STATISTICS
            WHERE table_schema=DATABASE() AND table_name='role_permissions' AND index_name='idx_role_permissions_permission_id';
            """,
            """
            CREATE INDEX idx_role_permissions_permission_id ON stock.role_permissions(permission_id);
            """
        ]
        
        # 插入默认角色
        insert_default_roles = """
        INSERT INTO stock.roles (name, description) 
        VALUES 
        ('超级管理员', '系统超级管理员，拥有所有权限'),
        ('普通用户', '普通用户，拥有基本操作权限')
        ON DUPLICATE KEY UPDATE name=name;
        """
        
        # 插入基础权限
        insert_default_permissions = """
        INSERT INTO stock.permissions (name, code, description, parent_id, path, level, sort_order, is_menu, icon, component, route_path) 
        VALUES 
        -- 系统管理
        ('系统管理', 'system', '系统管理相关功能', NULL, '1', 0, 1, TRUE, 'bi-gear', NULL, NULL),

        -- 用户管理
        ('用户管理', 'system:user', '用户管理相关功能', 1, '1/2', 1, 1, TRUE, 'bi-people', 'views/system/User.vue', '/system/user'),
        ('查看用户', 'system:user:view', '查看用户列表', 2, '1/2/3', 2, 1, FALSE, NULL, NULL, NULL),
        ('添加用户', 'system:user:add', '添加新用户', 2, '1/2/4', 2, 2, FALSE, NULL, NULL, NULL),
        ('编辑用户', 'system:user:edit', '编辑用户信息', 2, '1/2/5', 2, 3, FALSE, NULL, NULL, NULL),
        ('删除用户', 'system:user:delete', '删除用户', 2, '1/2/6', 2, 4, FALSE, NULL, NULL, NULL),
        ('分配角色', 'system:user:assign', '为用户分配角色', 2, '1/2/7', 2, 5, FALSE, NULL, NULL, NULL),

        -- 角色管理
        ('角色管理', 'system:role', '角色管理相关功能', 1, '1/8', 1, 2, TRUE, 'bi-person-badge', 'views/system/Role.vue', '/system/role'),
        ('查看角色', 'system:role:view', '查看角色列表', 8, '1/8/9', 2, 1, FALSE, NULL, NULL, NULL),
        ('添加角色', 'system:role:add', '添加新角色', 8, '1/8/10', 2, 2, FALSE, NULL, NULL, NULL),
        ('编辑角色', 'system:role:edit', '编辑角色信息', 8, '1/8/11', 2, 3, FALSE, NULL, NULL, NULL),
        ('删除角色', 'system:role:delete', '删除角色', 8, '1/8/12', 2, 4, FALSE, NULL, NULL, NULL),
        ('分配权限', 'system:role:assign', '为角色分配权限', 8, '1/8/13', 2, 5, FALSE, NULL, NULL, NULL),

        -- 权限管理
        ('权限管理', 'system:permission', '权限管理相关功能', 1, '1/14', 1, 3, TRUE, 'bi-shield-lock', 'views/system/Permission.vue', '/system/permission'),
        ('查看权限', 'system:permission:view', '查看权限列表', 14, '1/14/15', 2, 1, FALSE, NULL, NULL, NULL),
        ('添加权限', 'system:permission:add', '添加新权限', 14, '1/14/16', 2, 2, FALSE, NULL, NULL, NULL),
        ('编辑权限', 'system:permission:edit', '编辑权限信息', 14, '1/14/17', 2, 3, FALSE, NULL, NULL, NULL),
        ('删除权限', 'system:permission:delete', '删除权限', 14, '1/14/18', 2, 4, FALSE, NULL, NULL, NULL)
        ON DUPLICATE KEY UPDATE code=code;
        """
        
        # 为超级管理员角色分配所有权限
        assign_admin_permissions = """
        INSERT INTO stock.role_permissions (role_id, permission_id)
        SELECT 
            (SELECT id FROM stock.roles WHERE name = '超级管理员'),
            id
        FROM 
            stock.permissions
        ON DUPLICATE KEY UPDATE role_id=role_id;
        """
        
        # 为普通用户角色分配基本权限
        assign_user_permissions = """
        INSERT INTO stock.role_permissions (role_id, permission_id)
        SELECT 
            (SELECT id FROM stock.roles WHERE name = '普通用户'),
            id
        FROM 
            stock.permissions
        WHERE 
            code IN ('system:user:view')
        ON DUPLICATE KEY UPDATE role_id=role_id;
        """
        
        # 执行SQL语句
        logger.info("开始创建RBAC表...")
        
        # 创建表
        db.execute(create_roles_table)
        logger.info("角色表创建成功")
        
        db.execute(create_permissions_table)
        logger.info("权限表创建成功")
        
        db.execute(create_user_roles_table)
        logger.info("用户角色关联表创建成功")
        
        db.execute(create_role_permissions_table)
        logger.info("角色权限关联表创建成功")
        
        # 创建索引
        logger.info("开始创建索引...")
        for i in range(0, len(create_indexes), 2):
            # 检查索引是否存在
            check_sql = create_indexes[i]
            result = db.fetch_one(check_sql)
            
            # 如果索引不存在，则创建
            if result and result.get('IndexIsThere', 0) == 0:
                create_sql = create_indexes[i+1]
                db.execute(create_sql)
                logger.info(f"创建索引: {create_sql.strip()}")
        logger.info("索引创建成功")
        
        # 插入默认数据
        db.execute(insert_default_roles)
        logger.info("默认角色插入成功")
        
        db.execute(insert_default_permissions)
        logger.info("默认权限插入成功")
        
        db.execute(assign_admin_permissions)
        logger.info("超级管理员权限分配成功")
        
        db.execute(assign_user_permissions)
        logger.info("普通用户权限分配成功")
        
        logger.info("RBAC表创建完成")
        return True
    except Exception as e:
        logger.error(f"创建RBAC表失败: {str(e)}")
        return False

if __name__ == "__main__":
    success = create_rbac_tables()
    if success:
        print("RBAC表创建成功")
    else:
        print("RBAC表创建失败，请查看日志")
        sys.exit(1) 