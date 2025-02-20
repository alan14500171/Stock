<template>
  <div class="card">
    <div class="card-header d-flex justify-content-between align-items-center">
      <h4 class="mb-0">盈利统计</h4>
      <div class="btn-group">
        <button type="button" class="btn btn-sm btn-outline-secondary" @click="toggleSearch">
          <i :class="['bi', searchVisible ? 'bi-chevron-up' : 'bi-search']"></i>
          {{ searchVisible ? '收起' : '搜索' }}
        </button>
        <button type="button" class="btn btn-sm btn-outline-primary" @click="refreshMarketValue" :disabled="loading">
          <i :class="['bi', loading ? 'bi-arrow-clockwise bi-spin' : 'bi-arrow-clockwise']"></i>
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
          <date-input v-model="searchForm.startDate" @update:modelValue="handleStartDateChange" />
        </div>
        <div class="col-md-3">
          <label class="form-label small">结束日期</label>
          <date-input v-model="searchForm.endDate" @update:modelValue="handleEndDateChange" />
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
              <th></th>
              <th>市场</th>
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
            <template v-for="market in getMarkets" :key="market">
              <!-- 市场汇总 -->
              <tr class="market-row">
                <td>
                  <button @click="toggleMarket(market)" class="btn btn-sm btn-outline-primary">
                    <i :class="['bi bi-chevron-right', { 'rotate-90': isMarketExpanded(market) }]"></i>
                  </button>
                </td>
                <td>{{ market }}</td>
                <td class="text-end">-</td>
                <td class="text-end">{{ marketStats[market].transaction_count }}</td>
                <td class="text-end text-danger">{{ formatNumber(marketStats[market].total_buy) }}</td>
                <td class="text-end">-</td>
                <td class="text-end text-success">{{ formatNumber(marketStats[market].total_sell) }}</td>
                <td class="text-end">{{ formatNumber(marketStats[market].total_fees) }}</td>
                <td class="text-end" :class="getProfitClass(marketStats[market].realized_profit)">
                  {{ formatNumber(marketStats[market].realized_profit) }}
                </td>
                <td class="text-end">-</td>
                <td class="text-end">{{ formatNumber(marketStats[market].market_value) }}</td>
                <td class="text-end" :class="getProfitClass(marketStats[market].total_profit)">
                  {{ formatNumber(marketStats[market].total_profit) }}
                </td>
                <td class="text-end" :class="getProfitClass(marketStats[market].profit_rate)">
                  {{ formatRate(marketStats[market].profit_rate) }}
                </td>
              </tr>

              <!-- 持仓股票 -->
              <template v-if="isMarketExpanded(market)">
                <tr class="holding-group-row">
                  <td>
                    <button @click="toggleHoldingGroup(market)" class="btn btn-sm btn-outline-secondary">
                      <i :class="['bi bi-chevron-right', { 'rotate-90': isHoldingGroupExpanded(market) }]"></i>
                    </button>
                  </td>
                  <td colspan="12"><strong>持仓股票</strong></td>
                </tr>

                <template v-if="isHoldingGroupExpanded(market)">
                  <template v-for="stock in getHoldingStocks(market)" :key="stock.code">
                    <tr class="stock-row">
                      <td>
                        <button @click="toggleStock(market, stock.code)" class="btn btn-sm btn-outline-secondary">
                          <i :class="['bi bi-chevron-right', { 'rotate-90': isStockExpanded(market, stock.code) }]"></i>
                        </button>
                      </td>
                      <td>{{ stock.code }} <br> <small class="text-muted">{{ stock.name }}</small></td>
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
                      <td class="text-end" :class="getProfitClass(stock.realized_profit + stock.market_value)">
                        {{ formatNumber(stock.realized_profit + stock.market_value) }}
                      </td>
                      <td class="text-end" :class="getProfitClass(stock.total_buy > 0 ? ((stock.realized_profit + stock.market_value) / stock.total_buy * 100) : 0)">
                        {{ formatRate(stock.total_buy > 0 ? ((stock.realized_profit + stock.market_value) / stock.total_buy * 100) : 0) }}
                      </td>
                    </tr>
                    <!-- 交易明细行 -->
                    <tr v-if="isStockExpanded(market, stock.code)">
                      <td colspan="13" class="p-0">
                        <div class="transaction-details">
                          <table class="table table-sm mb-0">
                            <thead class="table-light">
                              <tr>
                                <th class="transaction-info">交易日期</th>
                                <th class="quantity-price">数量@单价</th>
                                <th class="text-end amount">买入金额</th>
                                <th class="text-end cost">移动加权平均价</th>
                                <th class="text-end amount">卖出金额</th>
                                <th class="text-end fees">费用</th>
                                <th class="text-end profit">盈亏</th>
                                <th class="text-end current-price">盈亏率</th>
                                <th class="text-end holding-value"></th>
                                <th class="text-end total-profit"></th>
                                <th class="text-end profit-rate"></th>
                              </tr>
                            </thead>
                            <tbody>
                              <template v-if="transactionDetails[`${market}-${stock.code}`]">
                                <tr v-for="detail in transactionDetails[`${market}-${stock.code}`]" :key="detail.id">
                                  <td class="transaction-info">
                                    {{ formatDate(detail.transaction_date) }}
                                    <span :class="['transaction-type-badge', detail.transaction_type === 'BUY' ? 'buy' : 'sell']">
                                      {{ detail.transaction_type === 'BUY' ? '买入' : '卖出' }}
                                    </span>
                                    <span class="transaction-code">{{ detail.transaction_code }}</span>
                                  </td>
                                  <td class="quantity-price">
                                    {{ formatNumber(detail.total_quantity, 0) }} @ 
                                    {{ formatNumber(detail.total_amount / detail.total_quantity, 3) }}
                                  </td>
                                  <td class="text-end amount">
                                    {{ detail.transaction_type === 'BUY' ? formatNumber(detail.total_amount) : '' }}
                                  </td>
                                  <td class="text-end cost">
                                    <template v-if="detail.transaction_type === 'BUY'">
                                      {{ formatNumber(detail.current_average_cost, 3) }}
                                    </template>
                                    <template v-else>
                                      {{ formatNumber(detail.sold_average_cost, 3) }}
                                    </template>
                                  </td>
                                  <td class="text-end amount">
                                    {{ detail.transaction_type === 'SELL' ? formatNumber(detail.total_amount) : '' }}
                                  </td>
                                  <td class="text-end fees">
                                    {{ formatNumber(detail.total_fees_hkd) }}
                                  </td>
                                  <td class="text-end" :class="getProfitClass(calculateProfit(detail))">
                                    {{ detail.transaction_type === 'SELL' ? formatNumber(calculateProfit(detail)) : '-' }}
                                  </td>
                                  <td class="text-end" :class="getProfitClass(calculateProfitRate(detail))">
                                    {{ detail.transaction_type === 'SELL' ? formatRate(calculateProfitRate(detail)) : '-' }}
                                  </td>
                                  <td class="text-end">-</td>
                                  <td class="text-end">-</td>
                                  <td class="text-end">-</td>
                                  <td class="text-end">-</td>
                                </tr>
                              </template>
                              <tr v-else>
                                <td colspan="11" class="text-center py-2">
                                  <small class="text-muted">暂无交易明细数据</small>
                                </td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                      </td>
                    </tr>
                  </template>
                </template>

                <!-- 已清仓股票 -->
                <tr class="closed-group-row">
                  <td>
                    <button @click="toggleClosedGroup(market)" class="btn btn-sm btn-outline-secondary">
                      <i :class="['bi bi-chevron-right', { 'rotate-90': isClosedGroupExpanded(market) }]"></i>
                    </button>
                  </td>
                  <td colspan="12"><strong>已清仓股票</strong></td>
                </tr>

                <template v-if="isClosedGroupExpanded(market)">
                  <template v-for="stock in getClosedStocks(market)" :key="stock.code">
                    <tr class="stock-row">
                      <td>
                        <button @click="toggleStock(market, stock.code)" class="btn btn-sm btn-outline-secondary">
                          <i :class="['bi bi-chevron-right', { 'rotate-90': isStockExpanded(market, stock.code) }]"></i>
                        </button>
                      </td>
                      <td>{{ stock.code }} <br> <small class="text-muted">{{ stock.name }}</small></td>
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
                      <td class="text-end" :class="getProfitClass(stock.realized_profit + stock.market_value)">
                        {{ formatNumber(stock.realized_profit + stock.market_value) }}
                      </td>
                      <td class="text-end" :class="getProfitClass(stock.total_buy > 0 ? ((stock.realized_profit + stock.market_value) / stock.total_buy * 100) : 0)">
                        {{ formatRate(stock.total_buy > 0 ? ((stock.realized_profit + stock.market_value) / stock.total_buy * 100) : 0) }}
                      </td>
                    </tr>
                    <!-- 交易明细行 -->
                    <tr v-if="isStockExpanded(market, stock.code)">
                      <td colspan="13" class="p-0">
                        <div class="transaction-details">
                          <table class="table table-sm mb-0">
                            <thead class="table-light">
                              <tr>
                                <th class="transaction-info">交易日期</th>
                                <th class="quantity-price">数量@单价</th>
                                <th class="text-end amount">买入金额</th>
                                <th class="text-end cost">移动加权平均价</th>
                                <th class="text-end amount">卖出金额</th>
                                <th class="text-end fees">费用</th>
                                <th class="text-end profit">盈亏</th>
                                <th class="text-end current-price">盈亏率</th>
                                <th class="text-end holding-value"></th>
                                <th class="text-end total-profit"></th>
                                <th class="text-end profit-rate"></th>
                              </tr>
                            </thead>
                            <tbody>
                              <template v-if="transactionDetails[`${market}-${stock.code}`]">
                                <tr v-for="detail in transactionDetails[`${market}-${stock.code}`]" :key="detail.id">
                                  <td class="transaction-info">
                                    {{ formatDate(detail.transaction_date) }}
                                    <span :class="['transaction-type-badge', detail.transaction_type === 'BUY' ? 'buy' : 'sell']">
                                      {{ detail.transaction_type === 'BUY' ? '买入' : '卖出' }}
                                    </span>
                                    <span class="transaction-code">{{ detail.transaction_code }}</span>
                                  </td>
                                  <td class="quantity-price">
                                    {{ formatNumber(detail.total_quantity, 0) }} @ 
                                    {{ formatNumber(detail.total_amount / detail.total_quantity, 3) }}
                                  </td>
                                  <td class="text-end amount">
                                    {{ detail.transaction_type === 'BUY' ? formatNumber(detail.total_amount) : '' }}
                                  </td>
                                  <td class="text-end cost">
                                    <template v-if="detail.transaction_type === 'BUY'">
                                      {{ formatNumber(detail.current_average_cost, 3) }}
                                    </template>
                                    <template v-else>
                                      {{ formatNumber(detail.sold_average_cost, 3) }}
                                    </template>
                                  </td>
                                  <td class="text-end amount">
                                    {{ detail.transaction_type === 'SELL' ? formatNumber(detail.total_amount) : '' }}
                                  </td>
                                  <td class="text-end fees">
                                    {{ formatNumber(detail.total_fees_hkd) }}
                                  </td>
                                  <td class="text-end" :class="getProfitClass(calculateProfit(detail))">
                                    {{ detail.transaction_type === 'SELL' ? formatNumber(calculateProfit(detail)) : '-' }}
                                  </td>
                                  <td class="text-end" :class="getProfitClass(calculateProfitRate(detail))">
                                    {{ detail.transaction_type === 'SELL' ? formatRate(calculateProfitRate(detail)) : '-' }}
                                  </td>
                                  <td class="text-end">-</td>
                                  <td class="text-end">-</td>
                                  <td class="text-end">-</td>
                                  <td class="text-end">-</td>
                                </tr>
                              </template>
                              <tr v-else>
                                <td colspan="11" class="text-center py-2">
                                  <small class="text-muted">暂无交易明细数据</small>
                                </td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                      </td>
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
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import DateInput from '../components/DateInput.vue'
import axios from 'axios'

const router = useRouter()

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
  const stocks = Object.entries(stockStats.value)
    .filter(([_, stock]) => stock.market === market)
    .map(([code, stock]) => ({ code, ...stock }))
  
  // 按持仓状态和市值排序
  return stocks.sort((a, b) => {
    // 先按持仓状态排序
    if (a.quantity > 0 && b.quantity <= 0) return -1
    if (a.quantity <= 0 && b.quantity > 0) return 1
    // 持仓的按市值排序
    if (a.quantity > 0 && b.quantity > 0) {
      return b.market_value - a.market_value
    }
    // 已清仓的按总盈亏排序
    return b.total_profit - a.total_profit
  })
}

// 获取市场持仓股票
const getHoldingStocks = (market) => {
  return Object.entries(stockStats.value)
    .filter(([_, stock]) => stock.market === market && stock.quantity > 0)
    .map(([code, stock]) => ({ code, ...stock }))
    .sort((a, b) => {
      // 按最新交易日期和创建时间排序
      const aDetails = transactionDetails.value[`${market}-${a.code}`] || [];
      const bDetails = transactionDetails.value[`${market}-${b.code}`] || [];
      const aLatest = aDetails[0] || {};
      const bLatest = bDetails[0] || {};
      
      // 先按交易日期排序
      const dateA = new Date(aLatest.transaction_date || 0);
      const dateB = new Date(bLatest.transaction_date || 0);
      if (dateA.getTime() !== dateB.getTime()) {
        return dateB.getTime() - dateA.getTime();
      }
      // 如果交易日期相同，按创建时间排序
      const createA = new Date(aLatest.created_at || 0);
      const createB = new Date(bLatest.created_at || 0);
      return createB.getTime() - createA.getTime();
    });
}

// 获取市场已清仓股票
const getClosedStocks = (market) => {
  return Object.entries(stockStats.value)
    .filter(([_, stock]) => stock.market === market && stock.quantity <= 0)
    .map(([code, stock]) => ({ code, ...stock }))
    .sort((a, b) => {
      // 按最新交易日期和创建时间排序
      const aDetails = transactionDetails.value[`${market}-${a.code}`] || [];
      const bDetails = transactionDetails.value[`${market}-${b.code}`] || [];
      const aLatest = aDetails[0] || {};
      const bLatest = bDetails[0] || {};
      
      // 先按交易日期排序
      const dateA = new Date(aLatest.transaction_date || 0);
      const dateB = new Date(bLatest.transaction_date || 0);
      if (dateA.getTime() !== dateB.getTime()) {
        return dateB.getTime() - dateA.getTime();
      }
      // 如果交易日期相同，按创建时间排序
      const createA = new Date(aLatest.created_at || 0);
      const createB = new Date(bLatest.created_at || 0);
      return createB.getTime() - createA.getTime();
    });
}

// 获取市场列表（按名称排序）
const getMarkets = computed(() => {
  return Object.keys(marketStats.value).sort();
});

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

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).replace(/\//g, '-')
}

const getProfitClass = (value) => {
  if (!value) return ''
  return value > 0 ? 'text-success' : value < 0 ? 'text-danger' : ''
}

// 展开/收起控制
const isMarketExpanded = (market) => expandedMarkets.value.has(market)
const isHoldingGroupExpanded = (market) => expandedHoldingGroups.value.has(market)
const isClosedGroupExpanded = (market) => expandedClosedGroups.value.has(market)
const isStockExpanded = (market, code) => {
  const stockKey = `${market}-${code}`
  return expandedStocks.value.has(stockKey)
}

const toggleMarket = (market) => {
  if (expandedMarkets.value.has(market)) {
    expandedMarkets.value.delete(market)
    expandedHoldingGroups.value.delete(market)
    expandedClosedGroups.value.delete(market)
  } else {
    expandedMarkets.value.add(market)
    expandedHoldingGroups.value.add(market)
    expandedClosedGroups.value.add(market)
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

const toggleStock = (market, code) => {
  const stockKey = `${market}-${code}`
  if (expandedStocks.value.has(stockKey)) {
    expandedStocks.value.delete(stockKey)
  } else {
    expandedStocks.value.add(stockKey)
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
    params.append('details', 'true')
    
    const response = await axios.get('/api/profit/', { params })
    if (response.data.success) {
      marketStats.value = response.data.data.market_stats
      stockStats.value = response.data.data.stock_stats
      
      // 处理交易明细数据，对每个股票的交易记录进行排序
      const rawTransactionDetails = response.data.data.transaction_details || {}
      transactionDetails.value = Object.fromEntries(
        Object.entries(rawTransactionDetails).map(([key, details]) => [
          key,
          processTransactionDetails(details)
        ])
      )
      
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
    const response = await axios.post('/api/stock/stocks/update-prices')
    if (response.data.success) {
      search()
    }
  } catch (error) {
    console.error('刷新市值失败:', error)
  } finally {
    loading.value = false
  }
}

const addTransaction = () => {
  router.push('/transactions/add')
}

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

// 处理后端返回的数据
const processTransactionDetails = (details) => {
  if (!details) return [];
  // 对交易明细按日期和创建时间降序排序
  return [...details].sort((a, b) => {
    // 先按交易日期排序
    const dateA = new Date(a.transaction_date);
    const dateB = new Date(b.transaction_date);
    if (dateA.getTime() !== dateB.getTime()) {
      return dateB.getTime() - dateA.getTime();
    }
    // 如果交易日期相同，按创建时间排序
    const createA = new Date(a.created_at || 0);
    const createB = new Date(b.created_at || 0);
    return createB.getTime() - createA.getTime();
  });
}

// 在 script setup 部分添加计算函数
const calculateHKDAmount = (detail) => {
  return detail.total_amount * detail.exchange_rate;
}

const calculateProfit = (detail) => {
  if (detail.transaction_type !== 'SELL') return 0;
  // 卖出盈亏 = 卖出金额 - (卖出数量 * 卖出时移动加权平均价) - 卖出费用
  const sellAmount = detail.total_amount;
  const costAmount = detail.total_quantity * detail.sold_average_cost;
  const fees = detail.total_fees_hkd;
  return Number((sellAmount - costAmount - fees).toFixed(2));  // 保留两位小数
}

// 在 script setup 部分添加计算盈亏率函数
const calculateProfitRate = (detail) => {
  if (detail.transaction_type !== 'SELL') return 0;
  const profit = calculateProfit(detail);
  const costAmount = detail.total_quantity * detail.sold_average_cost;
  return costAmount > 0 ? (profit / costAmount * 100) : 0;
}

// 初始化
onMounted(() => {
  search()
})
</script>

<style scoped>
.market-row {
  background-color: #f8f9fa;
}

.holding-group-row,
.closed-group-row {
  background-color: #f8f9fa;
}

.stock-row {
  background-color: #ffffff;
}

.stock-row:hover {
  background-color: #f8f9fa;
}

/* 层级缩进样式 */
/* 第一层级 - 市场行 */
.market-row td:first-child {
  padding-left: 0.1rem !important;
  position: relative;
  width: 40px;
}

/* 第二层级 - 持仓/已清仓分组 */
.holding-group-row td:first-child,
.closed-group-row td:first-child {
  padding-left: 0.5rem !important;
  position: relative;
  width: 40px;
}

.holding-group-row td:nth-child(2),
.closed-group-row td:nth-child(2) {
  padding-left: 2rem !important;/* 第二层级 - 修改缩进*/
}

/* 第三层级 - 股票行 */
.stock-row td:first-child {
  padding-left: 0.5rem !important;
  position: relative;
  width: 40px;
}

.stock-row td:nth-child(2) {
  padding-left: 1rem !important;/* 第三层级 - 修改缩进*/
}

/* 第四层级 - 交易明细 */
.transaction-details {
  padding-left: 5rem !important; /* 第四层级 - 修改缩进*/
  background-color: #ffffff;
  padding: 0.5rem;
  font-size: 0.75rem;  /* 12px */
}

.transaction-details .table {
  background-color: white;
  margin-bottom: 0;
}

.transaction-details th,
.transaction-details td {
  padding: 0.4rem 0.5rem;
  font-size: 0.75rem;  /* 12px */
  white-space: nowrap;
}

.transaction-details th {
  background-color: #f1f3f5;
  font-weight: 500;
  color: #495057;
}

.transaction-details td {
  vertical-align: middle;
}

.transaction-details tr:hover {
  background-color: #f8f9fa;
}

/* 交易明细列宽 持仓股票*/
.transaction-details .transaction-info {
  min-width: 50px;
  font-size: 0.75rem;  /* 12px */
}

.transaction-details .quantity-price {
  min-width: 60px;
  font-size: 0.75rem;  /* 12px */
}

.transaction-details .amount {
  min-width: 100px;
  font-size: 12px;
}

.transaction-details .cost {
  min-width: 80px;
  font-size: 12px;
}

.transaction-details .fees {
  min-width: 80px;
  font-size: 12px;
}

.transaction-details .profit {
  min-width: 80px;
  font-size: 12px;
}

.transaction-details .current-price {
  min-width: 100px;
  font-size: 12px;
}

.transaction-details .holding-value {
  min-width: 100px;
  font-size: 12px;
}

.transaction-details .total-profit {
  min-width: 100px;
  font-size: 12px;
}

.transaction-details .profit-rate {
  min-width: 100px;
  font-size: 12px;
}











/* 交易类型标签样式 */
.transaction-type-badge {
  display: inline-block;
  width: 30px;
  height: 16px;
  line-height: 15px;
  text-align: center;
  border-radius: 4px;
  font-size: 0.75rem;  /* 12px */
  font-weight: 450;
  margin: 0 6px;
}

.transaction-type-badge.buy {
  background-color: #e6071d;
  color: #ffffff;
}

.transaction-type-badge.sell {
  background-color: #549359;
  color: #ffffff;
}

.transaction-code {
  font-size: 0.675rem;  /* 14px */
  color: #6c757d;
  margin-left: 4px;
}

/* 按钮样式 */
.btn-sm {
  padding: 0.25rem 0.5rem;
  min-width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: #495057;
  transition: all 0.2s;
  margin: 2px;
  position: relative;
}

.btn-sm:hover {
  background: transparent;
}

.btn-sm:focus {
  box-shadow: none;
  outline: none;
}

.btn-sm .bi {
  font-size: 18px;
  width: 18px;
  height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease-in-out;
  position: relative;
  z-index: 2;
  font-weight: bold;
  stroke-width: 1px;
}

.rotate-90 {
  transform: rotate(90deg);
  color: #0d6efd !important;
}

/* 市场行按钮样式 */
.market-row .btn-sm {
  background: transparent;
  border: none;
}

.market-row .btn-sm .bi {
  font-size: 20px;
  width: 20px;
  height: 20px;
  font-weight: bold;
  transition: all 0.2s ease-in-out;
}

.market-row .btn-sm .bi-chevron-right {
  color: #495057;
}

/* 分组行按钮样式 */
.holding-group-row .btn-sm,
.closed-group-row .btn-sm {
  background: transparent;
  border: none;
  transform: translateX(0.8rem);
}

.holding-group-row .btn-sm .bi,
.closed-group-row .btn-sm .bi {
  font-size: 18px;
  width: 18px;
  height: 18px;
  font-weight: bold;
  transition: all 0.2s ease-in-out;
}

.holding-group-row .btn-sm .bi-chevron-right,
.closed-group-row .btn-sm .bi-chevron-right {
  color: #495057;
}

/* 股票行按钮样式 */
.stock-row .btn-sm {
  background: transparent;
  border: none;
  transform: translateX(1.2rem);
}

.stock-row .btn-sm .bi {
  font-size: 16px;
  width: 16px;
  height: 16px;
  font-weight: bold;
  transition: all 0.2s ease-in-out;
}

.stock-row .btn-sm .bi-chevron-right {
  color: #495057;
}

/* 按钮悬停效果 */
.btn-sm:hover .bi-chevron-right {
  color: #0d6efd;
}

.btn-sm:hover .rotate-90 {
  color: #0a58ca !important;
}

/* 交易明细表格样式 */
.transaction-details {
  background-color: #ffffff;
  padding: 0.5rem;
}

.transaction-details .table {
  margin-bottom: 0;
}

.transaction-details td {
  background-color: #ffffff;
  padding: 0.25rem 0.5rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  border-bottom: 1px solid #dee2e6;
  line-height: 1.2;
  vertical-align: middle;
  font-size: 12px;
}

.transaction-details tr:last-child td {
  border-bottom: none;
}

/* 交易明细行悬停效果 */
.transaction-details tr {
  transition: background-color 0.2s;
  height: 8px;
}

.transaction-details tr:hover td {
  background-color: #f8f9fa;
}

.transaction-details tr.selected td {
  background-color: #e9ecef;
}

/* 旋转动画 */
@keyframes bi-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.bi-spin {
  display: inline-block;
  animation: bi-spin 1s linear infinite;
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

.small {
  font-size: 0.875rem;
}

/* 交易类型徽章样式 */
.transaction-type-badge {
  display: inline-block;
  width: 30px;
  height: 16px;
  line-height: 15px;
  text-align: center;
  border-radius: 4px;
  font-size: 0.75rem;  /* 12px */
  font-weight: 450;
  margin: 0 6px;
}

.transaction-type-badge.buy {
  background-color: #e6071d;
  color: #ffffff;
}

.transaction-type-badge.sell {
  background-color: #549359;
  color: #ffffff;
}

/* 交易编号样式 */
.transaction-code {
  font-size: 0.675rem;  /* 14px */
  color: #6c757d;
  margin-left: 4px;
}

/* 交易信息列样式 */
.transaction-info {
  min-width: 180px;
  font-size: 0.75rem;  /* 12px */
}

/* 数量@单价列样式 */
.quantity-price {
  min-width: 60px;
  padding-left: 1rem !important;
  text-align: left !important;
  font-size: 12px;
}

/* 金额列样式 */
.amount {
  min-width: 100px;
  font-size: 12px;
}

/* 单笔成本列样式 */
.cost {
  min-width: 80px;
  font-size: 12px;
}

/* 费用列样式 */
.fees {
  min-width: 80px;
  font-size: 12px;
}

.profit {
  min-width: 80px;
  font-size: 12px;
} 

.current-price {
  min-width: 100px;
  font-size: 12px;
} 

.holding-value {
  min-width: 100px;
  font-size: 12px;
} 

.total-profit {
  min-width: 100px;
  font-size: 12px;
}  

.profit-rate {
  min-width: 100px;
  font-size: 12px;
}  
</style> 
