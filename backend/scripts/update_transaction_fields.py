#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
更新交易记录字段脚本

该脚本用于在交易记录的增加、修改、删除和分单操作后更新相关字段的计算，
特别是移动加权平均价格。

使用方法：
    python update_transaction_fields.py  # 处理所有记录
    python update_transaction_fields.py --holder_id=1  # 只处理指定持有人的记录
    python update_transaction_fields.py --stock_code=00700 --market=HK  # 只处理指定股票的记录
    python update_transaction_fields.py --transaction_id=123  # 只处理指定交易ID及其后续交易
    python update_transaction_fields.py --date=2023-01-01  # 只处理指定日期之后的记录
    python update_transaction_fields.py --update_original  # 同时更新原始交易记录
"""

import sys
import os
import logging
from datetime import datetime
import argparse

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.transaction_recalculator import recalculate_transaction_splits, ensure_log_directory

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'logs/update_transaction_fields_{datetime.now().strftime("%Y%m%d")}.log')
    ]
)

logger = logging.getLogger(__name__)

def main():
    """主函数"""
    try:
        # 解析命令行参数
        parser = argparse.ArgumentParser(description='更新交易记录字段')
        parser.add_argument('--transaction_id', type=int, help='指定交易ID，将处理该交易及其后续交易')
        parser.add_argument('--holder_id', type=int, help='指定持有人ID，不指定则处理所有记录')
        parser.add_argument('--stock_code', type=str, help='指定股票代码，需要同时指定市场')
        parser.add_argument('--market', type=str, help='指定股票市场，需要同时指定股票代码')
        parser.add_argument('--date', type=str, help='指定开始日期，格式为YYYY-MM-DD，只处理该日期及之后的记录')
        parser.add_argument('--update_original', action='store_true', help='是否同时更新原始交易记录')
        args = parser.parse_args()
        
        ensure_log_directory()
        logger.info("开始更新交易记录字段")
        
        # 验证参数
        if args.stock_code and not args.market:
            logger.error("指定股票代码时必须同时指定市场")
            return
        
        if args.market and not args.stock_code:
            logger.error("指定市场时必须同时指定股票代码")
            return
        
        # 解析日期参数
        start_date = None
        if args.date:
            try:
                start_date = datetime.strptime(args.date, '%Y-%m-%d').date()
                logger.info(f"只处理 {start_date} 及之后的记录")
            except ValueError:
                logger.error(f"日期格式错误: {args.date}，应为YYYY-MM-DD格式")
                return
        
        # 记录筛选条件
        if args.transaction_id:
            logger.info(f"只处理交易ID为 {args.transaction_id} 及其后续交易")
        
        if args.holder_id:
            logger.info(f"只处理持有人ID为 {args.holder_id} 的记录")
        
        if args.stock_code and args.market:
            logger.info(f"只处理股票代码为 {args.market}-{args.stock_code} 的记录")
        
        # 更新交易记录字段
        total, success, fail = recalculate_transaction_splits(
            holder_id=args.holder_id,
            stock_code=args.stock_code,
            market=args.market,
            start_date=start_date,
            transaction_id=args.transaction_id,
            update_original=args.update_original
        )
        
        logger.info(f"更新交易记录字段完成: 总计 {total} 条, 成功 {success} 条, 失败 {fail} 条")
    except Exception as e:
        logger.error(f"执行过程中发生错误: {str(e)}")

if __name__ == "__main__":
    main() 