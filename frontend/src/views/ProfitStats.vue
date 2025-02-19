<template>
  <div class="card">
    <div class="card-header d-flex justify-content-between align-items-center">
      <h4 class="mb-0">盈利统计</h4>
      <div class="btn-group">
        <button type="button" class="btn btn-sm btn-outline-secondary" @click="toggleSearch">
          <i :class="['fas', searchVisible ? 'fa-chevron-up' : 'fa-search']"></i>
          {{ searchVisible ? '收起' : '搜索' }}
        </button>
        <button type="button" class="btn btn-sm btn-outline-secondary" @click="refreshData" :disabled="loading">
          <i :class="['fas', loading ? 'fa-spinner fa-spin' : 'fa-sync-alt']"></i>
          刷新市值
        </button>
      </div>
    </div>

    <!-- 搜索表单 -->
    <div v-show="searchVisible" class="card-body border-bottom">
      <form @submit.prevent="search" class="row g-3">
        <div class="col-md-3">
          <label class="form-label small">开始日期</label>
          <date-input
            v-model="searchForm.startDate"
            placeholder="开始日期"
            @update:modelValue="handleStartDateChange"
          />
        </div>
        <div class="col-md-3">
          <label class="form-label small">结束日期</label>
          <date-input
            v-model="searchForm.endDate"
            placeholder="结束日期"
            @update:modelValue="handleEndDateChange"
          />
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
          <button type="submit" class="btn btn-sm btn-primary w-100" :disabled="loading">查询</button>
        </div>
        <div class="col-md-2 d-flex align-items-end">
          <button type="button" class="btn btn-sm btn-outline-secondary w-100" @click="resetSearch">重置</button>
        </div>
      </form>
    </div>

    <!-- 统计数据表格 -->
    <div class="card-body p-0">
      <div class="table-responsive">
        <table class="table table-hover mb-0">
          <thead class="table-light">
            <tr>
              <th>市场</th>
              <th>代码</th>
              <th class="text-end">数量</th>
              <th class="text-end">买入总额</th>
              <th class="text-end">平均成本</th>
              <th class="text-end">卖出总额</th>
              <th class="text-end">费用</th>
              <th class="text-end">已实现盈亏</th>
              <th class="text-end">当前价格</th>
              <th class="text-end">市值</th>
              <th class="text-end">总盈亏</th>
              <th class="text-end">盈亏率</th>
            </tr>
          </thead>
          <tbody>
            <template v-if="!loading">
              <!-- 市场汇总行 -->
              <tr v-for="(stats, market) in marketStats" :key="market" class="table-light fw-bold">
                <td>{{ market }}</td>
                <td>市场汇总</td>
                <td class="text-end">-</td>
                <td class="text-end text-danger">{{ formatNumber(stats.total_buy) }}</td>
                <td class="text-end">-</td>
                <td class="text-end text-success">{{ formatNumber(stats.total_sell) }}</td>
                <td class="text-end">{{ formatNumber(stats.total_fees) }}</td>
                <td class="text-end" :class="getProfitClass(stats.realized_profit)">
                  {{ formatNumber(stats.realized_profit) }}
                </td>
                <td class="text-end">-</td>
                <td class="text-end">{{ formatNumber(stats.market_value) }}</td>
                <td class="text-end" :class="getProfitClass(stats.total_profit)">
                  {{ formatNumber(stats.total_profit) }}
                </td>
                <td class="text-end" :class="getProfitClass(stats.profit_rate)">
                  {{ formatRate(stats.profit_rate) }}
                </td>
              </tr>

              <!-- 股票明细行 -->
              <template v-for="(stock, code) in stockStats" :key="code">
                <tr>
                  <td>{{ stock.market }}</td>
                  <td>
                    {{ code }}
                    <br>
                    <small class="text-muted">{{ stock.name }}</small>
                  </td>
                  <td class="text-end">{{ stock.quantity }}</td>
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
            <tr v-else>
              <td colspan="12" class="text-center py-3">
                <div class="spinner-border spinner-border-sm text-primary me-2"></div>
                加载中...
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <!-- 添加调试信息 -->
      <div v-if="!loading && (!Object.keys(marketStats).length || !Object.keys(stockStats).length)" 
           class="text-center py-4">
        <p class="text-muted mb-2">暂无数据</p>
        <small class="d-block text-muted">Market Stats: {{ Object.keys(marketStats).length }}</small>
        <small class="d-block text-muted">Stock Stats: {{ Object.keys(stockStats).length }}</small>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import DateInput from '../components/DateInput.vue'
import StockSelector from '../components/StockSelector.vue'
import axios from 'axios'

// 状态
const loading = ref(false)
const searchVisible = ref(false)
const marketStats = ref({})
const stockStats = ref({})

// 搜索表单
const searchForm = reactive({
  startDate: '',
  endDate: '',
  market: ''
})

// 格式化数字
const formatNumber = (value, decimals = 2) => {
  if (value === null || value === undefined) return '-'
  return Number(value).toLocaleString('zh-HK', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })
}

// 格式化收益率
const formatRate = (value) => {
  if (value === null || value === undefined) return '-'
  return value.toFixed(1) + '%'
}

// 获取盈亏样式
const getProfitClass = (value) => {
  if (value > 0) return 'text-success'
  if (value < 0) return 'text-danger'
  return ''
}

// 切换搜索面板
const toggleSearch = () => {
  searchVisible.value = !searchVisible.value
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

// 获取数据
const fetchData = async () => {
  if (loading.value) return
  
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (searchForm.startDate) params.append('start_date', searchForm.startDate)
    if (searchForm.endDate) params.append('end_date', searchForm.endDate)
    if (searchForm.market) params.append('market', searchForm.market)
    
    const response = await axios.get(`/api/profit?${params.toString()}`)
    console.log('API Response:', response.data) // 添加调试日志
    
    if (response.data.success) {
      marketStats.value = response.data.data.market_stats || {}
      stockStats.value = response.data.data.stock_stats || {}
    } else {
      console.error('API Error:', response.data.error)
      marketStats.value = {}
      stockStats.value = {}
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
    marketStats.value = {}
    stockStats.value = {}
  } finally {
    loading.value = false
  }
}

// 刷新市值
const refreshMarketValue = async () => {
  if (loading.value) return
  
  loading.value = true
  try {
    const response = await axios.get('/api/portfolio/market-value')
    console.log('Market Value Response:', response.data) // 添加调试日志
    
    if (response.data.success) {
      // 刷新数据
      await fetchData()
    } else {
      console.error('刷新市值失败:', response.data.error)
    }
  } catch (error) {
    console.error('刷新市值失败:', error)
  } finally {
    loading.value = false
  }
}

// 刷新数据
const refreshData = () => {
  fetchData()
}

// 搜索
const search = () => {
  fetchData()
}

// 重置搜索
const resetSearch = () => {
  searchForm.startDate = ''
  searchForm.endDate = ''
  searchForm.market = ''
  fetchData()
}

// 组件挂载时获取数据
onMounted(() => {
  fetchData()
})
</script>

<style scoped>
/* 表格样式 */
.table {
  margin-bottom: 0;
}

.table th {
  white-space: nowrap;
  font-size: 0.875rem;
  font-weight: 500;
  padding: 0.5rem;
  border-bottom: 2px solid #dee2e6;
  background-color: #f8f9fa;
  color: #495057;
}

.table td {
  padding: 0.5rem;
  font-size: 0.875rem;
  vertical-align: middle;
  border-bottom: 1px solid #dee2e6;
}

/* 市场行样式 */
.market-row {
  background-color: #f8f9fa;
}

.market-row td {
  font-weight: 500;
  color: #212529;
}

/* 股票行样式 */
.stock-row:hover {
  background-color: #f8f9fa;
}

.stock-row td {
  color: #212529;
}

/* 按钮样式 */
.btn-link {
  text-decoration: none;
  color: #6c757d;
  padding: 0.25rem;
  line-height: 1;
}

.btn-link:hover {
  color: #0d6efd;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
}

/* 文本颜色 */
.text-success {
  color: #198754 !important;
}

.text-danger {
  color: #dc3545 !important;
}

.text-muted {
  color: #6c757d !important;
  font-size: 0.75rem;
}

/* 卡片样式 */
.card {
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.card-header {
  background-color: #fff;
  border-bottom: 1px solid #dee2e6;
  padding: 0.75rem 1rem;
}

.card-body {
  padding: 1rem;
}

/* 表单样式 */
.form-label {
  margin-bottom: 0.25rem;
  color: #495057;
}

.form-select-sm {
  font-size: 0.875rem;
  padding: 0.25rem 0.5rem;
}

.form-control-sm {
  font-size: 0.875rem;
  padding: 0.25rem 0.5rem;
}

/* 图标样式 */
.fas {
  width: 1rem;
  text-align: center;
  margin-right: 0.25rem;
}

/* 响应式布局 */
.table-responsive {
  margin-bottom: 0;
}

@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .btn-group {
    width: 100%;
    justify-content: space-between;
  }
}
</style> 