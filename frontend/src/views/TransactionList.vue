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
              <th>日期</th>
              <th>市场</th>
              <th>股票代码</th>
              <th>交易编号</th>
              <th>买卖</th>
              <th>成交明细</th>
              <th class="text-end">总金额</th>
              <th class="text-end">经纪佣金</th>
              <th class="text-end">交易征费</th>
              <th class="text-end">印花税</th>
              <th class="text-end">交易费</th>
              <th class="text-end">存入证券费</th>
              <th class="text-end">手续费</th>
              <th class="text-end">净金额</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <template v-if="!loading">
              <tr v-for="transaction in transactions" :key="transaction.id">
                <td>{{ formatDate(transaction.transaction_date) }}</td>
                <td>{{ transaction.market }}</td>
                <td>
                  <div>{{ transaction.stock_code }}</div>
                  <small class="text-muted">{{ getStockName(transaction.stock_code) }}</small>
                </td>
                <td>{{ transaction.transaction_code }}</td>
                <td>
                  <span :class="['badge', transaction.transaction_type === 'BUY' ? 'bg-danger' : 'bg-success']">
                    {{ transaction.transaction_type === 'BUY' ? '买入' : '卖出' }}
                  </span>
                </td>
                <td>
                  <div v-for="detail in transaction.details" :key="detail.id">
                    {{ detail.quantity }}股 @ {{ formatNumber(detail.price, 3) }}
                  </div>
                </td>
                <td class="text-end">
                  {{ formatNumber(transaction.total_amount) }}
                  <template v-if="transaction.market !== 'HK'">
                    <br>
                    <small class="text-muted">
                      {{ formatNumber(transaction.exchange_rate, 3) }}@{{ formatNumber(transaction.total_amount_hkd) }}
                    </small>
                  </template>
                </td>
                <td class="text-end">{{ formatNumber(transaction.broker_fee) }}</td>
                <td class="text-end">{{ formatNumber(transaction.transaction_levy) }}</td>
                <td class="text-end">{{ formatNumber(transaction.stamp_duty) }}</td>
                <td class="text-end">{{ formatNumber(transaction.trading_fee) }}</td>
                <td class="text-end">{{ formatNumber(transaction.deposit_fee) }}</td>
                <td class="text-end">{{ formatNumber(transaction.total_fees) }}</td>
                <td class="text-end">
                  {{ formatNumber(transaction.net_amount) }}
                  <template v-if="transaction.market !== 'HK'">
                    <br>
                    <small class="text-muted">
                      {{ formatNumber(transaction.exchange_rate, 3) }}@{{ formatNumber(transaction.net_amount_hkd) }}
                    </small>
                  </template>
                </td>
                <td>
                  <div class="btn-group btn-group-sm">
                    <router-link :to="`/transactions/edit/${transaction.id}`" class="btn btn-outline-primary">
                      <i class="fas fa-edit"></i>
                    </router-link>
                    <button class="btn btn-outline-danger" @click="confirmDelete(transaction)">
                      <i class="fas fa-trash"></i>
                    </button>
                  </div>
                </td>
              </tr>
            </template>
            <tr v-else>
              <td colspan="15" class="text-center py-3">
                <div class="spinner-border spinner-border-sm text-primary me-2"></div>
                加载中...
              </td>
            </tr>
            <tr v-if="!loading && transactions.length === 0">
              <td colspan="15" class="text-center py-4">
                <p class="text-muted mb-2">暂无交易记录</p>
                <router-link to="/transactions/add" class="btn btn-primary btn-sm">
                  添加第一条记录
                </router-link>
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
      searchForm.stockCodes.forEach(code => params.append('stock_codes', code))
    }
    params.append('page', currentPage.value)
    params.append('per_page', pageSize)
    
    const response = await axios.get(`/api/stock/transactions?${params.toString()}`)
    if (response.data.success) {
      transactions.value = response.data.data.items
      totalPages.value = Math.ceil(response.data.data.total / pageSize)
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
  font-size: 0.875rem;
}

.btn-group-sm > .btn {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
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
</style> 