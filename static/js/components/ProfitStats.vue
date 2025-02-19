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
        <button type="button" class="btn btn-sm btn-outline-secondary" @click="expandAll">
          <i class="fas fa-expand-alt"></i> 展开
        </button>
        <button type="button" class="btn btn-sm btn-outline-secondary" @click="collapseAll">
          <i class="fas fa-compress-alt"></i> 收起
        </button>
        <router-link to="/stock/add" class="btn btn-sm btn-primary">
          <i class="fas fa-plus"></i> 添加记录
        </router-link>
      </div>
    </div>

    <!-- 搜索表单 -->
    <div v-show="searchVisible" class="card-body border-bottom">
      <form @submit.prevent="search" class="row g-3">
        <div class="col-md-3">
          <label class="form-label small">开始日期</label>
          <input type="text" class="form-control form-control-sm" v-model="searchForm.startDate" 
                 placeholder="YYYY-MM-DD" pattern="\d{4}-\d{2}-\d{2}"
                 @input="formatDateInput">
        </div>
        <div class="col-md-3">
          <label class="form-label small">结束日期</label>
          <input type="text" class="form-control form-control-sm" v-model="searchForm.endDate"
                 placeholder="YYYY-MM-DD" pattern="\d{4}-\d{2}-\d{2}"
                 @input="formatDateInput">
        </div>
        <div class="col-md-2">
          <label class="form-label small">市场</label>
          <select class="form-select form-select-sm" v-model="searchForm.market">
            <option value="">全部</option>
            <option value="HK">HK</option>
            <option value="USA">USA</option>
          </select>
        </div>
        <div class="col-md-4">
          <label class="form-label small">股票代码</label>
          <stock-selector v-model="searchForm.stockCodes" :stocks="allStocks" />
        </div>
        <div class="col-md-2 d-flex align-items-end">
          <button type="submit" class="btn btn-sm btn-primary w-100" :disabled="loading">查询</button>
        </div>
        <div class="col-md-2 d-flex align-items-end">
          <button type="button" class="btn btn-sm btn-outline-secondary w-100" @click="resetSearch">重置</button>
        </div>
      </form>
    </div>

    <div class="card-body">
      <div class="table-responsive">
        <table class="table table-hover">
          <thead class="table-light">
            <tr>
              <th style="width: 30px"></th>
              <th style="width: 50px">市场</th>
              <th style="width: 80px">代码</th>
              <th class="text-end" style="width: 60px">数量</th>
              <th class="text-end" style="width: 50px">笔数</th>
              <th class="text-end" style="width: 100px">买入总额</th>
              <th class="text-end" style="width: 80px">平均价格</th>
              <th class="text-end" style="width: 100px">卖出总额</th>
              <th class="text-end" style="width: 80px">费用</th>
              <th class="text-end" style="width: 100px">盈亏</th>
              <th class="text-end" style="width: 80px">现价</th>
              <th class="text-end" style="width: 100px">持仓价值</th>
              <th class="text-end" style="width: 100px">总盈亏</th>
              <th class="text-end" style="width: 60px">盈亏率</th>
            </tr>
          </thead>
          <tbody>
            <!-- 市场汇总行 -->
            <template v-for="(stats, market) in marketStats" :key="market">
              <tr class="market-row fw-bold">
                <td>
                  <button class="btn btn-sm btn-link p-0" @click="toggleMarket(market)">
                    <i :class="['fas', marketExpanded[market] ? 'fa-chevron-down' : 'fa-chevron-right']"></i>
                  </button>
                </td>
                <td>{{ market }}</td>
                <td>市场汇总</td>
                <td class="text-end">-</td>
                <td class="text-end">{{ stats.transaction_count }}</td>
                <td class="text-end text-danger">{{ formatNumber(stats.total_buy) }}</td>
                <td class="text-end">-</td>
                <td class="text-end text-success">{{ formatNumber(stats.total_sell) }}</td>
                <td class="text-end">{{ formatNumber(stats.total_fees) }}</td>
                <td class="text-end" :class="getProfitClass(stats.realized_profit)">
                  {{ formatNumber(stats.realized_profit) }}
                </td>
                <td class="text-end">-</td>
                <td class="text-end text-success">{{ formatNumber(stats.market_value) }}</td>
                <td class="text-end" :class="getProfitClass(stats.total_profit)">
                  {{ formatNumber(stats.total_profit) }}
                </td>
                <td class="text-end" :class="getProfitClass(stats.profit_rate)">
                  {{ formatRate(stats.profit_rate) }}
                </td>
              </tr>

              <!-- 持仓和已清仓股票 -->
              <template v-if="marketExpanded[market]">
                <!-- 持仓股票 -->
                <tr v-for="stock in getHoldingStocks(market)" :key="stock.code"
                    class="stock-row" :class="{'d-none': !marketExpanded[market]}">
                  <td></td>
                  <td></td>
                  <td>
                    {{ stock.code }}
                    <br v-if="stock.name">
                    <small v-if="stock.name" class="text-muted">{{ stock.name }}</small>
                  </td>
                  <td class="text-end fw-bold">{{ stock.current_quantity }}</td>
                  <td class="text-end">{{ stock.transaction_count }}</td>
                  <td class="text-end text-danger">{{ formatNumber(stock.total_buy) }}</td>
                  <td class="text-end">{{ formatNumber(stock.avg_cost, 3) }}</td>
                  <td class="text-end text-success">{{ formatNumber(stock.total_sell) }}</td>
                  <td class="text-end">{{ formatNumber(stock.total_fees) }}</td>
                  <td class="text-end" :class="getProfitClass(stock.realized_profit)">
                    {{ formatNumber(stock.realized_profit) }}
                  </td>
                  <td class="text-end">{{ formatNumber(stock.current_price, 3) }}</td>
                  <td class="text-end text-success">{{ formatNumber(stock.market_value) }}</td>
                  <td class="text-end" :class="getProfitClass(stock.total_profit)">
                    {{ formatNumber(stock.total_profit) }}
                  </td>
                  <td class="text-end" :class="getProfitClass(stock.profit_rate)">
                    {{ formatRate(stock.profit_rate) }}
                  </td>
                </tr>

                <!-- 已清仓股票 -->
                <tr v-for="stock in getClosedStocks(market)" :key="stock.code"
                    class="stock-row" :class="{'d-none': !marketExpanded[market]}">
                  <td></td>
                  <td></td>
                  <td>
                    {{ stock.code }}
                    <br v-if="stock.name">
                    <small v-if="stock.name" class="text-muted">{{ stock.name }}</small>
                  </td>
                  <td class="text-end">-</td>
                  <td class="text-end">{{ stock.transaction_count }}</td>
                  <td class="text-end text-danger">{{ formatNumber(stock.total_buy) }}</td>
                  <td class="text-end">{{ formatNumber(stock.avg_cost, 3) }}</td>
                  <td class="text-end text-success">{{ formatNumber(stock.total_sell) }}</td>
                  <td class="text-end">{{ formatNumber(stock.total_fees) }}</td>
                  <td class="text-end" :class="getProfitClass(stock.realized_profit)">
                    {{ formatNumber(stock.realized_profit) }}
                  </td>
                  <td class="text-end">-</td>
                  <td class="text-end">-</td>
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

<script>
import { ref, reactive, onMounted } from 'vue'
import StockSelector from './StockSelector.vue'
import { formatDateInput } from '../utils/dateUtils'
import { formatNumber, formatRate } from '../utils/numberUtils'

export default {
  name: 'ProfitStats',
  
  components: {
    StockSelector
  },

  setup() {
    const loading = ref(false)
    const searchVisible = ref(false)
    const marketExpanded = reactive({})
    const marketStats = ref({})
    const stockStats = ref({})
    const allStocks = ref([])
    
    const searchForm = reactive({
      startDate: '',
      endDate: '',
      market: '',
      stockCodes: []
    })

    // 获取统计数据
    const fetchData = async () => {
      loading.value = true
      try {
        const params = new URLSearchParams()
        if (searchForm.startDate) params.append('start_date', searchForm.startDate)
        if (searchForm.endDate) params.append('end_date', searchForm.endDate)
        if (searchForm.market) params.append('market', searchForm.market)
        searchForm.stockCodes.forEach(code => params.append('stock_codes', code))

        const response = await fetch(`/api/profit?${params.toString()}`)
        const result = await response.json()
        
        if (result.success) {
          marketStats.value = result.data.market_stats
          stockStats.value = result.data.stock_stats
          allStocks.value = result.data.all_stocks
        } else {
          throw new Error(result.error)
        }
      } catch (error) {
        console.error('获取数据失败:', error)
        // TODO: 显示错误提示
      } finally {
        loading.value = false
      }
    }

    // 搜索相关方法
    const toggleSearch = () => {
      searchVisible.value = !searchVisible.value
    }

    const search = () => {
      fetchData()
    }

    const resetSearch = () => {
      searchForm.startDate = ''
      searchForm.endDate = ''
      searchForm.market = ''
      searchForm.stockCodes = []
      fetchData()
    }

    // 展开/收起相关方法
    const toggleMarket = (market) => {
      marketExpanded[market] = !marketExpanded[market]
    }

    const expandAll = () => {
      Object.keys(marketStats.value).forEach(market => {
        marketExpanded[market] = true
      })
    }

    const collapseAll = () => {
      Object.keys(marketStats.value).forEach(market => {
        marketExpanded[market] = false
      })
    }

    // 数据处理方法
    const getHoldingStocks = (market) => {
      return Object.entries(stockStats.value)
        .filter(([_, stock]) => stock.market === market && stock.current_quantity > 0)
        .map(([code, stock]) => ({ code, ...stock }))
    }

    const getClosedStocks = (market) => {
      return Object.entries(stockStats.value)
        .filter(([_, stock]) => stock.market === market && stock.current_quantity === 0)
        .map(([code, stock]) => ({ code, ...stock }))
    }

    const getProfitClass = (value) => {
      if (value > 0) return 'text-success'
      if (value < 0) return 'text-danger'
      return ''
    }

    // 初始化
    onMounted(() => {
      fetchData()
    })

    return {
      loading,
      searchVisible,
      marketExpanded,
      marketStats,
      stockStats,
      allStocks,
      searchForm,
      toggleSearch,
      search,
      resetSearch,
      toggleMarket,
      expandAll,
      collapseAll,
      getHoldingStocks,
      getClosedStocks,
      getProfitClass,
      formatNumber,
      formatRate,
      formatDateInput
    }
  }
}
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
}

.text-success {
  color: #198754 !important;
}

.text-danger {
  color: #dc3545 !important;
}
</style> 