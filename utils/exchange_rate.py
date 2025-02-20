from config.database import db
from models import ExchangeRate
from datetime import datetime, timedelta
import requests
import json

def get_exchange_rates_api_rate(currency, date_str=None):
    """从Exchange Rates API获取汇率数据
    
    Args:
        currency: 货币代码
        date_str: 日期字符串，格式为YYYY-MM-DD，如果为None则获取实时汇率
        
    Returns:
        float: 汇率值，如果获取失败则返回None
    """
    print(f"尝试从Exchange Rates API获取{currency}汇率...")
    try:
        # 构建API URL
        base_url = 'https://open.er-api.com/v6'
        if date_str:
            url = f'{base_url}/historical/{date_str}'
        else:
            url = f'{base_url}/latest/USD'
            
        print(f"请求URL: {url}")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data.get('result') == 'success':
            rates = data.get('rates', {})
            if 'HKD' in rates:
                rate = rates['HKD']
                print(f"成功获取到汇率: {rate}")
                return rate
        
        print("未能从API获取到汇率数据")
        return None
        
    except Exception as e:
        print(f"从Exchange Rates API获取汇率时发生错误: {str(e)}")
        return None

def ensure_exchange_rate_exists(currency, date_str):
    """确保指定日期的汇率记录存在，如果不存在则添加临时汇率
    
    Args:
        currency: 货币代码
        date_str: 日期字符串，格式为YYYY-MM-DD
        
    Returns:
        float: 汇率值，如果获取失败则返回None
    """
    try:
        # 转换日期字符串为日期对象
        rate_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # 检查数据库中是否已有该日期的汇率
        rate_record = ExchangeRate.query.filter_by(
            currency=currency,
            rate_date=rate_date
        ).first()
        
        if rate_record:
            return rate_record.rate
            
        print(f"本地数据库中未找到 {date_str} 的 {currency} 汇率记录，尝试从API获取临时汇率...")
        
        # 获取汇率数据
        rate = get_exchange_rates_api_rate(currency, None)  # 使用实时汇率作为临时汇率
        
        if rate:
            # 保存到数据库，标记为临时汇率
            new_rate = ExchangeRate(
                currency=currency,
                rate_date=rate_date,
                rate=rate,
                source='TEMPORARY'  # 标记为临时汇率
            )
            db.session.add(new_rate)
            db.session.commit()
            print(f"已将 {date_str} 的 {currency} 临时汇率保存到本地数据库")
            return rate
            
        print(f"无法获取 {date_str} 的 {currency} 汇率")
        return None
    
    except Exception as e:
        print(f"获取汇率时发生错误: {str(e)}")
        return None

def update_temporary_rates():
    """更新所有临时汇率记录
    
    查找所有标记为临时汇率的记录，尝试从API获取历史汇率进行更新。
    只会更新临时汇率记录，不会修改手动添加或其他来源的汇率。
    
    Returns:
        dict: 包含更新统计信息的字典
            - updated: 成功更新的记录数
            - skipped: 跳过的记录数（非临时汇率）
            - failed: 更新失败的记录数
    """
    stats = {
        'updated': 0,
        'skipped': 0,
        'failed': 0
    }
    
    try:
        # 查找所有临时汇率记录
        temp_rates = ExchangeRate.query.filter_by(source='TEMPORARY').all()
        
        if not temp_rates:
            print("没有找到需要更新的临时汇率记录")
            return stats
            
        print(f"找到 {len(temp_rates)} 条临时汇率记录需要更新")
        
        # 按日期分组，减少API调用次数
        date_groups = {}
        for record in temp_rates:
            date_str = record.rate_date.strftime('%Y-%m-%d')
            if date_str not in date_groups:
                date_groups[date_str] = []
            date_groups[date_str].append(record)
        
        # 更新每个日期的汇率
        for date_str, records in date_groups.items():
            try:
                # 获取该日期的汇率
                rate = get_exchange_rates_api_rate(records[0].currency, date_str)
                
                if rate:
                    # 更新所有该日期的记录
                    for record in records:
                        record.rate = rate
                        record.source = 'EXCHANGE_RATES_API'
                        db.session.merge(record)
                        stats['updated'] += 1
                        print(f"更新记录成功: {date_str}, 新汇率: {rate}")
                else:
                    stats['failed'] += len(records)
                    print(f"获取 {date_str} 的汇率失败")
                
                # 每更新5条记录提交一次事务
                if stats['updated'] % 5 == 0:
                    db.session.commit()
                    print(f"已更新 {stats['updated']} 条记录")
                
            except Exception as e:
                print(f"更新 {date_str} 的汇率记录时发生错误: {str(e)}")
                stats['failed'] += len(records)
        
        # 提交剩余的事务
        try:
            db.session.commit()
            print(f"成功更新临时汇率数据：更新 {stats['updated']} 条，"
                  f"跳过 {stats['skipped']} 条，失败 {stats['failed']} 条")
            
        except Exception as e:
            db.session.rollback()
            print(f"保存数据时发生错误: {str(e)}")
            stats['failed'] += stats['updated']
            stats['updated'] = 0
    
    except Exception as e:
        print(f"更新临时汇率时发生错误: {str(e)}")
        stats['failed'] += 1
    
    return stats

def get_exchange_rate(currency, date_str):
    """获取指定日期的汇率，优先使用本地数据
    
    Args:
        currency: 货币代码
        date_str: 日期字符串，格式为YYYY-MM-DD
        
    Returns:
        float: 汇率值，如果获取失败则返回None
    """
    try:
        # 转换日期字符串为日期对象
        rate_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # 检查数据库中是否已有该日期的汇率
        rate_record = ExchangeRate.query.filter_by(
            currency=currency,
            rate_date=rate_date
        ).first()
        
        if rate_record:
            return rate_record.rate
            
        print(f"本地数据库中未找到 {date_str} 的 {currency} 汇率记录，尝试从API获取...")
        
        # 获取汇率数据
        rate = get_exchange_rates_api_rate(currency, date_str if rate_date != datetime.now().date() else None)
        
        if rate:
            # 保存到数据库
            new_rate = ExchangeRate(
                currency=currency,
                rate_date=rate_date,
                rate=rate,
                source='EXCHANGE_RATES_API'
            )
            db.session.add(new_rate)
            db.session.commit()
            print(f"已将 {date_str} 的 {currency} 汇率保存到本地数据库")
            return rate
            
        print(f"无法获取 {date_str} 的 {currency} 汇率")
        return None
        
    except Exception as e:
        print(f"获取汇率时发生错误: {str(e)}")
        return None

def batch_update_exchange_rates(currency, start_date, end_date):
    """批量更新指定日期范围内的汇率
    
    Args:
        currency: 货币代码
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        dict: 包含更新统计信息的字典
    """
    stats = {
        'added': 0,
        'updated': 0,
        'skipped': 0,
        'failed': 0
    }
    
    try:
        print(f"开始批量更新从 {start_date} 到 {end_date} 的汇率数据...")
        
        # 获取数据库中已存在的记录
        existing_rates = {
            r.rate_date: r
            for r in ExchangeRate.query.filter(
                ExchangeRate.currency == currency,
                ExchangeRate.rate_date >= start_date,
                ExchangeRate.rate_date <= end_date
            ).all()
        }
        
        print(f"数据库中已有 {len(existing_rates)} 条记录")
        
        # 遍历日期范围
        current_date = start_date
        while current_date <= end_date:
            try:
                date_str = current_date.strftime('%Y-%m-%d')
                
                if current_date in existing_rates:
                    record = existing_rates[current_date]
                    # 跳过手动修改的记录
                    if record.source == 'MANUAL':
                        print(f"跳过手动修改的记录: {date_str}")
                        stats['skipped'] += 1
                        current_date += timedelta(days=1)
                        continue
                
                # 获取汇率数据
                rate = get_exchange_rates_api_rate(currency, date_str if current_date != datetime.now().date() else None)
                
                if rate:
                    if current_date in existing_rates:
                        # 更新现有记录
                        record = existing_rates[current_date]
                        record.rate = rate
                        record.source = 'EXCHANGE_RATES_API'
                        db.session.merge(record)
                        stats['updated'] += 1
                        print(f"更新记录: {date_str}, 汇率: {rate}")
                    else:
                        # 创建新记录
                        new_rate = ExchangeRate(
                            currency=currency,
                            rate_date=current_date,
                            rate=rate,
                            source='EXCHANGE_RATES_API'
                        )
                        db.session.add(new_rate)
                        stats['added'] += 1
                        print(f"新增记录: {date_str}, 汇率: {rate}")
                    
                    # 每10条记录提交一次事务
                    if (stats['updated'] + stats['added']) % 10 == 0:
                        db.session.commit()
                        print(f"已保存 {stats['updated'] + stats['added']} 条记录")
                else:
                    stats['failed'] += 1
                    print(f"获取 {date_str} 的汇率失败")
                
            except Exception as e:
                print(f"处理日期 {date_str} 的数据时发生错误: {str(e)}")
                stats['failed'] += 1
            
            current_date += timedelta(days=1)
        
        # 提交剩余的事务
        try:
            db.session.commit()
            print(f"成功更新汇率数据：新增 {stats['added']} 条，更新 {stats['updated']} 条，"
                  f"跳过 {stats['skipped']} 条，失败 {stats['failed']} 条")
            
        except Exception as e:
            db.session.rollback()
            print(f"保存数据时发生错误: {str(e)}")
            stats['failed'] += stats['added'] + stats['updated']
            stats['added'] = 0
            stats['updated'] = 0
    
    except Exception as e:
        print(f"批量更新汇率时发生错误: {str(e)}")
        stats['failed'] += 1
    
    return stats 