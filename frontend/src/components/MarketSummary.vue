<template>
  <tr class="market-row">
    <td>
      <button class="btn btn-sm btn-link p-0" @click="$emit('toggle')">
        <i :class="['bi', isExpanded ? 'bi-chevron-down' : 'bi-chevron-right']"></i>
      </button>
    </td>
    <td>{{ market }}</td>
    <td class="text-end">-</td>
    <td class="text-end">{{ data.transaction_count || 0 }}</td>
    <td class="text-end text-danger">{{ formatAmount(data.total_buy_hkd) }}</td>
    <td class="text-end">-</td>
    <td class="text-end text-success">{{ formatAmount(data.total_sell_hkd) }}</td>
    <td class="text-end">{{ formatAmount(data.total_fees_hkd) }}</td>
    <td class="text-end" :class="getProfitClass(data.realized_profit_hkd)">
      {{ formatAmount(data.realized_profit_hkd) }}
    </td>
    <td class="text-end">-</td>
    <td class="text-end">{{ formatAmount(data.market_value) }}</td>
    <td class="text-end" :class="getProfitClass(data.total_profit)">
      {{ formatAmount(data.total_profit) }}
    </td>
    <td class="text-end" :class="getProfitClass(data.profit_rate)">
      {{ formatPercent(data.profit_rate) }}
    </td>
  </tr>
</template>

<script setup>
const props = defineProps({
  market: {
    type: String,
    required: true
  },
  data: {
    type: Object,
    required: true
  },
  isExpanded: {
    type: Boolean,
    default: false
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
const formatAmount = (value) => {
  if (value === null || value === undefined) return '-'
  return formatNumber(value, 2)
}

// 获取盈亏样式
const getProfitClass = (value) => {
  if (!value) return ''
  return value > 0 ? 'text-success' : value < 0 ? 'text-danger' : ''
}
</script>

<style scoped>
.market-row {
  background-color: #f8f9fa;
  font-weight: 500;
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
</style> 