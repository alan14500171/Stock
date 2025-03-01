from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

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
            'avg_price': Decimal('0')  # 添加平均价格字段
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

    @staticmethod
    def get_previous_state(db, user_id, stock_code, market, transaction_date, transaction_id=None):
        """获取交易之前的持仓状态"""
        sql = """
            SELECT id,
                   current_quantity as quantity,
                   current_cost as cost,
                   current_avg_cost as avg_cost
            FROM stock.stock_transactions 
            WHERE user_id = %s 
                AND stock_code = %s 
                AND market = %s
                AND (transaction_date < %s 
                     OR (transaction_date = %s AND id < %s))
            ORDER BY transaction_date DESC, id DESC 
            LIMIT 1
        """
        params = [
            user_id, stock_code, market,
            transaction_date, transaction_date,
            transaction_id or 0
        ]
        
        result = db.fetch_one(sql, params)
        if result:
            return {
                'id': result['id'],
                'quantity': Decimal(str(result['quantity'])),
                'cost': Decimal(str(result['cost'])),
                'avg_cost': Decimal(str(result['avg_cost']))
            }
        return {
            'id': 0,
            'quantity': Decimal('0'),
            'cost': Decimal('0'),
            'avg_cost': Decimal('0')
        }

    @staticmethod
    def update_subsequent_transactions(db, user_id, stock_code, market, transaction_date, transaction_id, holder_id=None):
        """
        更新后续交易记录
        
        Args:
            db: 数据库连接
            user_id: 用户ID
            stock_code: 股票代码
            market: 市场
            transaction_date: 交易日期
            transaction_id: 交易ID
            holder_id: 持有人ID（可选）
        """
        # 获取当前编辑的交易分单记录
        if holder_id:
            # 如果提供了持有人ID，获取该持有人的分单记录
            current_transaction_sql = """
                SELECT current_quantity, current_cost, current_avg_cost
                FROM stock.transaction_splits 
                WHERE original_transaction_id = %s AND holder_id = %s
            """
            current_trans = db.fetch_one(current_transaction_sql, [transaction_id, holder_id])
        else:
            # 如果没有提供持有人ID，获取原始交易记录
            current_transaction_sql = """
                SELECT current_quantity, current_cost, current_avg_cost
                FROM stock.stock_transactions 
                WHERE id = %s AND user_id = %s
            """
            current_trans = db.fetch_one(current_transaction_sql, [transaction_id, user_id])
        
        if not current_trans:
            return False
        
        # 获取后续交易分单记录
        if holder_id:
            # 如果提供了持有人ID，获取该持有人的后续分单记录
            sql = """
                SELECT id, transaction_type, total_quantity, total_amount,
                       broker_fee, transaction_levy, stamp_duty, 
                       trading_fee, deposit_fee
                FROM stock.transaction_splits 
                WHERE holder_id = %s 
                    AND stock_code = %s 
                    AND market = %s
                    AND (transaction_date > %s 
                         OR (transaction_date = %s AND id > %s))
                ORDER BY transaction_date, id
            """
            transactions = db.fetch_all(sql, [
                holder_id, stock_code, market,
                transaction_date, transaction_date,
                transaction_id
            ])
        else:
            # 如果没有提供持有人ID，获取原始交易记录
            sql = """
                SELECT id, transaction_type, total_quantity, total_amount,
                       broker_fee, transaction_levy, stamp_duty, 
                       trading_fee, deposit_fee
                FROM stock.stock_transactions 
                WHERE user_id = %s 
                    AND stock_code = %s 
                    AND market = %s
                    AND (transaction_date > %s 
                         OR (transaction_date = %s AND id > %s))
                ORDER BY transaction_date, id
            """
            transactions = db.fetch_all(sql, [
                user_id, stock_code, market,
                transaction_date, transaction_date,
                transaction_id
            ])
        
        if not transactions:
            return True
        
        try:
            # 使用当前编辑交易后的状态作为起始状态
            current_state = {
                'quantity': Decimal(str(current_trans['current_quantity'])),
                'cost': Decimal(str(current_trans['current_cost'])),
                'avg_cost': Decimal(str(current_trans['current_avg_cost']))
            }
            
            # 逐个更新后续交易
            for trans in transactions:
                # 对于卖出交易，检查持仓是否足够
                if trans['transaction_type'].lower() == 'sell' and Decimal(str(trans['total_quantity'])) > current_state['quantity']:
                    return False
                
                # 计算新状态
                try:
                    new_state = TransactionCalculator.calculate_position_change(trans, current_state)
                    
                    # 更新数据库
                    if holder_id:
                        # 更新交易分单记录
                        update_sql = """
                            UPDATE stock.transaction_splits
                            SET prev_quantity = %s,
                                prev_cost = %s,
                                prev_avg_cost = %s,
                                current_quantity = %s,
                                current_cost = %s,
                                current_avg_cost = %s,
                                realized_profit = %s,
                                profit_rate = %s,
                                avg_price = %s,
                                updated_at = NOW()
                            WHERE id = %s
                        """
                    else:
                        # 更新原始交易记录
                        update_sql = """
                            UPDATE stock.stock_transactions
                            SET prev_quantity = %s,
                                prev_cost = %s,
                                prev_avg_cost = %s,
                                current_quantity = %s,
                                current_cost = %s,
                                current_avg_cost = %s,
                                realized_profit = %s,
                                profit_rate = %s,
                                avg_price = %s,
                                updated_at = NOW()
                            WHERE id = %s
                        """
                    
                    db.execute(update_sql, [
                        new_state['prev_quantity'],
                        new_state['prev_cost'],
                        new_state['prev_avg_cost'],
                        new_state['current_quantity'],
                        new_state['current_cost'],
                        new_state['current_avg_cost'],
                        new_state['realized_profit'],
                        new_state['profit_rate'],
                        new_state['avg_price'],
                        trans['id']
                    ])
                    
                    # 更新当前状态用于下一次计算
                    current_state = {
                        'quantity': new_state['current_quantity'],
                        'cost': new_state['current_cost'],
                        'avg_cost': new_state['current_avg_cost']
                    }
                except ValueError:
                    return False
            
            return True
            
        except Exception as e:
            print(f"更新后续交易记录失败: {str(e)}")
            return False 