<template>
  <div class="card">
    <div class="card-header d-flex justify-content-between align-items-center">
      <h4 class="mb-0">盈利统计</h4>
      <div class="btn-group">
        <button type="button" class="btn btn-sm btn-outline-secondary" @click="toggleSearch">
          <i :class="['fas', searchVisible ? 'fa-chevron-up' : 'fa-search']"></i>
          {{ searchVisible ? '收起' : '搜索' }}
        </button>
        <button type="button" class="btn btn-sm btn-outline-secondary" @click="refreshMarketValue" :disabled="loading">
          <i :class="['fas', loading ? 'fa-spinner fa-spin' : 'fa-sync-alt']"></i>
          刷新市值
        </button>
        <button type="button" class="btn btn-sm btn-outline-secondary" @click="expandAll">
          <i class="fas fa-expand"></i> 展开
        </button>
        <button type="button" class="btn btn-sm btn-outline-secondary" @click="collapseAll">
          <i class="fas fa-compress"></i> 收起
        </button>
        <router-link to="/transactions/add" class="btn btn-sm btn-primary">
          <i class="fas fa-plus"></i> 添加记录
        </router-link>
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
            <i class="fas fa-search"></i> 搜索
          </button>
        </div>
        <div class="col-md-2 d-flex align-items-end">
          <button type="button" class="btn btn-sm btn-outline-secondary w-100" @click="resetSearch">
            <i class="fas fa-undo"></i> 重置
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
              <th>市场</th>
              <th>代码</th>
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
              <tr class="market-row">
                <td>
                  <button class="btn btn-sm btn-link p-0" @click="toggleMarket(market)">
                    <i :class="['fas', isMarketExpanded(market) ? 'fa-chevron-down' : 'fa-chevron-right']"></i>
                  </button>
                </td>
                <td>{{ market }}</td>
                <td>市场汇总</td>
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

              <!-- 股票明细行 -->
              <template v-if="isMarketExpanded(market)">
                <tr v-for="stock in getMarketStocks(market)" :key="stock.code" class="stock-row">
                  <td></td>
                  <td></td>
                  <td>
                    {{ stock.code }}
                    <br v-if="stock.name">
                    <small class="text-muted">{{ stock.name }}</small>
                  </td>
                  <td class="text-end fw-bold">{{ stock.quantity || '-' }}</td>
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
              </template>
            </template>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import axios from 'axios'
import DateInput from '../components/DateInput.vue'

// 状态
const loading = ref(false)
const searchVisible = ref(false)
const expandedMarkets = ref(new Set())
const marketStats = ref({})
const stockStats = ref({})

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
    .sort((a, b) => b.market_value - a.market_value)
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
  return value.toFixed(1) + '%'
}

const getProfitClass = (value) => {
  if (!value) return ''
  return value > 0 ? 'text-success' : value < 0 ? 'text-danger' : ''
}

// 展开/收起控制
const isMarketExpanded = (market) => expandedMarkets.value.has(market)

const toggleMarket = (market) => {
  if (expandedMarkets.value.has(market)) {
    expandedMarkets.value.delete(market)
  } else {
    expandedMarkets.value.add(market)
  }
}

const expandAll = () => {
  Object.keys(marketStats.value).forEach(market => {
    expandedMarkets.value.add(market)
  })
}

const collapseAll = () => {
  expandedMarkets.value.clear()
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
search()
</script>

<style scoped>
.market-row {
  background-color: #f8f9fa;
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

.table th {
  white-space: nowrap;
  font-size: 0.875rem;
}

.table td {
  font-size: 0.875rem;
}

.table .market-row {
  font-weight: 500;
}

.small {
  font-size: 0.875rem;
}
</style> 