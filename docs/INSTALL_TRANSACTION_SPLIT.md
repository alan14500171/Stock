# 交易分单功能安装指南

本文档将指导您安装和配置股票交易系统的交易分单功能。

## 功能介绍

交易分单功能允许用户将单笔股票交易记录拆分给多个持有人，按照指定比例分配股份和相关费用。这对于共同购买股票的场景非常有用，可以清晰记录每个持有人的股份占比和成本。

## 安装步骤

### 1. 创建数据库表

首先，执行数据库迁移脚本，创建交易分单表：

```bash
# 进入后端目录
cd backend

# 执行迁移脚本
python migrations/create_transaction_splits_table.py
```

### 2. 更新后端代码

确保以下文件已正确添加到系统中：

- `backend/routes/transaction_split.py`
- `backend/utils/db.py`（如果不存在）

然后，修改后端入口文件 `backend/main.py`，添加新的路由注册：

```python
# 在导入部分添加
from routes.transaction_split import transaction_split_bp

# 在注册蓝图部分添加
app.register_blueprint(transaction_split_bp)
```

### 3. 更新前端代码

确保以下文件已正确添加到系统中：

- `frontend/src/views/TransactionSplit.vue`

然后，更新路由配置文件 `frontend/src/router/index.js`，添加交易分单页面的路由：

```javascript
import TransactionSplit from '../views/TransactionSplit.vue'

// 在路由列表中添加
{
  path: '/transaction/split',
  name: 'TransactionSplit',
  component: TransactionSplit,
  meta: { 
    title: '交易分单',
    requiresAuth: true,
    permission: 'transaction:records:edit'
  }
}
```

最后，更新 `frontend/src/App.vue` 文件，在导航菜单中添加交易分单入口：

```html
<li class="nav-item">
  <router-link to="/transaction/split" class="nav-link" v-if="hasPermission('transaction:records:edit')">
    <i class="bi bi-scissors"></i> 交易分单
  </router-link>
</li>
```

### 4. 配置权限

确保您的用户具有 `transaction:records:edit` 权限才能访问交易分单功能。可以通过系统的权限管理界面为相应角色分配此权限。

### 5. 重启服务

完成上述配置后，重启前端和后端服务：

```bash
# 重启后端
cd backend
python main.py

# 重启前端
cd frontend
npm run dev
```

## 使用说明

1. 登录系统后，点击导航栏上的"交易分单"菜单项
2. 在搜索框中输入交易编号并点击查询
3. 在查询结果中，可以看到交易详情和分配区域
4. 点击"添加分配"按钮，选择持有人，输入分配比例或数量
5. 确保总分配比例为100%，总分配数量等于原交易数量
6. 点击"保存分单"按钮完成分单操作

## 常见问题

1. **为什么我看不到"交易分单"菜单？**  
   确认您的用户账号拥有 `transaction:records:edit` 权限。

2. **查询交易记录失败怎么办？**  
   确认交易编号输入正确，且该交易记录确实存在于系统中。

3. **保存分单时提示"总比例必须为100%"怎么办？**  
   检查所有分配项的比例之和是否为100%，可以通过调整各个分配项的比例或数量来满足要求。

## 支持与帮助

如有任何问题，请联系系统管理员获取帮助。