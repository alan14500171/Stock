<template>
  <tbody class="stock-group">
    <!-- 组标题行 -->
    <tr :class="['group-row', type === 'holding' ? 'holding-group' : 'closed-group']" @click="$emit('toggle')">
      <td class="text-center">
        <i :class="['bi', isExpanded ? 'bi-chevron-down' : 'bi-chevron-right']"></i>
      </td>
      <td colspan="12">
        <i :class="['bi', type === 'holding' ? 'bi-graph-up text-success' : 'bi-check-circle text-secondary']"></i>
        {{ type === 'holding' ? '持仓股票' : '已清仓股票' }}
        <span class="badge bg-secondary ms-2">{{ stocks.length }}</span>
      </td>
    </tr>

    <!-- 股票列表 -->
    <template v-if="isExpanded">
      <tr v-for="stock in stocks" :key="stock.code" class="stock-row">
        <td class="text-center">
          <button class="btn btn-sm btn-link p-0" @click="$emit('toggleStock', stock.code)">
            <i :class="['bi', isStockExpanded(stock.code) ? 'bi-chevron-down' : 'bi-chevron-right']"></i>
          </button>
        </td>
        <td>
          {{ stock.code }}
          <br>
          <small class="text-muted">{{ stock.name }}</small>
        </td>
        <td class="text-end">{{ stock.quantity || '-' }}</td>
        <td class="text-end">{{ stock.transaction_count || 0 }}</td>
        <td class="text-end text-danger">{{ formatAmount(stock.total_buy_hkd) }}</td>
        <td class="text-end">{{ formatAmount(stock.average_cost, 3) }}</td>
        <td class="text-end text-success">{{ formatAmount(stock.total_sell_hkd) }}</td>
        <td class="text-end">{{ formatAmount(stock.total_fees_hkd) }}</td>
        <td class="text-end" :class="getProfitClass(stock.realized_profit_hkd)">
          {{ formatAmount(stock.realized_profit_hkd) }}
        </td>
        <td class="text-end">{{ formatAmount(stock.current_price, 3) }}</td>
        <td class="text-end">{{ formatAmount(stock.market_value) }}</td>
        <td class="text-end" :class="getProfitClass(stock.total_profit)">
          {{ formatAmount(stock.total_profit) }}
        </td>
        <td class="text-end" :class="getProfitClass(stock.profit_rate)">
          {{ formatPercent(stock.profit_rate) }}
        </td>
      </tr>

      <!-- 交易明细 -->
      <template v-for="stock in stocks" :key="'details-' + stock.code">
        <template v-if="isStockExpanded(stock.code)">
          <transaction-item
            v-for="transaction in getTransactionDetails(stock.code)"
            :key="transaction.id"
            :transaction="transaction"
          />
        </template>
      </template>
    </template>
  </tbody>
</template>

<script setup>
import TransactionItem from './TransactionItem.vue'

const props = defineProps({
  market: {
    type: String,
    required: true
  },
  type: {
    type: String,
    required: true,
    validator: (value) => ['holding', 'closed'].includes(value)
  },
  stocks: {
    type: Array,
    required: true
  },
  isExpanded: {
    type: Boolean,
    default: false
  },
  expandedStocks: {
    type: Set,
    required: true
  },
  transactionDetails: {
    type: Object,
    required: true
  }
})

// 格式化数字
const formatNumber = (value, decimals = 2) => {
  if (value === null || value === undefined) return '-'
  return Number(value).toLocaleString('zh-HK', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })
}

// 格式化百分比
const formatPercent = (value) => {
  if (value === null || value === undefined) return '-'
  return `${formatNumber(value, 1)}%`
}

// 格式化金额
const formatAmount = (value, decimals = 2) => {
  if (value === null || value === undefined) return '-'
  return formatNumber(value, decimals)
}

// 获取盈亏样式
const getProfitClass = (value) => {
  if (!value) return ''
  return value > 0 ? 'text-success' : value < 0 ? 'text-danger' : ''
}

// 检查股票是否展开
const isStockExpanded = (code) => {
  return props.expandedStocks.has(`${props.market}-${code}`)
}

// 获取交易明细
const getTransactionDetails = (code) => {
  const key = `${props.market}-${code}`
  return props.transactionDetails[key] || []
}
</script>

<style scoped>
.group-row {
  background-color: #f8f9fa;
  cursor: pointer;
  font-weight: 500;
}

.holding-group {
  border-left: 4px solid #198754;
}

.closed-group {
  border-left: 4px solid #6c757d;
}

.stock-row {
  cursor: pointer;
}

.stock-row:hover {
  background-color: #f8f9fa;
}

.btn-link {
  text-decoration: none;
  color: #6c757d;
}

.btn-link:hover {
  color: #0d6efd;
}

.text-success {
  color: #198754 !important;
}

.text-danger {
  color: #dc3545 !important;
}

.badge {
  font-weight: normal;
}
</style> 