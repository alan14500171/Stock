from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import logging
from typing import Dict, List, Tuple, Optional, Any
from utils.db import get_db_connection

logger = logging.getLogger(__name__)

class TransactionCalculator:
    @staticmethod
    def calculate_fees(transaction):
        """计算交易的总费用"""
        fees = [
            'broker_fee', 'transaction_levy', 'stamp_duty',
            'trading_fee', 'deposit_fee'
        ]
        return sum(Decimal(str(transaction.get(fee) or 0)) for fee in fees)

    @staticmethod
    def calculate_net_amount(transaction, total_fees):
        """计算交易的净金额"""
        total_amount = Decimal(str(transaction['total_amount']))
        if transaction['transaction_type'].lower() == 'buy':
            return total_amount + total_fees
        else:
            return total_amount - total_fees

    @staticmethod
    def calculate_position_change(transaction, prev_state):
        """计算持仓变化"""
        total_quantity = Decimal(str(transaction['total_quantity']))
        total_amount = Decimal(str(transaction['total_amount']))
        total_fees = TransactionCalculator.calculate_fees(transaction)
        
        # 获取之前的状态
        prev_quantity = Decimal(str(prev_state.get('quantity', 0)))
        prev_cost = Decimal(str(prev_state.get('cost', 0)))
        prev_avg_cost = Decimal(str(prev_state.get('avg_cost', 0)))
        
        # 初始化结果
        result = {
            'prev_quantity': prev_quantity,
            'prev_cost': prev_cost,
            'prev_avg_cost': prev_avg_cost,
            'realized_profit': Decimal('0'),
            'profit_rate': Decimal('0'),
            'total_fees': total_fees,
            'net_amount': Decimal('0'),
            'avg_price': Decimal('0')
        }
        
        # 计算净金额
        result['net_amount'] = TransactionCalculator.calculate_net_amount(transaction, total_fees)
        
        # 计算平均价格（单价）
        if total_quantity > 0:
            result['avg_price'] = total_amount / total_quantity
        
        # 根据交易类型计算
        if transaction['transaction_type'].lower() == 'buy':
            # 买入
            result['current_quantity'] = prev_quantity + total_quantity
            result['current_cost'] = prev_cost + total_amount + total_fees
            result['current_avg_cost'] = (result['current_cost'] / result['current_quantity']
                                        if result['current_quantity'] > 0 else Decimal('0'))
        else:
            # 卖出
            if prev_quantity < total_quantity:
                raise ValueError(f'卖出数量({total_quantity})大于持仓数量({prev_quantity})')
            
            result['current_quantity'] = prev_quantity - total_quantity
            
            # 计算已实现盈亏
            if prev_avg_cost > 0:
                cost_basis = prev_avg_cost * total_quantity
                result['realized_profit'] = total_amount - cost_basis - total_fees
                result['profit_rate'] = (result['realized_profit'] / cost_basis * 100
                                              if cost_basis > 0 else Decimal('0'))
            
            # 更新成本
            result['current_cost'] = (prev_cost * (result['current_quantity'] / prev_quantity)
                                    if prev_quantity > 0 else Decimal('0'))
            result['current_avg_cost'] = (result['current_cost'] / result['current_quantity']
                                        if result['current_quantity'] > 0 else Decimal('0'))
        
        # 格式化数值
        for key in result:
            if isinstance(result[key], Decimal):
                result[key] = result[key].quantize(Decimal('0.00000'), rounding=ROUND_HALF_UP)
        
        return result

    @staticmethod
    def process_transaction(
        db_conn,
        transaction_data: Dict[str, Any],
        operation_type: str,
        holder_id: Optional[int] = None,
        original_transaction_id: Optional[int] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        统一处理交易记录的计算逻辑
        
        Args:
            db_conn: 数据库连接
            transaction_data: 交易数据
            operation_type: 操作类型 ('add', 'edit', 'delete', 'split')
            holder_id: 持有人ID（分单时使用）
            original_transaction_id: 原始交易ID（分单和编辑时使用）
            
        Returns:
            Tuple[bool, Dict]: (是否成功, 结果数据)
        """
        try:
            # 验证交易数据（除删除操作外）
            if operation_type != 'delete':
                errors = TransactionCalculator.validate_transaction(transaction_data)
                if errors:
                    return False, {'message': '数据验证失败', 'errors': errors}

            # 获取交易前的持仓状态
            prev_state = TransactionCalculator._get_previous_holding_state(
                db_conn,
                holder_id if holder_id else transaction_data.get('user_id'),
                transaction_data['stock_code'],
                transaction_data['market'],
                transaction_data['transaction_date'],
                original_transaction_id,
                is_split=(operation_type == 'split')
            )

            # 根据操作类型处理
            if operation_type == 'delete':
                return TransactionCalculator._handle_delete(
                    db_conn, transaction_data, prev_state, holder_id
                )
            else:
                # 计算持仓变化
                try:
                    position_change = TransactionCalculator.calculate_position_change(
                        transaction_data, prev_state
                    )
                except ValueError as e:
                    return False, {'message': str(e)}

                # 更新数据库
                if operation_type == 'split':
                    return TransactionCalculator._handle_split(
                        db_conn, transaction_data, position_change,
                        holder_id, original_transaction_id
                    )
                elif operation_type == 'edit':
                    return TransactionCalculator._handle_edit(
                        db_conn, transaction_data, position_change,
                        original_transaction_id
                    )
                else:  # add
                    return TransactionCalculator._handle_add(
                        db_conn, transaction_data, position_change
                    )

        except Exception as e:
            logger.error(f"处理交易记录失败: {str(e)}")
            return False, {'message': f'处理交易记录失败: {str(e)}'}

    @staticmethod
    def _get_previous_holding_state(
        db_conn,
        user_or_holder_id: int,
        stock_code: str,
        market: str,
        transaction_date: str,
        transaction_id: Optional[int] = None,
        is_split: bool = False
    ) -> Dict[str, Any]:
        """获取之前的持仓状态"""
        table = "transaction_splits" if is_split else "stock_transactions"
        id_field = "holder_id" if is_split else "user_id"
        
        sql = f"""
            SELECT current_quantity as quantity,
                   current_cost as cost,
                   current_avg_cost as avg_cost
            FROM {table}
            WHERE {id_field} = %s
                AND stock_code = %s
                AND market = %s
                AND (transaction_date < %s
                     OR (transaction_date = %s AND id < %s))
            ORDER BY transaction_date DESC, id DESC
            LIMIT 1
        """
        
        cursor = db_conn.cursor()
        cursor.execute(sql, [
            user_or_holder_id, stock_code, market,
            transaction_date, transaction_date,
            transaction_id or 0
        ])
        result = cursor.fetchone()
        cursor.close()
        
        if result:
            return {
                'quantity': Decimal(str(result['quantity'])),
                'cost': Decimal(str(result['cost'])),
                'avg_cost': Decimal(str(result['avg_cost']))
            }
        return {
            'quantity': Decimal('0'),
            'cost': Decimal('0'),
            'avg_cost': Decimal('0')
        }

    @staticmethod
    def _handle_add(
        db_conn,
        transaction_data: Dict[str, Any],
        position_change: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """处理新增交易"""
        try:
            insert_sql = """
                INSERT INTO stock_transactions (
                    user_id, transaction_date, stock_code, market,
                    transaction_type, total_quantity, total_amount,
                    broker_fee, stamp_duty, transaction_levy,
                    trading_fee, deposit_fee, prev_quantity,
                    prev_cost, prev_avg_cost, current_quantity,
                    current_cost, current_avg_cost, total_fees,
                    net_amount, realized_profit, profit_rate,
                    avg_price, remarks
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
            """
            
            params = [
                transaction_data['user_id'],
                transaction_data['transaction_date'],
                transaction_data['stock_code'],
                transaction_data['market'],
                transaction_data['transaction_type'],
                transaction_data['total_quantity'],
                transaction_data['total_amount'],
                transaction_data.get('broker_fee', 0),
                transaction_data.get('stamp_duty', 0),
                transaction_data.get('transaction_levy', 0),
                transaction_data.get('trading_fee', 0),
                transaction_data.get('deposit_fee', 0),
                position_change['prev_quantity'],
                position_change['prev_cost'],
                position_change['prev_avg_cost'],
                position_change['current_quantity'],
                position_change['current_cost'],
                position_change['current_avg_cost'],
                position_change['total_fees'],
                position_change['net_amount'],
                position_change['realized_profit'],
                position_change['profit_rate'],
                position_change['avg_price'],
                transaction_data.get('remarks', '')
            ]
            
            transaction_id = db_conn.insert(insert_sql, params)
            if not transaction_id:
                return False, {'message': '插入交易记录失败'}
                
            return True, {
                'transaction_id': transaction_id,
                'position_change': position_change
            }
            
        except Exception as e:
            logger.error(f"新增交易记录失败: {str(e)}")
            return False, {'message': f'新增交易记录失败: {str(e)}'}

    @staticmethod
    def _handle_edit(
        db_conn,
        transaction_data: Dict[str, Any],
        position_change: Dict[str, Any],
        transaction_id: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """处理编辑交易"""
        try:
            update_sql = """
                UPDATE stock_transactions
                SET transaction_date = %s,
                    stock_code = %s,
                    market = %s,
                    transaction_type = %s,
                    total_quantity = %s,
                    total_amount = %s,
                    broker_fee = %s,
                    stamp_duty = %s,
                    transaction_levy = %s,
                    trading_fee = %s,
                    deposit_fee = %s,
                    prev_quantity = %s,
                    prev_cost = %s,
                    prev_avg_cost = %s,
                    current_quantity = %s,
                    current_cost = %s,
                    current_avg_cost = %s,
                    total_fees = %s,
                    net_amount = %s,
                    realized_profit = %s,
                    profit_rate = %s,
                    avg_price = %s,
                    remarks = %s,
                    updated_at = NOW()
                WHERE id = %s
            """
            
            params = [
                transaction_data['transaction_date'],
                transaction_data['stock_code'],
                transaction_data['market'],
                transaction_data['transaction_type'],
                transaction_data['total_quantity'],
                transaction_data['total_amount'],
                transaction_data.get('broker_fee', 0),
                transaction_data.get('stamp_duty', 0),
                transaction_data.get('transaction_levy', 0),
                transaction_data.get('trading_fee', 0),
                transaction_data.get('deposit_fee', 0),
                position_change['prev_quantity'],
                position_change['prev_cost'],
                position_change['prev_avg_cost'],
                position_change['current_quantity'],
                position_change['current_cost'],
                position_change['current_avg_cost'],
                position_change['total_fees'],
                position_change['net_amount'],
                position_change['realized_profit'],
                position_change['profit_rate'],
                position_change['avg_price'],
                transaction_data.get('remarks', ''),
                transaction_id
            ]
            
            success = db_conn.execute(update_sql, params)
            if not success:
                return False, {'message': '更新交易记录失败'}
                
            return True, {'position_change': position_change}
            
        except Exception as e:
            logger.error(f"编辑交易记录失败: {str(e)}")
            return False, {'message': f'编辑交易记录失败: {str(e)}'}

    @staticmethod
    def _handle_delete(
        db_conn,
        transaction_data: Dict[str, Any],
        prev_state: Dict[str, Any],
        holder_id: Optional[int] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """处理删除交易"""
        try:
            if holder_id:
                # 删除分单记录
                delete_sql = """
                    DELETE FROM transaction_splits
                    WHERE holder_id = %s
                        AND stock_code = %s
                        AND market = %s
                        AND transaction_date = %s
                """
                params = [
                    holder_id,
                    transaction_data['stock_code'],
                    transaction_data['market'],
                    transaction_data['transaction_date']
                ]
            else:
                # 删除原始交易记录
                delete_sql = """
                    DELETE FROM stock_transactions
                    WHERE id = %s
                """
                params = [transaction_data['id']]
            
            cursor = db_conn.cursor()
            cursor.execute(delete_sql, params)
            affected_rows = cursor.rowcount
            db_conn.commit()
            cursor.close()
            
            if affected_rows == 0:
                return False, {'message': '删除交易记录失败'}
                
            return True, {'prev_state': prev_state}
            
        except Exception as e:
            logger.error(f"删除交易记录失败: {str(e)}")
            return False, {'message': f'删除交易记录失败: {str(e)}'}

    @staticmethod
    def _handle_split(
        db_conn,
        transaction_data: Dict[str, Any],
        position_change: Dict[str, Any],
        holder_id: int,
        original_transaction_id: int
    ) -> Tuple[bool, Dict[str, Any]]:
        """处理交易分单"""
        try:
            logger.info(f"开始处理交易分单: holder_id={holder_id}, original_transaction_id={original_transaction_id}")
            logger.info(f"交易数据: {transaction_data}")
            logger.info(f"持仓变化: {position_change}")
            
            # 获取股票名称
            cursor = db_conn.cursor()
            stock_name_sql = """
                SELECT code_name FROM stocks 
                WHERE code = %s AND market = %s
                LIMIT 1
            """
            cursor.execute(stock_name_sql, [
                transaction_data['stock_code'],
                transaction_data['market']
            ])
            stock_result = cursor.fetchone()
            stock_name = stock_result['code_name'] if stock_result else transaction_data['stock_code']
            cursor.close()
            
            insert_sql = """
                INSERT INTO transaction_splits (
                    original_transaction_id, holder_id, split_ratio,
                    transaction_date, stock_code, market, stock_name,
                    transaction_type, total_quantity, total_amount,
                    broker_fee, stamp_duty, transaction_levy,
                    trading_fee, deposit_fee, prev_quantity,
                    prev_cost, prev_avg_cost, current_quantity,
                    current_cost, current_avg_cost, total_fees,
                    net_amount, realized_profit, profit_rate,
                    avg_price, remarks
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            params = [
                original_transaction_id,
                holder_id,
                transaction_data['split_ratio'],
                transaction_data['transaction_date'],
                transaction_data['stock_code'],
                transaction_data['market'],
                stock_name,
                transaction_data['transaction_type'],
                transaction_data['total_quantity'],
                transaction_data['total_amount'],
                transaction_data.get('broker_fee', 0),
                transaction_data.get('stamp_duty', 0),
                transaction_data.get('transaction_levy', 0),
                transaction_data.get('trading_fee', 0),
                transaction_data.get('deposit_fee', 0),
                position_change['prev_quantity'],
                position_change['prev_cost'],
                position_change['prev_avg_cost'],
                position_change['current_quantity'],
                position_change['current_cost'],
                position_change['current_avg_cost'],
                position_change['total_fees'],
                position_change['net_amount'],
                position_change['realized_profit'],
                position_change['profit_rate'],
                position_change['avg_price'],
                transaction_data.get('remarks', '') or ''
            ]
            
            logger.info(f"执行SQL: {insert_sql}")
            logger.info(f"参数: {params}")
            
            cursor = db_conn.cursor()
            cursor.execute(insert_sql, params)
            split_id = cursor.lastrowid
            db_conn.commit()
            cursor.close()
            
            logger.info(f"分单记录插入成功，ID: {split_id}")
            
            if not split_id:
                logger.error("插入分单记录失败，未获取到ID")
                return False, {'message': '插入分单记录失败'}
                
            return True, {
                'split_id': split_id,
                'position_change': position_change
            }
            
        except Exception as e:
            logger.error(f"处理交易分单失败: {str(e)}")
            return False, {'message': f'处理交易分单失败: {str(e)}'}

    @staticmethod
    def recalculate_subsequent_transactions(
        db_conn,
        stock_code: str,
        market: str,
        start_date: str,
        holder_id: Optional[int] = None
    ) -> bool:
        """
        重新计算后续交易记录
        
        Args:
            db_conn: 数据库连接
            stock_code: 股票代码
            market: 市场
            start_date: 开始日期
            holder_id: 持有人ID（可选）
            
        Returns:
            bool: 是否成功
        """
        try:
            # 获取需要重新计算的交易记录
            if holder_id:
                sql = """
                    SELECT *
                    FROM transaction_splits
                    WHERE holder_id = %s
                        AND stock_code = %s
                        AND market = %s
                        AND transaction_date >= %s
                    ORDER BY transaction_date, id
                """
                params = [holder_id, stock_code, market, start_date]
            else:
                sql = """
                    SELECT *
                    FROM stock_transactions
                    WHERE stock_code = %s
                        AND market = %s
                        AND transaction_date >= %s
                    ORDER BY transaction_date, id
                """
                params = [stock_code, market, start_date]
            
            cursor = db_conn.cursor()
            cursor.execute(sql, params)
            transactions = cursor.fetchall()
            cursor.close()
            
            if not transactions:
                return True
            
            # 获取第一条记录之前的状态
            prev_state = TransactionCalculator._get_previous_holding_state(
                db_conn,
                holder_id if holder_id else transactions[0]['user_id'],
                stock_code,
                market,
                start_date,
                is_split=bool(holder_id)
            )
            
            # 逐条重新计算
            for trans in transactions:
                # 构建交易数据
                transaction_data = {
                    'transaction_type': trans['transaction_type'],
                    'total_quantity': trans['total_quantity'],
                    'total_amount': trans['total_amount'],
                    'broker_fee': trans['broker_fee'],
                    'stamp_duty': trans['stamp_duty'],
                    'transaction_levy': trans['transaction_levy'],
                    'trading_fee': trans['trading_fee'],
                    'deposit_fee': trans['deposit_fee']
                }
                
                # 计算持仓变化
                try:
                    position_change = TransactionCalculator.calculate_position_change(
                        transaction_data, prev_state
                    )
                except ValueError:
                    return False
                
                # 更新数据库
                if holder_id:
                    update_sql = """
                        UPDATE transaction_splits
                        SET prev_quantity = %s,
                            prev_cost = %s,
                            prev_avg_cost = %s,
                            current_quantity = %s,
                            current_cost = %s,
                            current_avg_cost = %s,
                            total_fees = %s,
                            net_amount = %s,
                            realized_profit = %s,
                            profit_rate = %s,
                            avg_price = %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """
                else:
                    update_sql = """
                        UPDATE stock_transactions
                        SET prev_quantity = %s,
                            prev_cost = %s,
                            prev_avg_cost = %s,
                            current_quantity = %s,
                            current_cost = %s,
                            current_avg_cost = %s,
                            total_fees = %s,
                            net_amount = %s,
                            realized_profit = %s,
                            profit_rate = %s,
                            avg_price = %s,
                            updated_at = NOW()
                        WHERE id = %s
                    """
                
                params = [
                    position_change['prev_quantity'],
                    position_change['prev_cost'],
                    position_change['prev_avg_cost'],
                    position_change['current_quantity'],
                    position_change['current_cost'],
                    position_change['current_avg_cost'],
                    position_change['total_fees'],
                    position_change['net_amount'],
                    position_change['realized_profit'],
                    position_change['profit_rate'],
                    position_change['avg_price'],
                    trans['id']
                ]
                
                cursor = db_conn.cursor()
                cursor.execute(update_sql, params)
                db_conn.commit()
                cursor.close()
                
                # 更新前值状态用于下一次计算
                prev_state = {
                    'quantity': position_change['current_quantity'],
                    'cost': position_change['current_cost'],
                    'avg_cost': position_change['current_avg_cost']
                }
            
            return True
            
        except Exception as e:
            logger.error(f"重新计算后续交易记录失败: {str(e)}")
            return False

    @staticmethod
    def validate_transaction(transaction):
        """验证交易记录"""
        required_fields = [
            'transaction_date',
            'stock_code',
            'market',
            'transaction_type',
            'total_quantity',
            'total_amount'
        ]
        
        errors = []
        
        # 检查必填字段
        for field in required_fields:
            if not transaction.get(field):
                errors.append(f'缺少必填字段: {field}')
        
        # 验证数值字段
        if transaction.get('total_quantity'):
            try:
                quantity = Decimal(str(transaction['total_quantity']))
                if quantity <= 0:
                    errors.append('交易数量必须大于0')
            except:
                errors.append('交易数量必须为数字')
        
        if transaction.get('total_amount'):
            try:
                amount = Decimal(str(transaction['total_amount']))
                if amount <= 0:
                    errors.append('交易金额必须大于0')
            except:
                errors.append('交易金额必须为数字')
        
        # 验证交易类型
        if transaction.get('transaction_type'):
            if transaction['transaction_type'].lower() not in ['buy', 'sell']:
                errors.append('交易类型必须为 buy 或 sell')
        
        # 验证日期格式
        if transaction.get('transaction_date'):
            try:
                if isinstance(transaction['transaction_date'], str):
                    datetime.strptime(transaction['transaction_date'], '%Y-%m-%d')
            except:
                errors.append('交易日期格式错误，应为 YYYY-MM-DD')
        
        return errors 