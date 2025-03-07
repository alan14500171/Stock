<template>
  <template class="stock-item">
    <!-- 股票信息行 -->
    <tr :class="['stock-row', type === 'holding' ? 'holding-stock' : 'closed-stock']" @click="$emit('toggle')">
      <td class="text-center">
        <i :class="['bi', isExpanded ? 'bi-chevron-down' : 'bi-chevron-right']"></i>
      </td>
      <td>
        {{ stock.code }}
        <br>
        <small class="text-muted">{{ stock.name }}</small>
      </td>
      <td class="text-end">{{ stock.quantity || '-' }}</td>
      <td class="text-end">{{ stock.transaction_count }}</td>
      <td class="text-end text-danger">{{ formatNumber(stock.total_buy) }}</td>
      <td class="text-end">{{ formatNumber(stock.average_cost, 3) }}</td>
      <td class="text-end text-success">{{ formatNumber(stock.total_sell) }}</td>
      <td class="text-end">{{ formatNumber(stock.total_fees) }}</td>
      <td class="text-end" :class="getProfitClass(stock.realized_profit)">
        {{ formatNumber(stock.realized_profit) }}
      </td>
      <td class="text-end">{{ stock.current_price ? formatNumber(stock.current_price, 3) : '-' }}</td>
      <td class="text-end">{{ formatNumber(stock.market_value) }}</td>
      <td class="text-end" :class="getProfitClass(stock.total_profit)">
        {{ formatNumber(stock.total_profit) }}
      </td>
      <td class="text-end" :class="getProfitClass(stock.profit_rate)">
        {{ formatRate(stock.profit_rate) }}
      </td>
    </tr>

    <!-- 交易明细 -->
    <template v-if="isExpanded && transactionDetails">
      <transaction-item
        v-for="transaction in transactionDetails"
        :key="transaction.id"
        :transaction="transaction"
      />
    </template>
  </template>
</template>

<script setup>
import TransactionItem from './TransactionItem.vue'

defineProps({
  stock: {
    type: Object,
    required: true
  },
  type: {
    type: String,
    required: true,
    validator: (value) => ['holding', 'closed'].includes(value)
  },
  isExpanded: {
    type: Boolean,
    default: false
  },
  transactionDetails: {
    type: Array,
    default: () => []
  }
})

// 格式化函数
const formatNumber = (value, decimals = 2) => {
  if (value === null || value === undefined) return '-'
  return Number(value).toLocaleString('zh-HK', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })
}

const formatRate = (value) => {
  if (value === null || value === undefined) return '-'
  return value.toFixed(1) + '%'
}

const getProfitClass = (value) => {
  if (!value) return ''
  return value > 0 ? 'text-success' : value < 0 ? 'text-danger' : ''
}
</script>

<style scoped>
.stock-row {
  cursor: pointer;
}

.holding-stock {
  border-left: 4px solid #198754;
}

.closed-stock {
  border-left: 4px solid #6c757d;
}

.text-success {
  color: #198754 !important;
}

.text-danger {
  color: #dc3545 !important;
}
</style> 