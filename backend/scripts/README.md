# 后端管理脚本

本目录包含系统管理和维护所需的核心脚本。这些脚本用于数据库初始化、权限设置和管理员管理等操作。

## 脚本列表

### 数据库管理

- `create_database.py` - 创建并初始化数据库
  - 用法: `python create_database.py`
  - 功能: 创建数据库结构，设置初始表格和基础数据

### 用户管理

- `reset_admin_password.py` - 重置管理员密码
  - 用法: `python reset_admin_password.py [新密码]`
  - 功能: 当管理员密码丢失时，可以使用此脚本重置

### 权限管理

- `init_rbac.py` - 初始化基于角色的访问控制
  - 用法: `python init_rbac.py`
  - 功能: 设置基本的角色和权限

- `create_rbac_tables.py` - 创建RBAC所需的数据库表
  - 用法: `python create_rbac_tables.py`
  - 功能: 初始化角色、权限和用户关联表

## 使用说明

这些脚本通常在系统部署或重大维护时使用。请在执行前确保了解脚本的功能和影响。

### 执行方法

1. 确保已安装所有依赖:
   ```bash
   pip install -r ../requirements.txt
   ```

2. 执行脚本:
   ```bash
   python <script_name>.py
   ```

## 注意事项

- 大多数脚本需要在项目根目录或backend目录下执行
- 执行脚本前请确保数据库连接配置正确
- 部分脚本可能会修改或删除数据，请在执行前进行数据备份

# 脚本工具集

本目录包含各种用于系统维护和数据处理的脚本工具。

## 脚本列表

### recalculate_transaction_splits.py

该脚本用于重新计算交易分单表中的字段，包括 `prev_quantity`, `prev_cost`, `prev_avg_cost`, `current_quantity`, `current_cost`, `current_avg_cost`, `running_quantity`, `running_cost`, `realized_profit`, `profit_rate` 等。

**功能说明**：
- 按持有人和股票分组获取交易分单记录
- 按交易日期和ID排序处理每条记录
- 重新计算以下字段：
  - prev_quantity（交易前持仓数量）
  - prev_cost（交易前总成本）
  - prev_avg_cost（交易前移动加权平均价）
  - current_quantity（交易后持仓数量）
  - current_cost（交易后总成本）
  - current_avg_cost（交易后移动加权平均价）
  - total_fees（总费用）
  - net_amount（净金额）
  - running_quantity（累计数量）
  - running_cost（累计成本）
  - realized_profit（已实现盈亏）
  - profit_rate（盈亏比率）
- 使用批量更新提高性能

**计算逻辑**：
1. **买入交易**:
   - `current_quantity` = `prev_quantity` + `total_quantity`
   - `buy_cost_with_fees` = `total_amount` + `total_fees` (包含所有交易费用)
   - `current_cost` = `prev_cost` + `buy_cost_with_fees`
   - `current_avg_cost` = `current_cost` / `current_quantity`
   - `net_amount` = -(`total_amount` + `total_fees`) (买入为负数，表示支出)

2. **卖出交易**:
   - `current_quantity` = `prev_quantity` - `total_quantity`
   - `buy_cost` = `total_quantity` * `prev_avg_cost`
   - `realized_profit` = `total_amount` - `buy_cost` - `total_fees`
   - `profit_rate` = (`realized_profit` / `buy_cost`) * 100
   - `current_cost` = `prev_cost` * (`current_quantity` / `prev_quantity`)
   - `current_avg_cost` = `prev_avg_cost` (保持不变)
   - `net_amount` = `total_amount` - `total_fees` (卖出为正数，表示收入)

**使用方法**：
```bash
# 处理所有记录
python backend/scripts/recalculate_transaction_splits.py

# 只处理指定持有人的记录
python backend/scripts/recalculate_transaction_splits.py --holder_id=1

# 只处理指定股票的记录
python backend/scripts/recalculate_transaction_splits.py --stock_code=00700 --market=HK

# 只处理指定日期及之后的记录
python backend/scripts/recalculate_transaction_splits.py --date=2023-01-01

# 只处理指定交易及其后续交易
python backend/scripts/recalculate_transaction_splits.py --transaction_id=123

# 同时更新原始交易记录
python backend/scripts/recalculate_transaction_splits.py --update_original
```

**日志**：
执行日志将保存在 `logs/recalculate_transaction_splits_YYYYMMDD.log` 文件中，包含处理的记录数量和任何错误信息。

**注意事项**：
- 该脚本会按照持有人、股票、交易日期和ID排序处理记录
- 使用批量更新提高性能
- 建议在执行前备份数据库

### add_default_splits.py

为没有分单记录的交易添加默认的100%分单记录。

**功能说明**：
- 查找所有没有分单记录的交易
- 为每个交易创建一个100%的默认分单记录
- 关联到用户的默认持有人（第一个关联的持有人）
- 计算所有必要的持仓字段（prev_quantity, prev_cost, current_quantity等）
- 更新交易记录的has_splits标志

**使用方法**：
```bash
cd /path/to/project
python backend/scripts/add_default_splits.py
```

**日志**：
执行日志将保存在 `logs/add_default_splits_YYYYMMDD.log` 文件中，包含处理的交易数量和任何错误信息。

**注意事项**：
- 脚本会跳过没有关联持有人的交易
- 对于卖出交易，如果没有之前的持仓记录，会记录异常但继续处理其他交易

### execute_db_changes.py

执行数据库结构更改脚本，用于添加新字段和更新数据。

**功能**：
该脚本会执行 `add_database_fields.sql` 文件中的SQL语句，包括：

1. 为 `stock_transactions` 表添加 `has_splits` 和 `avg_price` 字段
2. 为 `transaction_splits` 表添加 `avg_price` 字段
3. 更新 `stock_transactions` 表中的 `has_splits` 字段，根据是否存在对应的分单记录
4. 计算并更新两个表中的 `avg_price` 字段

**使用方法**：
```bash
python backend/scripts/execute_db_changes.py
```

**日志**：
执行日志将保存在 `logs/db_changes_YYYYMMDD.log` 文件中，包含每条SQL语句的执行结果和任何错误信息。

### update_transaction_fields.py

该脚本用于在交易记录的增加、修改、删除和分单操作后更新相关字段的计算，特别是移动加权平均价格。

**功能**：
- 重新计算交易分单表（`transaction_splits`）中的字段，包括：
  - `prev_quantity`：交易前数量
  - `prev_cost`：交易前成本
  - `prev_avg_cost`：交易前平均成本
  - `current_quantity`：交易后数量
  - `current_cost`：交易后成本
  - `current_avg_cost`：交易后平均成本（移动加权平均价格）
  - `running_quantity`：累计数量
  - `running_cost`：累计成本
  - `realized_profit`：已实现盈亏
  - `profit_rate`：盈亏率

- 支持按持有人、股票、市场或特定交易ID进行筛选处理
- 支持按日期筛选，只处理指定日期之后的记录
- 支持更新原始交易记录，使其与分单记录保持一致

**计算逻辑**：
1. **买入交易**:
   - `current_quantity` = `prev_quantity` + `total_quantity`
   - `buy_cost_with_fees` = `total_amount` + `total_fees` (包含所有交易费用)
   - `current_cost` = `prev_cost` + `buy_cost_with_fees`
   - `current_avg_cost` = `current_cost` / `current_quantity`
   - `net_amount` = -(`total_amount` + `total_fees`) (买入为负数，表示支出)

2. **卖出交易**:
   - `current_quantity` = `prev_quantity` - `total_quantity`
   - `buy_cost` = `total_quantity` * `prev_avg_cost`
   - `realized_profit` = `total_amount` - `buy_cost` - `total_fees`
   - `profit_rate` = (`realized_profit` / `buy_cost`) * 100
   - `current_cost` = `prev_cost` * (`current_quantity` / `prev_quantity`)
   - `current_avg_cost` = `prev_avg_cost` (保持不变)
   - `net_amount` = `total_amount` - `total_fees` (卖出为正数，表示收入)

**使用方法**：
```bash
python update_transaction_fields.py  # 处理所有记录
python update_transaction_fields.py --holder_id=1  # 只处理指定持有人的记录
python update_transaction_fields.py --stock_code=00700 --market=HK  # 只处理指定股票的记录
python update_transaction_fields.py --transaction_id=123  # 只处理指定交易ID及其后续交易
python update_transaction_fields.py --date=2023-01-01  # 只处理指定日期之后的记录
python update_transaction_fields.py --update_original  # 同时更新原始交易记录
```

**注意事项**：
- 该脚本会按照持有人、股票、交易日期和ID排序处理记录
- 使用批量更新提高性能
- 建议在执行前备份数据库
- 脚本会自动获取指定交易之前的持仓状态，确保计算的连续性

**日志**：
脚本执行过程中的日志会保存在 `logs/update_transaction_fields_YYYYMMDD.log` 文件中，同时也会在控制台输出。

## 核心模块

### utils/transaction_recalculator.py

该模块提供了重新计算交易分单记录字段的核心功能，可以在添加交易记录、修改交易记录、删除交易记录、交易记录分单后调用，确保所有相关字段的计算准确性。

**主要功能**：
- 提供统一的交易记录重新计算功能
- 支持按持有人、股票、日期、交易ID等条件筛选记录
- 自动获取交易前的持仓状态，确保计算的连续性
- 批量更新提高性能
- 支持更新原始交易记录

**主要函数**：
- `recalculate_transaction_splits(holder_id=None, stock_code=None, market=None, start_date=None, transaction_id=None, update_original=False)`：重新计算交易分单记录字段
- `get_previous_state(holder_id, market, stock_code, transaction_date, transaction_id=None)`：获取指定交易之前的持仓状态
- `update_original_transactions()`：更新原始交易记录，使其与分单记录保持一致

**集成方式**：
该模块已集成到交易服务中，在以下操作后会自动调用：
1. 添加交易记录
2. 修改交易记录
3. 删除交易记录
4. 交易记录分单

**手动调用**：
```python
from utils.transaction_recalculator import recalculate_transaction_splits

# 重新计算指定股票在指定日期之后的记录
recalculate_transaction_splits(
    stock_code='00700',
    market='HK',
    start_date='2023-01-01',
    update_original=True
)
```

**注意事项**：
- 该模块会修改数据库中的记录，建议在执行前备份数据库
- 对于大量数据，处理可能需要较长时间，建议在非高峰期执行
- 使用日期参数可以大幅减少处理时间，只更新最近的交易记录 