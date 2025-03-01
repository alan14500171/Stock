import mysql.connector
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    'host': '172.16.0.109',
    'user': 'root',
    'password': 'Zxc000123',
    'database': 'stock'
}

def get_db_connection():
    """创建数据库连接"""
    return mysql.connector.connect(**DB_CONFIG)

def get_all_stock_positions():
    """获取所有股票持仓"""
    sql = """
    SELECT DISTINCT user_id, stock_code, market
    FROM stock_transactions
    WHERE transaction_type IN ('buy', 'sell')
    ORDER BY user_id, market, stock_code
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql)
    positions = cursor.fetchall()
    cursor.close()
    conn.close()
    return positions

def calculate_avg_cost(user_id, stock_code, market):
    """计算单个股票的移动加权平均价"""
    logger.info(f"处理股票: {market}:{stock_code} (用户ID: {user_id})")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 获取该股票的所有交易记录
        sql = """
        SELECT id, transaction_type, transaction_date, total_quantity, total_amount,
               broker_fee, transaction_levy, stamp_duty, trading_fee, clearing_fee, deposit_fee
        FROM stock_transactions
        WHERE user_id = %s AND stock_code = %s AND market = %s
              AND transaction_type IN ('buy', 'sell')
        ORDER BY transaction_date, id
        """
        cursor.execute(sql, (user_id, stock_code, market))
        transactions = cursor.fetchall()
        
        # 初始化变量
        current_quantity = 0
        current_cost = 0
        current_avg_cost = 0
        
        # 遍历每笔交易
        for transaction in transactions:
            (id, trans_type, trans_date, quantity, amount, 
             broker_fee, levy, stamp, trading, clearing, deposit) = transaction
            
            # 计算总费用
            total_fees = sum(fee or 0 for fee in [broker_fee, levy, stamp, trading, clearing, deposit])
            
            # 保存交易前的状态
            prev_quantity = current_quantity
            prev_cost = current_cost
            prev_avg_cost = current_avg_cost if current_quantity > 0 else 0
            
            # 更新持仓状态
            if trans_type.lower() == 'buy':
                # 买入
                current_quantity += quantity
                current_cost += amount + total_fees
                if current_quantity > 0:
                    current_avg_cost = current_cost / current_quantity
            else:
                # 卖出
                if current_quantity >= quantity:
                    # 计算剩余成本
                    remain_ratio = (current_quantity - quantity) / current_quantity
                    current_cost = current_cost * remain_ratio
                    current_quantity -= quantity
                    if current_quantity > 0:
                        current_avg_cost = current_cost / current_quantity
                    else:
                        current_avg_cost = 0
                else:
                    logger.warning(f"警告：卖出数量({quantity})大于持仓数量({current_quantity})")
                    current_quantity = 0
                    current_cost = 0
                    current_avg_cost = 0
            
            # 更新数据库
            update_sql = """
            UPDATE stock_transactions
            SET prev_quantity = %s,
                prev_cost = %s,
                prev_avg_cost = %s,
                current_quantity = %s,
                current_cost = %s,
                current_avg_cost = %s
            WHERE id = %s
            """
            cursor.execute(update_sql, (
                prev_quantity,
                prev_cost,
                prev_avg_cost,
                current_quantity,
                current_cost,
                current_avg_cost,
                id
            ))
        
        # 提交事务
        conn.commit()
        logger.info(f"成功更新股票 {market}:{stock_code} 的移动加权平均价")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"处理股票 {market}:{stock_code} 时出错: {str(e)}")
        raise
    
    finally:
        cursor.close()
        conn.close()

def main():
    """主函数"""
    start_time = datetime.now()
    logger.info("开始更新移动加权平均价...")
    
    try:
        # 获取所有股票持仓
        positions = get_all_stock_positions()
        total = len(positions)
        logger.info(f"共找到 {total} 个股票持仓需要处理")
        
        # 遍历处理每个股票
        for i, position in enumerate(positions, 1):
            logger.info(f"进度: {i}/{total}")
            calculate_avg_cost(
                position['user_id'],
                position['stock_code'],
                position['market']
            )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"全部处理完成！耗时: {duration:.2f} 秒")
        
    except Exception as e:
        logger.error(f"处理过程中出错: {str(e)}")
        raise

if __name__ == '__main__':
    main() 