#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import logging

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db
import logging

logger = logging.getLogger(__name__)

def setup_logging():
    """设置日志配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def update_table_schema():
    """更新数据库表结构"""
    try:
        # 开始事务
        db.execute("START TRANSACTION")
        
        # 添加新字段
        alter_table_sql = """
            ALTER TABLE stock.stock_transactions
            ADD COLUMN IF NOT EXISTS realized_profit DECIMAL(20,5) DEFAULT 0.00000 COMMENT '已实现盈亏',
            ADD COLUMN IF NOT EXISTS profit_rate DECIMAL(10,5) DEFAULT 0.00000 COMMENT '盈亏比率（%）'
        """
        db.execute(alter_table_sql)
        
        # 更新现有记录的默认值
        update_records_sql = """
            UPDATE stock.stock_transactions
            SET realized_profit = 0.00000,
                profit_rate = 0.00000
            WHERE realized_profit IS NULL
               OR profit_rate IS NULL
        """
        db.execute(update_records_sql)
        
        # 提交事务
        db.execute("COMMIT")
        logger.info("数据库表结构更新成功")
        return True
        
    except Exception as e:
        db.execute("ROLLBACK")
        logger.error(f"更新数据库表结构失败: {str(e)}")
        return False

def main():
    """主函数"""
    setup_logging()
    logger.info("开始更新数据库表结构...")
    
    if update_table_schema():
        logger.info("数据库表结构更新完成")
    else:
        logger.error("数据库表结构更新失败")

if __name__ == '__main__':
    main() 