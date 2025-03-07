#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
交易分单表创建迁移脚本
"""

import pymysql
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def create_transaction_splits_table(connection):
    """
    创建交易分单表
    """
    cursor = connection.cursor()
    
    try:
        # 检查表是否已存在
        cursor.execute("SHOW TABLES LIKE 'transaction_splits'")
        if cursor.fetchone():
            logger.info("transaction_splits 表已存在，跳过创建")
            return
        
        # 创建交易分单表
        create_table_sql = """
        CREATE TABLE `transaction_splits` (
            `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
            `original_transaction_id` INT NOT NULL COMMENT '原始交易ID',
            `holder_id` INT DEFAULT NULL COMMENT '持有人ID',
            `holder_name` VARCHAR(100) DEFAULT NULL COMMENT '持有人名称',
            `split_ratio` DECIMAL(10,4) NOT NULL COMMENT '分摊比例',
            `transaction_date` DATE NOT NULL COMMENT '交易日期',
            `stock_id` INT DEFAULT NULL COMMENT '股票ID',
            `stock_code` VARCHAR(20) NOT NULL COMMENT '股票代码',
            `stock_name` VARCHAR(100) DEFAULT NULL COMMENT '股票名称',
            `market` VARCHAR(20) NOT NULL COMMENT '市场',
            `transaction_code` VARCHAR(50) DEFAULT NULL COMMENT '交易编号',
            `transaction_type` VARCHAR(10) NOT NULL COMMENT '交易类型(买入/卖出)',
            `total_amount` FLOAT NOT NULL COMMENT '总金额',
            `total_quantity` INT NOT NULL COMMENT '总数量',
            `broker_fee` FLOAT DEFAULT NULL COMMENT '佣金',
            `stamp_duty` FLOAT DEFAULT NULL COMMENT '印花税',
            `transaction_levy` FLOAT DEFAULT NULL COMMENT '交易征费',
            `trading_fee` FLOAT DEFAULT NULL COMMENT '交易费',
            `deposit_fee` FLOAT DEFAULT NULL COMMENT '存入证券费',
            `prev_quantity` INT DEFAULT NULL COMMENT '交易前持仓数量',
            `prev_cost` DECIMAL(10,2) DEFAULT NULL COMMENT '交易前总成本',
            `prev_avg_cost` DECIMAL(10,2) DEFAULT NULL COMMENT '交易前移动加权平均价',
            `current_quantity` INT DEFAULT NULL COMMENT '交易后持仓数量',
            `current_cost` DECIMAL(10,2) DEFAULT NULL COMMENT '交易后总成本',
            `current_avg_cost` DECIMAL(10,2) DEFAULT NULL COMMENT '交易后移动加权平均价',
            `total_fees` DECIMAL(10,2) DEFAULT NULL COMMENT '总费用',
            `net_amount` DECIMAL(10,2) DEFAULT NULL COMMENT '净金额',
            `running_quantity` INT DEFAULT NULL COMMENT '累计数量',
            `running_cost` DECIMAL(10,2) DEFAULT NULL COMMENT '累计成本',
            `realized_profit` DECIMAL(10,2) DEFAULT NULL COMMENT '已实现盈亏',
            `profit_rate` DECIMAL(10,2) DEFAULT NULL COMMENT '盈亏比率',
            `exchange_rate` DECIMAL(10,4) DEFAULT 1.0 COMMENT '汇率',
            `remarks` TEXT DEFAULT NULL COMMENT '备注',
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            PRIMARY KEY (`id`),
            INDEX `idx_original_transaction` (`original_transaction_id`),
            INDEX `idx_holder` (`holder_id`),
            INDEX `idx_stock` (`stock_code`, `market`),
            INDEX `idx_transaction_date` (`transaction_date`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='交易分单记录';
        """
        
        cursor.execute(create_table_sql)
        logger.info("成功创建 transaction_splits 表")
        
    except Exception as e:
        logger.error(f"创建 transaction_splits 表时出错: {e}")
        raise
    finally:
        cursor.close()

def main():
    """
    主函数
    """
    # 数据库连接配置
    db_config = {
        'host': '172.16.0.109',
        'port': 3306,
        'user': 'root',
        'password': 'Zxc000123',
        'database': 'stock',
        'charset': 'utf8mb4'
    }
    
    # 建立数据库连接
    try:
        connection = pymysql.connect(**db_config)
        logger.info("数据库连接成功")
        
        # 创建交易分单表
        create_transaction_splits_table(connection)
        
        # 提交事务
        connection.commit()
        logger.info("迁移成功完成")
        
    except Exception as e:
        logger.error(f"迁移失败: {e}")
        if 'connection' in locals():
            connection.rollback()
    finally:
        if 'connection' in locals():
            connection.close()
            logger.info("数据库连接已关闭")

if __name__ == "__main__":
    main() 