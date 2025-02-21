<template>
  <div class="card">
    <div class="card-header d-flex justify-content-between align-items-center">
      <h4 class="mb-0">交易记录列表</h4>
      <div class="btn-group">
        <button type="button" class="btn btn-sm btn-outline-secondary" @click="toggleSearch">
          <i :class="['fas', searchVisible ? 'fa-chevron-up' : 'fa-search']"></i>
          {{ searchVisible ? '收起' : '搜索' }}
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
        <div class="col-md-4">
          <label class="form-label small">股票代码</label>
          <stock-selector
            v-model="searchForm.stockCodes"
            :stocks="allStocks"
            :market="searchForm.market"
          />
        </div>
        <div class="col-md-2 d-flex align-items-end">
          <button type="submit" class="btn btn-sm btn-primary w-100" :disabled="loading">
            <i class="fas fa-search"></i> 查询
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
              <th></th>
              <th>市场</th>
              <th>股票代码</th>
              <th>名称</th>
              <th>数量</th>
              <th class="text-end">买入总额</th>
              <th class="text-end">卖出总额</th>
              <th class="text-end">费用</th>
              <th class="text-end">已实现盈亏</th>
              <th class="text-end">现价</th>
              <th class="text-end">持仓价值</th>
              <th class="text-end">总盈亏</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <template v-if="!loading">
              <template v-for="(group, marketCode) in groupedTransactions" :key="marketCode">
                <!-- 市场分组头部 -->
                <tr class="table-secondary">
                  <td></td>
                  <td colspan="12">
                    <strong>{{ marketCode }}</strong>
                    <span class="ms-2 text-muted">
                      (总买入: {{ formatNumber(group.total.buy_amount) }},
                      总卖出: {{ formatNumber(group.total.sell_amount) }},
                      总费用: {{ formatNumber(group.total.fees) }})
                    </span>
                  </td>
                </tr>

                <!-- 持仓股票 -->
                <tr v-if="group.holding_stocks && group.holding_stocks.length > 0" class="table-light">
                  <td>
                    <button class="btn btn-sm btn-outline-secondary expand-btn" @click="toggleHoldingStocks(marketCode)">
                      <i class="fas" :class="isHoldingStocksExpanded(marketCode) ? 'fa-minus-square' : 'fa-plus-square'"></i>
                    </button>
                  </td>
                  <td colspan="12">
                    <strong class="text-primary">持仓股票 ({{ group.holding_stocks.length }})</strong>
                  </td>
                </tr>

                <!-- 持仓股票列表 -->
                <template v-if="isHoldingStocksExpanded(marketCode)">
                  <template v-for="stock in group.holding_stocks" :key="`${stock.market}-${stock.code}`">
                    <tr>
                      <td class="text-center">
                        <button class="btn btn-sm btn-outline-secondary expand-btn" @click="toggleDetails(stock)">
                          <i class="fas" :class="expandedStocks.includes(`${stock.market}-${stock.code}`) ? 'fa-minus-circle' : 'fa-plus-circle'"></i>
                        </button>
                      </td>
                      <td>{{ stock.market }}</td>
                      <td>{{ stock.code }}</td>
                      <td>{{ stock.name }}</td>
                      <td>{{ formatNumber(stock.quantity) }}</td>
                      <td class="text-end">{{ formatNumber(stock.total_buy) }}</td>
                      <td class="text-end">{{ formatNumber(stock.total_sell) }}</td>
                      <td class="text-end">{{ formatNumber(stock.total_fees) }}</td>
                      <td class="text-end" :class="{'text-success': stock.realized_profit > 0, 'text-danger': stock.realized_profit < 0}">
                        {{ formatNumber(stock.realized_profit) }}
                      </td>
                      <td class="text-end">{{ formatNumber(stock.current_price) }}</td>
                      <td class="text-end">{{ formatNumber(stock.market_value) }}</td>
                      <td class="text-end" :class="{'text-success': stock.total_profit > 0, 'text-danger': stock.total_profit < 0}">
                        {{ formatNumber(stock.total_profit) }}
                        <small class="d-block text-muted">
                          ({{ formatNumber(stock.profit_rate, 2) }}%)
                        </small>
                      </td>
                      <td>
                        <div class="btn-group btn-group-sm">
                          <button class="btn btn-outline-primary" @click="showDetails(stock)">
                            <i class="fas fa-list"></i>
                          </button>
                          <button class="btn btn-outline-secondary" @click="exportTransactions(stock)">
                            <i class="fas fa-download"></i>
                          </button>
                        </div>
                      </td>
                    </tr>
                    <!-- 交易明细行 -->
                    <tr v-if="expandedStocks.includes(`${stock.market}-${stock.code}`)">
                      <td colspan="13" class="p-0">
                        <div class="transaction-details">
                          <table class="table table-sm table-bordered mb-0">
                            <thead class="table-light">
                              <tr>
                                <th>交易日期</th>
                                <th>交易编号</th>
                                <th>类型</th>
                                <th class="text-end">数量@单价</th>
                                <th class="text-end">买入金额</th>
                                <th class="text-end">移动加权平均价</th>
                                <th class="text-end">卖出金额</th>
                                <th class="text-end">费用</th>
                                <th class="text-end">盈亏</th>
                                <th class="text-end">现价</th>
                                <th class="text-end">持仓价值</th>
                                <th class="text-end">总盈亏</th>
                                <th class="text-end">盈亏率</th>
                              </tr>
                            </thead>
                            <tbody>
                              <template v-if="transactionDetails[`${stock.market}-${stock.code}`]">
                                <tr v-for="detail in transactionDetails[`${stock.market}-${stock.code}`]" :key="detail.id">
                                  <td>{{ formatDate(detail.transaction_date) }}</td>
                                  <td>{{ detail.transaction_code }}</td>
                                  <td>{{ detail.transaction_type === 'BUY' ? '买入' : '卖出' }}</td>
                                  <td class="text-end">{{ formatNumber(detail.total_quantity, 0) }} @ {{ formatNumber(detail.total_amount / detail.total_quantity, 3) }}</td>
                                  <td class="text-end">{{ detail.transaction_type === 'BUY' ? formatNumber(detail.total_amount) : '' }}</td>
                                  <td class="text-end">{{ formatNumber(detail.sold_average_cost, 3) }}</td>
                                  <td class="text-end">{{ detail.transaction_type === 'SELL' ? formatNumber(detail.total_amount) : '' }}</td>
                                  <td class="text-end">{{ formatNumber(detail.total_fees_hkd) }}</td>
                                  <td class="text-end">{{ detail.transaction_type === 'SELL' ? formatNumber(calculateProfit(detail)) : '-' }}</td>
                                  <td class="text-end">-</td>
                                  <td class="text-end">-</td>
                                  <td class="text-end">-</td>
                                  <td class="text-end">-</td>
                                </tr>
                              </template>
                              <tr v-else>
                                <td colspan="13" class="text-center py-2">
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
                <tr v-if="group.closed_stocks && group.closed_stocks.length > 0" class="table-light">
                  <td>
                    <button class="btn btn-sm btn-outline-secondary expand-btn" @click="toggleClosedStocks(marketCode)">
                      <i class="fas" :class="isClosedStocksExpanded(marketCode) ? 'fa-minus-square' : 'fa-plus-square'"></i>
                    </button>
                  </td>
                  <td colspan="12">
                    <strong class="text-secondary">已清仓股票 ({{ group.closed_stocks.length }})</strong>
                  </td>
                </tr>

                <!-- 已清仓股票列表 -->
                <template v-if="isClosedStocksExpanded(marketCode)">
                  <template v-for="stock in group.closed_stocks" :key="`${stock.market}-${stock.code}`">
                    <tr>
                      <td class="text-center">
                        <button class="btn btn-sm btn-outline-secondary expand-btn" @click="toggleDetails(stock)">
                          <i class="fas" :class="expandedStocks.includes(`${stock.market}-${stock.code}`) ? 'fa-minus-circle' : 'fa-plus-circle'"></i>
                        </button>
                      </td>
                      <td>{{ stock.market }}</td>
                      <td>{{ stock.code }}</td>
                      <td>{{ stock.name }}</td>
                      <td>{{ formatNumber(stock.quantity) }}</td>
                      <td class="text-end">{{ formatNumber(stock.total_buy) }}</td>
                      <td class="text-end">{{ formatNumber(stock.total_sell) }}</td>
                      <td class="text-end">{{ formatNumber(stock.total_fees) }}</td>
                      <td class="text-end" :class="{'text-success': stock.realized_profit > 0, 'text-danger': stock.realized_profit < 0}">
                        {{ formatNumber(stock.realized_profit) }}
                      </td>
                      <td class="text-end">{{ formatNumber(stock.current_price) }}</td>
                      <td class="text-end">{{ formatNumber(stock.market_value) }}</td>
                      <td class="text-end" :class="{'text-success': stock.total_profit > 0, 'text-danger': stock.total_profit < 0}">
                        {{ formatNumber(stock.total_profit) }}
                        <small class="d-block text-muted">
                          ({{ formatNumber(stock.profit_rate, 2) }}%)
                        </small>
                      </td>
                      <td>
                        <div class="btn-group btn-group-sm">
                          <button class="btn btn-outline-primary" @click="showDetails(stock)">
                            <i class="fas fa-list"></i>
                          </button>
                          <button class="btn btn-outline-secondary" @click="exportTransactions(stock)">
                            <i class="fas fa-download"></i>
                          </button>
                        </div>
                      </td>
                    </tr>
                    <!-- 交易明细行 -->
                    <tr v-if="expandedStocks.includes(`${stock.market}-${stock.code}`)">
                      <td colspan="13" class="p-0">
                        <div class="transaction-details">
                          <table class="table table-sm table-bordered mb-0">
                            <thead class="table-light">
                              <tr>
                                <th>交易日期</th>
                                <th>交易编号</th>
                                <th>类型</th>
                                <th class="text-end">数量@单价</th>
                                <th class="text-end">买入金额</th>
                                <th class="text-end">移动加权平均价</th>
                                <th class="text-end">卖出金额</th>
                                <th class="text-end">费用</th>
                                <th class="text-end">盈亏</th>
                                <th class="text-end">现价</th>
                                <th class="text-end">持仓价值</th>
                                <th class="text-end">总盈亏</th>
                                <th class="text-end">盈亏率</th>
                              </tr>
                            </thead>
                            <tbody>
                              <template v-if="transactionDetails[`${stock.market}-${stock.code}`]">
                                <tr v-for="detail in transactionDetails[`${stock.market}-${stock.code}`]" :key="detail.id">
                                  <td>{{ formatDate(detail.transaction_date) }}</td>
                                  <td>{{ detail.transaction_code }}</td>
                                  <td>{{ detail.transaction_type === 'BUY' ? '买入' : '卖出' }}</td>
                                  <td class="text-end">{{ formatNumber(detail.total_quantity, 0) }} @ {{ formatNumber(detail.total_amount / detail.total_quantity, 3) }}</td>
                                  <td class="text-end">{{ detail.transaction_type === 'BUY' ? formatNumber(detail.total_amount) : '' }}</td>
                                  <td class="text-end">{{ formatNumber(detail.sold_average_cost, 3) }}</td>
                                  <td class="text-end">{{ detail.transaction_type === 'SELL' ? formatNumber(detail.total_amount) : '' }}</td>
                                  <td class="text-end">{{ formatNumber(detail.total_fees_hkd) }}</td>
                                  <td class="text-end">{{ detail.transaction_type === 'SELL' ? formatNumber(calculateProfit(detail)) : '-' }}</td>
                                  <td class="text-end">-</td>
                                  <td class="text-end">-</td>
                                  <td class="text-end">-</td>
                                  <td class="text-end">-</td>
                                </tr>
                              </template>
                              <tr v-else>
                                <td colspan="13" class="text-center py-2">
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
            <tr v-else>
              <td colspan="12" class="text-center py-3">
                <div class="spinner-border spinner-border-sm text-primary me-2"></div>
                加载中...
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 分页 -->
      <div v-if="totalPages > 1" class="card-footer d-flex justify-content-center">
        <nav>
          <ul class="pagination pagination-sm mb-0">
            <li class="page-item" :class="{ disabled: currentPage === 1 }">
              <a class="page-link" href="#" @click.prevent="changePage(currentPage - 1)">
                <i class="fas fa-chevron-left"></i>
              </a>
            </li>
            <li v-for="page in displayedPages" 
                :key="page" 
                class="page-item"
                :class="{ active: currentPage === page, disabled: page === '...' }">
              <template v-if="page === '...'">
                <span class="page-link">{{ page }}</span>
              </template>
              <template v-else>
                <a class="page-link" href="#" @click.prevent="changePage(page)">{{ page }}</a>
              </template>
            </li>
            <li class="page-item" :class="{ disabled: currentPage === totalPages }">
              <a class="page-link" href="#" @click.prevent="changePage(currentPage + 1)">
                <i class="fas fa-chevron-right"></i>
              </a>
            </li>
          </ul>
        </nav>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import DateInput from '../components/DateInput.vue'
import StockSelector from '../components/StockSelector.vue'
import axios from 'axios'

const router = useRouter()
const loading = ref(false)
const searchVisible = ref(false)
const transactions = ref([])
const allStocks = ref([])
const currentPage = ref(1)
const totalPages = ref(1)
const pageSize = 15

// 搜索表单
const searchForm = reactive({
  startDate: '',
  endDate: '',
  market: '',
  stockCodes: []
})

// 添加展开/收起状态管理
const expandedStocks = ref([])
const transactionDetails = ref({})

// 添加持仓和已清仓股票的展开状态管理
const expandedHoldingStocks = ref([])
const expandedClosedStocks = ref([])

// 获取所有股票
const fetchStocks = async () => {
  try {
    const response = await axios.get('/api/stock/stocks')
    if (response.data.success) {
      allStocks.value = response.data.data.items
    }
  } catch (error) {
    console.error('获取股票列表失败:', error)
  }
}

// 获取交易记录
const fetchTransactions = async () => {
  if (loading.value) return
  
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (searchForm.startDate) params.append('start_date', searchForm.startDate)
    if (searchForm.endDate) params.append('end_date', searchForm.endDate)
    if (searchForm.market) params.append('market', searchForm.market)
    if (searchForm.stockCodes.length > 0) {
      searchForm.stockCodes.forEach(code => params.append('stock_codes[]', code))
    }
    params.append('page', currentPage.value)
    params.append('per_page', pageSize)
    
    console.log('发送请求获取交易记录:', `/api/profit/?${params.toString()}`)
    const response = await axios.get(`/api/profit/?${params.toString()}`)
    console.log('获取到的响应:', response.data)
    
    if (response.data.success) {
      // 处理市场统计数据
      const marketStats = response.data.data.market_stats || {}
      const stockStats = response.data.data.stock_stats || {}
      
      // 重置数据
      transactions.value = []
      
      // 构建分组数据
      const groups = {}
      
      // 处理每个市场的数据
      Object.entries(marketStats).forEach(([market, marketData]) => {
        groups[market] = {
          total: {
            buy_amount: marketData.total_buy || 0,
            sell_amount: marketData.total_sell || 0,
            fees: marketData.total_fees || 0
          },
          holding_stocks: [],
          closed_stocks: []
        }
      })
      
      // 处理每个股票的数据
      Object.entries(stockStats).forEach(([key, stockData]) => {
        const [market, code] = key.split('-')
        if (groups[market]) {
          // 根据是否有持仓数量来区分持仓和已清仓
          const stockList = stockData.quantity > 0 ? groups[market].holding_stocks : groups[market].closed_stocks
          
          stockList.push({
            market: market,
            code: code,
            name: stockData.name,
            quantity: stockData.quantity || 0,
            total_buy: stockData.total_buy || 0,
            total_sell: stockData.total_sell || 0,
            total_fees: stockData.total_fees || 0,
            realized_profit: stockData.realized_profit || 0,
            current_price: stockData.current_price || 0,
            market_value: stockData.market_value || 0,
            total_profit: stockData.total_profit || 0,
            profit_rate: stockData.profit_rate || 0
          })
        }
      })
      
      // 更新数据
      Object.entries(groups).forEach(([market, group]) => {
        // 处理持仓股票
        group.holding_stocks.forEach(stock => {
          transactions.value.push({
            market: stock.market,
            stock_code: stock.code,
            name: stock.name,
            ...stock
          })
        })
        
        // 处理已清仓股票
        group.closed_stocks.forEach(stock => {
          transactions.value.push({
            market: stock.market,
            stock_code: stock.code,
            name: stock.name,
            ...stock
          })
        })
      })
      
      console.log('处理后的分组数据:', groups)
    }
  } catch (error) {
    console.error('获取交易记录失败:', error)
  } finally {
    loading.value = false
  }
}

// 分页相关
const displayedPages = computed(() => {
  const pages = []
  const maxDisplayed = 7 // 最多显示的页码数
  const sidePages = 2 // 当前页两侧显示的页码数
  
  if (totalPages.value <= maxDisplayed) {
    // 总页数较少时，显示所有页码
    for (let i = 1; i <= totalPages.value; i++) {
      pages.push(i)
    }
  } else {
    // 总页数较多时，显示部分页码
    if (currentPage.value <= sidePages + 3) {
      // 当前页靠近开始
      for (let i = 1; i <= sidePages + 3; i++) {
        pages.push(i)
      }
      pages.push('...')
      pages.push(totalPages.value)
    } else if (currentPage.value >= totalPages.value - (sidePages + 2)) {
      // 当前页靠近结束
      pages.push(1)
      pages.push('...')
      for (let i = totalPages.value - (sidePages + 2); i <= totalPages.value; i++) {
        pages.push(i)
      }
    } else {
      // 当前页在中间
      pages.push(1)
      pages.push('...')
      for (let i = currentPage.value - sidePages; i <= currentPage.value + sidePages; i++) {
        pages.push(i)
      }
      pages.push('...')
      pages.push(totalPages.value)
    }
  }
  
  return pages
})

// 切换页码
const changePage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
    fetchTransactions()
  }
}

// 搜索相关
const toggleSearch = () => {
  searchVisible.value = !searchVisible.value
}

const search = () => {
  currentPage.value = 1
  fetchTransactions()
}

const resetSearch = () => {
  searchForm.startDate = ''
  searchForm.endDate = ''
  searchForm.market = ''
  searchForm.stockCodes = []
  currentPage.value = 1
  fetchTransactions()
}

// 删除交易记录
const confirmDelete = async (transaction) => {
  if (!confirm('确定要删除这条交易记录吗？')) return
  
  try {
    const response = await axios.delete(`/api/stock/transactions/${transaction.id}`)
    if (response.data.success) {
      // 重新加载数据
      fetchTransactions()
    }
  } catch (error) {
    console.error('删除交易记录失败:', error)
  }
}

// 工具函数
const formatDate = (date) => {
  return new Date(date).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).replace(/\//g, '-')
}

const formatNumber = (value, decimals = 2) => {
  if (value === null || value === undefined) return '-'
  return Number(value).toLocaleString('zh-HK', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })
}

const getStockName = (code) => {
  const stock = allStocks.value.find(s => s.code === code)
  return stock ? stock.name : ''
}

// 切换持仓股票显示
const toggleHoldingStocks = (market) => {
  const index = expandedHoldingStocks.value.indexOf(market)
  if (index === -1) {
    expandedHoldingStocks.value.push(market)
  } else {
    expandedHoldingStocks.value.splice(index, 1)
  }
}

// 切换已清仓股票显示
const toggleClosedStocks = (market) => {
  const index = expandedClosedStocks.value.indexOf(market)
  if (index === -1) {
    expandedClosedStocks.value.push(market)
  } else {
    expandedClosedStocks.value.splice(index, 1)
  }
}

// 检查持仓股票是否展开
const isHoldingStocksExpanded = (market) => {
  return expandedHoldingStocks.value.includes(market)
}

// 检查已清仓股票是否展开
const isClosedStocksExpanded = (market) => {
  return expandedClosedStocks.value.includes(market)
}

// 修改 groupedTransactions 计算属性
const groupedTransactions = computed(() => {
  const groups = {}
  
  transactions.value.forEach(transaction => {
    const market = transaction.market
    if (!groups[market]) {
      groups[market] = {
        total: {
          buy_amount: 0,
          sell_amount: 0,
          fees: 0
        },
        holding_stocks: [],
        closed_stocks: []
      }
    }
    
    // 根据是否有持仓数量来区分持仓和已清仓
    const stockList = transaction.quantity > 0 ? groups[market].holding_stocks : groups[market].closed_stocks
    
    // 查找现有的股票记录
    let stock = stockList.find(s => s.code === transaction.stock_code)
    if (!stock) {
      stock = {
        market: transaction.market,
        code: transaction.stock_code,
        name: transaction.name,
        quantity: transaction.quantity || 0,
        total_buy: transaction.total_buy || 0,
        total_sell: transaction.total_sell || 0,
        total_fees: transaction.total_fees || 0,
        realized_profit: transaction.realized_profit || 0,
        current_price: transaction.current_price || 0,
        market_value: transaction.market_value || 0,
        total_profit: transaction.total_profit || 0,
        profit_rate: transaction.profit_rate || 0
      }
      stockList.push(stock)
    }
    
    // 更新市场汇总数据
    groups[market].total.buy_amount += transaction.total_buy || 0
    groups[market].total.sell_amount += transaction.total_sell || 0
    groups[market].total.fees += transaction.total_fees || 0
  })
  
  return groups
})

// 添加查看详情方法
const showDetails = (stock) => {
  // 实现查看详情的逻辑
}

// 添加导出方法
const exportTransactions = (stock) => {
  // 实现导出的逻辑
}

// 切换明细显示
const toggleDetails = async (stock) => {
  const key = `${stock.market}-${stock.code}`
  console.log('切换明细显示:', key)
  
  const index = expandedStocks.value.indexOf(key)
  if (index === -1) {
    // 展开并获取数据
    console.log('展开股票明细:', stock)
    expandedStocks.value.push(key)
    
    try {
      const params = new URLSearchParams()
      params.append('market', stock.market)
      params.append('stock_codes[]', stock.code)
      
      console.log('发送请求获取交易明细:', `/api/profit/?${params.toString()}`)
      const response = await axios.get(`/api/profit/?${params.toString()}`)
      console.log('获取到的响应:', response.data)
      
      if (response.data.success) {
        if (response.data.data.transaction_details) {
          const details = response.data.data.transaction_details[key] || []
          console.log('处理后的交易明细:', details)
          transactionDetails.value[key] = details
        } else {
          console.warn('响应中没有 transaction_details 数据')
          transactionDetails.value[key] = []
        }
      } else {
        console.error('获取交易明细失败:', response.data.message)
        transactionDetails.value[key] = []
      }
    } catch (error) {
      console.error('获取交易明细失败:', error)
      transactionDetails.value[key] = []
    }
  } else {
    // 收起
    console.log('收起股票明细:', key)
    expandedStocks.value.splice(index, 1)
  }
}

// 初始化
onMounted(() => {
  fetchStocks()
  fetchTransactions()
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

/* 按钮样式 */
.btn-sm {
  padding: 0.25rem 0.5rem;
  line-height: 1.2;
  border-radius: 0.2rem;
}

.btn-sm:hover {
  background-color: #e9ecef;
}

.btn-sm .fas {
  font-size: 1.25rem;
  display: inline-block;
  width: 1em;
  height: 1em;
  vertical-align: -0.125em;
}

/* 文本样式 */
.text-muted {
  font-size: 0.75rem;
}

/* 徽章样式 */
.badge {
  font-size: 0.75rem;
  font-weight: normal;
  padding: 0.25rem 0.5rem;
}

/* 分页样式 */
.pagination {
  margin-bottom: 0;
}

.page-link {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
}

.page-item.active .page-link {
  background-color: #0d6efd;
  border-color: #0d6efd;
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

.card-footer {
  background-color: #fff;
  border-top: 1px solid #dee2e6;
  padding: 0.75rem 1rem;
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

/* 图标样式 */
.fas {
  width: 1rem;
  text-align: center;
  margin-right: 0.25rem;
}

/* 响应式布局 */
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

/* 添加交易明细样式 */
.transaction-details {
  background-color: #f8f9fa;
  padding: 0.5rem;
  font-size: 0.8125rem;
}

.transaction-details .table {
  background-color: white;
  margin-bottom: 0;
}

.transaction-details th,
.transaction-details td {
  padding: 0.4rem 0.5rem;
  font-size: 0.8125rem;
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

/* 展开按钮样式 */
.expand-btn {
  width: 32px;
  height: 32px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  background-color: white;
  transition: all 0.2s;
}

.expand-btn:hover {
  background-color: #f8f9fa;
  border-color: #0d6efd;
}

.expand-btn .fas {
  font-size: 1.25rem;
  margin: 0;
  width: auto;
}

.expand-btn .fa-plus-square,
.expand-btn .fa-plus-circle {
  color: #0d6efd;
}

.expand-btn .fa-minus-square,
.expand-btn .fa-minus-circle {
  color: #dc3545;
}

.expand-btn:hover .fa-plus-square,
.expand-btn:hover .fa-plus-circle {
  color: #0a58ca;
}

.expand-btn:hover .fa-minus-square,
.expand-btn:hover .fa-minus-circle {
  color: #b02a37;
}
</style> 