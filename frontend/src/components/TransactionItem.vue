<template>
  <tr class="transaction-row">
    <td></td>
    <td>
      <div class="transaction-header">
        <small class="text-muted">{{ formatDate(transaction.transaction_date) }}</small>
        <small class="text-muted ms-2">{{ transaction.transaction_code.trim() }}</small>
      </div>
    </td>
    <td class="text-end">{{ formatNumber(transaction.total_quantity) }}</td>
    <td class="text-end">1</td>
    <td class="text-end" :class="{'text-danger': transaction.transaction_type === 'buy'}">
      {{ transaction.transaction_type === 'buy' ? formatAmount(transaction.total_amount_hkd) : '-' }}
    </td>
    <td class="text-end">{{ formatAmount(transaction.average_price, 3) }}</td>
    <td class="text-end" :class="{'text-success': transaction.transaction_type === 'sell'}">
      {{ transaction.transaction_type === 'sell' ? formatAmount(transaction.total_amount_hkd) : '-' }}
    </td>
    <td class="text-end">{{ formatAmount(transaction.total_fees_hkd) }}</td>
    <td class="text-end">-</td>
    <td class="text-end">-</td>
    <td class="text-end">-</td>
    <td class="text-end">-</td>
    <td class="text-end">-</td>
  </tr>
</template>

<script setup>
const props = defineProps({
  transaction: {
    type: Object,
    required: true
  }
})

// 格式化数字
const formatNumber = (value, decimals = 0) => {
  if (value === null || value === undefined) return '-'
  return Number(value).toLocaleString('zh-HK', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })
}

// 格式化金额
const formatAmount = (value, decimals = 2) => {
  if (value === null || value === undefined) return '-'
  return formatNumber(value, decimals)
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-HK', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}
</script>

<style scoped>
.transaction-row {
  background-color: #fff;
  border-left: 1px dashed #dee2e6;
  font-size: 0.875rem;
}

.transaction-row td {
  padding-top: 0.5rem;
  padding-bottom: 0.5rem;
}

.transaction-header {
  margin-bottom: 0.25rem;
}

.transaction-header small {
  display: inline-block;
  margin-right: 0.5rem;
}

.text-success {
  color: #198754 !important;
}

.text-danger {
  color: #dc3545 !important;
}
</style> 