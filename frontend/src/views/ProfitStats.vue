<template>
  <div class="card">
    <div class="card-header d-flex justify-content-between align-items-center">
      <h4 class="mb-0">盈利统计</h4>
      <div class="btn-group">
        <button type="button" class="btn btn-sm btn-outline-secondary" @click="toggleSearch">
          <i class="bi bi-search"></i>
          搜索
        </button>
        <button type="button" class="btn btn-sm btn-outline-secondary" @click="refreshMarketValue" :disabled="loading">
          <i :class="['bi', loading ? 'bi-arrow-clockwise' : 'bi-arrow-repeat']"></i>
          刷新市值
        </button>
        <button type="button" class="btn btn-sm btn-primary" @click="addTransaction">
          <i class="bi bi-plus-lg"></i>
          添加记录
        </button>
      </div>
    </div>

    <!-- 搜索表单 -->
    <div v-show="searchVisible" class="card-body border-bottom">
      <form @submit.prevent="search" class="row g-3">
        <div class="col-md-3">
          <label class="form-label small">开始日期</label>
          <date-input v-model="searchForm.startDate" />
        </div>
        <div class="col-md-3">
          <label class="form-label small">结束日期</label>
          <date-input v-model="searchForm.endDate" />
        </div>
        <div class="col-md-2">
          <label class="form-label small">市场</label>
          <select class="form-select form-select-sm" v-model="searchForm.market">
            <option value="">全部</option>
            <option value="HK">HK</option>
            <option value="USA">USA</option>
          </select>
        </div>
        <div class="col-md-2 d-flex align-items-end">
          <button type="submit" class="btn btn-sm btn-primary w-100" :disabled="loading">
            <i class="bi bi-search"></i> 搜索
          </button>
        </div>
        <div class="col-md-2 d-flex align-items-end">
          <button type="button" class="btn btn-sm btn-outline-secondary w-100" @click="resetSearch">
            <i class="bi bi-arrow-counterclockwise"></i> 重置
          </button>
        </div>
      </form>
    </div>

    <div class="card-body p-0">
      <div class="table-responsive">
        <table class="table table-hover table-sm mb-0">
          <thead class="table-light">
            <tr>
              <th style="width: 30px"></th>
              <th>名称</th>
              <th class="text-end">数量</th>
              <th class="text-end">笔数</th>
              <th class="text-end">买入总额</th>
              <th class="text-end">平均价格</th>
              <th class="text-end">卖出总额</th>
              <th class="text-end">费用</th>
              <th class="text-end">已实现盈亏</th>
              <th class="text-end">现价</th>
              <th class="text-end">持仓价值</th>
              <th class="text-end">总盈亏</th>
              <th class="text-end">盈亏率</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="(marketData, market) in marketStats" :key="market">
              <!-- 市场汇总行 -->
              <tr class="market-row" @click="toggleMarket(market)">
                <td class="text-center">
                  <i :class="['bi', isMarketExpanded(market) ? 'bi-chevron-down' : 'bi-chevron-right']"></i>
                </td>
                <td>{{ market }}</td>
                <td class="text-end">-</td>
                <td class="text-end">{{ marketData.transaction_count }}</td>
                <td class="text-end text-danger">{{ formatNumber(marketData.total_buy) }}</td>
                <td class="text-end">-</td>
                <td class="text-end text-success">{{ formatNumber(marketData.total_sell) }}</td>
                <td class="text-end">{{ formatNumber(marketData.total_fees) }}</td>
                <td class="text-end" :class="getProfitClass(marketData.realized_profit)">
                  {{ formatNumber(marketData.realized_profit) }}
                </td>
                <td class="text-end">-</td>
                <td class="text-end">{{ formatNumber(marketData.market_value) }}</td>
                <td class="text-end" :class="getProfitClass(marketData.total_profit)">
                  {{ formatNumber(marketData.total_profit) }}
                </td>
                <td class="text-end" :class="getProfitClass(marketData.profit_rate)">
                  {{ formatRate(marketData.profit_rate) }}
                </td>
              </tr>

              <template v-if="isMarketExpanded(market)">
                <!-- 持仓股票组 -->
                <tr class="group-row holding-group" @click="toggleHoldingGroup(market)">
                  <td class="text-center">
                    <i :class="['bi', isHoldingGroupExpanded(market) ? 'bi-chevron-down' : 'bi-chevron-right']"></i>
                  </td>
                  <td colspan="12">
                    <i class="bi bi-graph-up text-success"></i>
                    持仓股票
                  </td>
                </tr>

                <!-- 持仓股票列表 -->
                <template v-if="isHoldingGroupExpanded(market)" v-for="stock in getHoldingStocks(market)" :key="stock.code">
                  <tr class="stock-row holding-stock" @click="toggleStock(market, stock.code)">
                    <td class="text-center">
                      <i :class="['bi', isStockExpanded(`${market}-${stock.code}`) ? 'bi-chevron-down' : 'bi-chevron-right']"></i>
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
                    <td class="text-end">{{ formatNumber(stock.current_price, 3) }}</td>
                    <td class="text-end">{{ formatNumber(stock.market_value) }}</td>
                    <td class="text-end" :class="getProfitClass(stock.total_profit)">
                      {{ formatNumber(stock.total_profit) }}
                    </td>
                    <td class="text-end" :class="getProfitClass(stock.profit_rate)">
                      {{ formatRate(stock.profit_rate) }}
                    </td>
                  </tr>

                  <!-- 交易明细行 -->
                  <template v-if="isStockExpanded(`${market}-${stock.code}`) && transactionDetails[`${market}-${stock.code}`]">
                    <tr v-for="transaction in transactionDetails[`${market}-${stock.code}`]" 
                        :key="transaction.id" 
                        class="transaction-row">
                      <td></td>
                      <td>
                        <small class="text-muted">{{ transaction.transaction_date }}</small>
                        <br>
                        <small>{{ transaction.transaction_code }}</small>
                      </td>
                      <td class="text-end">{{ transaction.transaction_type === 'buy' ? transaction.total_quantity : -transaction.total_quantity }}</td>
                      <td class="text-end">-</td>
                      <td class="text-end" :class="{'text-danger': transaction.transaction_type === 'buy'}">
                        {{ transaction.transaction_type === 'buy' ? formatNumber(transaction.total_amount) : '-' }}
                      </td>
                      <td class="text-end">{{ formatNumber(transaction.total_amount / transaction.total_quantity, 3) }}</td>
                      <td class="text-end" :class="{'text-success': transaction.transaction_type === 'sell'}">
                        {{ transaction.transaction_type === 'sell' ? formatNumber(transaction.total_amount) : '-' }}
                      </td>
                      <td class="text-end">{{ formatNumber(transaction.total_fees) }}</td>
                      <td class="text-end">-</td>
                      <td class="text-end">-</td>
                      <td class="text-end">-</td>
                      <td class="text-end">-</td>
                      <td class="text-end">-</td>
                    </tr>
                  </template>
                </template>

                <!-- 已清仓股票组 -->
                <tr class="group-row closed-group" @click="toggleClosedGroup(market)">
                  <td class="text-center">
                    <i :class="['bi', isClosedGroupExpanded(market) ? 'bi-chevron-down' : 'bi-chevron-right']"></i>
                  </td>
                  <td colspan="12">
                    <i class="bi bi-check-circle text-secondary"></i>
                    已清仓股票
                  </td>
                </tr>

                <!-- 已清仓股票列表 -->
                <template v-if="isClosedGroupExpanded(market)" v-for="stock in getClosedStocks(market)" :key="stock.code">
                  <tr class="stock-row closed-stock" @click="toggleStock(market, stock.code)">
                    <td class="text-center">
                      <i :class="['bi', isStockExpanded(`${market}-${stock.code}`) ? 'bi-chevron-down' : 'bi-chevron-right']"></i>
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
                    <td class="text-end">{{ formatNumber(stock.current_price, 3) }}</td>
                    <td class="text-end">{{ formatNumber(stock.market_value) }}</td>
                    <td class="text-end" :class="getProfitClass(stock.total_profit)">
                      {{ formatNumber(stock.total_profit) }}
                    </td>
                    <td class="text-end" :class="getProfitClass(stock.profit_rate)">
                      {{ formatRate(stock.profit_rate) }}
                    </td>
                  </tr>

                  <!-- 交易明细行 -->
                  <template v-if="isStockExpanded(`${market}-${stock.code}`) && transactionDetails[`${market}-${stock.code}`]">
                    <tr v-for="transaction in transactionDetails[`${market}-${stock.code}`]" 
                        :key="transaction.id" 
                        class="transaction-row">
                      <td></td>
                      <td>
                        <small class="text-muted">{{ transaction.transaction_date }}</small>
                        <br>
                        <small>{{ transaction.transaction_code }}</small>
                      </td>
                      <td class="text-end">{{ transaction.transaction_type === 'buy' ? transaction.total_quantity : -transaction.total_quantity }}</td>
                      <td class="text-end">-</td>
                      <td class="text-end" :class="{'text-danger': transaction.transaction_type === 'buy'}">
                        {{ transaction.transaction_type === 'buy' ? formatNumber(transaction.total_amount) : '-' }}
                      </td>
                      <td class="text-end">{{ formatNumber(transaction.total_amount / transaction.total_quantity, 3) }}</td>
                      <td class="text-end" :class="{'text-success': transaction.transaction_type === 'sell'}">
                        {{ transaction.transaction_type === 'sell' ? formatNumber(transaction.total_amount) : '-' }}
                      </td>
                      <td class="text-end">{{ formatNumber(transaction.total_fees) }}</td>
                      <td class="text-end">-</td>
                      <td class="text-end">-</td>
                      <td class="text-end">-</td>
                      <td class="text-end">-</td>
                      <td class="text-end">-</td>
                    </tr>
                  </template>
                </template>
              </template>
            </template>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import DateInput from '../components/DateInput.vue'
import axios from 'axios'

// 状态管理
const loading = ref(false)
const searchVisible = ref(false)
const expandedMarkets = ref(new Set())
const expandedHoldingGroups = ref(new Set())
const expandedClosedGroups = ref(new Set())
const expandedStocks = ref(new Set())
const marketStats = ref({})
const stockStats = ref({})
const transactionDetails = ref({})

// 搜索表单
const searchForm = reactive({
  startDate: '',
  endDate: '',
  market: ''
})

// 计算属性
const getMarketStocks = (market) => {
  return Object.entries(stockStats.value)
    .filter(([_, stock]) => stock.market === market)
    .map(([code, stock]) => ({ code, ...stock }))
    .sort((a, b) => b.total_buy - a.total_buy)
}

const getHoldingStocks = (market) => {
  return Object.entries(stockStats.value)
    .filter(([_, stock]) => stock.market === market && stock.quantity > 0)
    .map(([code, stock]) => ({ code, ...stock }))
    .sort((a, b) => b.market_value - a.market_value)
}

const getClosedStocks = (market) => {
  return Object.entries(stockStats.value)
    .filter(([_, stock]) => stock.market === market && (!stock.quantity || stock.quantity <= 0))
    .map(([code, stock]) => ({ code, ...stock }))
    .sort((a, b) => b.total_profit - a.total_profit)
}

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
  return value.toFixed(2) + '%'
}

const getProfitClass = (value) => {
  if (!value) return ''
  return value > 0 ? 'text-success' : value < 0 ? 'text-danger' : ''
}

// 展开/收起控制
const isMarketExpanded = (market) => expandedMarkets.value.has(market)
const isHoldingGroupExpanded = (market) => expandedHoldingGroups.value.has(market)
const isClosedGroupExpanded = (market) => expandedClosedGroups.value.has(market)
const isStockExpanded = (stockKey) => expandedStocks.value.has(stockKey)

const toggleMarket = (market) => {
  if (expandedMarkets.value.has(market)) {
    expandedMarkets.value.delete(market)
  } else {
    expandedMarkets.value.add(market)
  }
}

const toggleHoldingGroup = (market) => {
  if (expandedHoldingGroups.value.has(market)) {
    expandedHoldingGroups.value.delete(market)
  } else {
    expandedHoldingGroups.value.add(market)
  }
}

const toggleClosedGroup = (market) => {
  if (expandedClosedGroups.value.has(market)) {
    expandedClosedGroups.value.delete(market)
  } else {
    expandedClosedGroups.value.add(market)
  }
}

const toggleStock = async (market, code) => {
  const stockKey = `${market}-${code}`
  if (expandedStocks.value.has(stockKey)) {
    expandedStocks.value.delete(stockKey)
  } else {
    expandedStocks.value.add(stockKey)
    // 获取交易明细
    await loadTransactionDetails(market, code)
  }
}

const loadTransactionDetails = async (market, code) => {
  const stockKey = `${market}-${code}`
  if (transactionDetails.value[stockKey]) return

  try {
    loading.value = true
    const response = await axios.get(`/api/stock/transactions`, {
      params: {
        market,
        stock_code: code,
        start_date: searchForm.startDate,
        end_date: searchForm.endDate
      }
    })
    if (response.data.success) {
      transactionDetails.value[stockKey] = response.data.data.items
    }
  } catch (error) {
    console.error('获取交易明细失败:', error)
  } finally {
    loading.value = false
  }
}

const expandAll = () => {
  Object.keys(marketStats.value).forEach(market => {
    expandedMarkets.value.add(market)
    expandedHoldingGroups.value.add(market)
    expandedClosedGroups.value.add(market)
  })
}

const collapseAll = () => {
  expandedMarkets.value.clear()
  expandedHoldingGroups.value.clear()
  expandedClosedGroups.value.clear()
}

// 搜索相关
const toggleSearch = () => {
  searchVisible.value = !searchVisible.value
}

const search = async () => {
  if (loading.value) return
  
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (searchForm.startDate) params.append('start_date', searchForm.startDate)
    if (searchForm.endDate) params.append('end_date', searchForm.endDate)
    if (searchForm.market) params.append('market', searchForm.market)
    
    const response = await axios.get(`/api/profit?${params.toString()}`)
    if (response.data.success) {
      marketStats.value = response.data.data.market_stats
      stockStats.value = response.data.data.stock_stats
      // 默认展开所有市场
      expandAll()
    }
  } catch (error) {
    console.error('获取数据失败:', error)
  } finally {
    loading.value = false
  }
}

const resetSearch = () => {
  searchForm.startDate = ''
  searchForm.endDate = ''
  searchForm.market = ''
  search()
}

const refreshMarketValue = async () => {
  if (loading.value) return
  
  loading.value = true
  try {
    const response = await axios.get('/api/portfolio/market-value')
    if (response.data.success) {
      // 刷新数据
      search()
    }
  } catch (error) {
    console.error('刷新市值失败:', error)
  } finally {
    loading.value = false
  }
}

// 初始化
onMounted(() => {
  search()
})

// 日期变更处理
const handleStartDateChange = (value) => {
  searchForm.startDate = value
  if (searchForm.endDate && value > searchForm.endDate) {
    searchForm.endDate = value
  }
}

const handleEndDateChange = (value) => {
  searchForm.endDate = value
  if (searchForm.startDate && value < searchForm.startDate) {
    searchForm.startDate = value
  }
}

// 刷新数据
const refreshData = () => {
  search()
}
</script>

<style scoped>
.market-row {
  background-color: #f8f9fa;
  cursor: pointer;
}

.group-row {
  background-color: #fff;
  cursor: pointer;
  font-weight: 500;
}

.group-row td {
  padding: 0.5rem 1rem;
  color: #6c757d;
}

.group-row i {
  margin-right: 0.5rem;
}

.holding-group {
  border-left: 4px solid #198754;
}

.closed-group {
  border-left: 4px solid #6c757d;
}

.holding-stock {
  border-left: 4px solid #198754;
  cursor: pointer;
  padding-left: 2rem;
}

.closed-stock {
  border-left: 4px solid #6c757d;
  cursor: pointer;
  padding-left: 2rem;
}

.transaction-row {
  background-color: #fafafa;
  font-size: 0.875rem;
}

.transaction-row td {
  border-top: 1px dashed #dee2e6;
  padding-top: 0.4rem;
  padding-bottom: 0.4rem;
  padding-left: 3rem;
}

.text-success {
  color: #198754 !important;
}

.text-danger {
  color: #dc3545 !important;
}

.table th {
  white-space: nowrap;
  font-size: 0.875rem;
}

.table td {
  font-size: 0.875rem;
  vertical-align: middle;
}

.table .market-row {
  font-weight: 500;
}

.small {
  font-size: 0.875rem;
}

.stock-row:hover, .market-row:hover, .group-row:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.stock-row td {
  padding-left: 2rem;
}

.stock-row small {
  font-size: 0.75rem;
}

.transaction-row:hover {
  background-color: #f5f5f5;
}
</style> 