<template>
  <div class="card">
    <div class="card-header d-flex justify-content-between align-items-center">
      <h5 class="mb-0">交易记录</h5>
      <div class="btn-group">
        <button class="btn btn-primary btn-sm" @click="addTransaction">
          <i class="fas fa-plus me-1"></i>添加记录
        </button>
        <button class="btn btn-outline-secondary btn-sm" @click="toggleSearch">
          <i :class="['fas', searchVisible ? 'fa-chevron-up' : 'fa-search']" class="me-1"></i>
          {{ searchVisible ? '收起' : '搜索' }}
        </button>
      </div>
    </div>

    <!-- 搜索表单 -->
    <div v-show="searchVisible" class="card-body border-bottom">
      <form @submit.prevent="search" class="row g-2 align-items-end">
        <div class="col-auto" style="width: 160px;">
          <label class="form-label small">开始日期</label>
          <input
            type="text"
            class="form-control form-control-sm"
            :value="startDateDisplayValue"
            @input="handleStartDateInput"
            @blur="handleStartDateBlur"
            @keydown.enter.prevent="focusNext($event, 'endDate')"
            @keydown.tab="focusNext($event, 'endDate')"
            placeholder="YYYY-MM-DD"
            ref="startDate"
          />
        </div>
        <div class="col-auto" style="width: 160px;">
          <label class="form-label small">结束日期</label>
          <input
            type="text"
            class="form-control form-control-sm"
            :value="endDateDisplayValue"
            @input="handleEndDateInput"
            @blur="handleEndDateBlur"
            @keydown.enter.prevent="focusNext($event, 'market')"
            @keydown.tab="focusNext($event, 'market')"
            placeholder="YYYY-MM-DD"
            ref="endDate"
          />
        </div>
        <div class="col-auto" style="width: 100px;">
          <label class="form-label small">市场</label>
          <select 
            class="form-select form-select-sm" 
            v-model="searchForm.market"
            ref="market"
            @keydown.enter.prevent="focusNext($event, 'transactionCode')"
            @keydown.tab="focusNext($event, 'transactionCode')"
          >
            <option value="">全部</option>
            <option value="HK">HK</option>
            <option value="USA">USA</option>
          </select>
        </div>
        <div class="col-auto" style="width: 160px;">
          <label class="form-label small">交易编号</label>
          <input
            type="text"
            class="form-control form-control-sm"
            v-model="searchForm.transactionCode"
            ref="transactionCode"
            @keydown.enter.prevent="searchAndClear"
            @keydown.tab="focusNext($event, 'search')"
            placeholder="输入交易编号"
            data-testid="transaction-code-input"
          />
        </div>
        <div class="col" style="min-width: 200px;">
          <label class="form-label small">股票代码</label>
          <stock-selector
            v-model="searchForm.stockCodes"
            :stocks="allStocks"
            :market="searchForm.market"
          />
        </div>
        <div class="col-auto">
          <button type="submit" class="btn btn-sm btn-primary" style="width: 80px;" :disabled="loading" ref="searchBtn">
            <i class="fas fa-search"></i> 查询
          </button>
        </div>
        <div class="col-auto">
          <button type="button" class="btn btn-sm btn-outline-secondary" style="width: 80px;" @click="resetSearch">
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
              <th style="width: 100px" class="text-center">日期</th>
              <th style="width: 40px" class="text-center">市场</th>
              <th style="width: 120px" class="text-center">股票代码</th>
              <th style="width: 100px" class="text-center">交易编号</th>
              <th style="width: 50px" class="text-center">买卖</th>
              <th style="width: 90px" class="text-center">成交明细</th>
              <th style="width: 70px" class="text-end">平均价</th>
              <th style="width: 80px" class="text-end">总金额</th>
              <th style="width: 70px" class="text-end">经纪佣金</th>
              <th style="width: 70px" class="text-end">交易征费</th>
              <th style="width: 70px" class="text-end">印花税</th>
              <th style="width: 70px" class="text-end">交易费</th>
              <th style="width: 70px" class="text-end">存入证券费</th>
              <th style="width: 70px" class="text-end">手续费</th>
              <th style="width: 80px" class="text-end">净金额</th>
              <th style="width: 70px" class="text-center">操作</th>
            </tr>
          </thead>
          <tbody>
            <template v-if="!loading">
              <tr v-for="transaction in sortedTransactions" :key="transaction.id">
                <td>{{ formatDate(transaction.transaction_date) }}</td>
                <td>{{ transaction.market }}</td>
                <td class="text-center">
                  {{ transaction.stock_code }}
                  <br>
                  <small class="text-muted">{{ transaction.stock_name }}</small>
                </td>
                <td>{{ transaction.transaction_code.trim() }}</td>
                <td>
                  <span :class="['badge', transaction.transaction_type === 'BUY' ? 'bg-danger' : 'bg-success']">
                    {{ transaction.transaction_type === 'BUY' ? '买入' : '卖出' }}
                  </span>
                </td>
                <td>
                  <template v-if="transaction.details && transaction.details.length">
                    <div v-for="(detail, index) in transaction.details" :key="index" class="text-nowrap">
                      {{ formatNumber(detail.quantity, 0) }}股@{{ formatNumber(detail.price, 3) }}
                    </div>
                  </template>
                  <template v-else>
                    {{ formatNumber(transaction.total_quantity, 0) }}股@{{ formatNumber(transaction.total_amount / transaction.total_quantity, 3) }}
                  </template>
                </td>
                <td class="text-end">{{ formatNumber(transaction.total_amount / transaction.total_quantity, 3) }}</td>
                <td class="text-end">{{ formatNumber(transaction.total_amount) }}</td>
                <td class="text-end">{{ formatNumber(transaction.broker_fee) }}</td>
                <td class="text-end">{{ formatNumber(transaction.transaction_levy) }}</td>
                <td class="text-end">{{ formatNumber(transaction.stamp_duty) }}</td>
                <td class="text-end">{{ formatNumber(transaction.trading_fee) }}</td>
                <td class="text-end">{{ formatNumber(transaction.deposit_fee) }}</td>
                <td class="text-end">{{ formatNumber(transaction.total_fees) }}</td>
                <td class="text-end" :class="{'text-danger': transaction.transaction_type === 'BUY', 'text-success': transaction.transaction_type === 'SELL'}">
                  {{ transaction.transaction_type === 'BUY' ? '-' : '' }}{{ formatNumber(transaction.net_amount) }}
                  <template v-if="transaction.deposit_fee > 0">
                    <br>
                    <small :class="{'text-danger': transaction.transaction_type === 'BUY', 'text-success': transaction.transaction_type === 'SELL'}">
                      ({{ transaction.transaction_type === 'BUY' ? '-' : '' }}{{ formatNumber(transaction.net_amount - transaction.deposit_fee) }})
                    </small>
                  </template>
                </td>
                <td>
                  <div class="d-flex justify-content-end gap-1">
                    <button 
                      class="btn btn-link btn-xs text-primary" 
                      @click="editTransaction(transaction)" 
                      title="编辑"
                      style="min-width: 32px; padding: 0.15rem 0.5rem; font-size: 0.75rem; border-radius: 0.2rem;"
                    >
                      编辑
                    </button>
                    <button 
                      class="btn btn-link btn-xs text-danger" 
                      @click="confirmDelete(transaction)" 
                      title="删除"
                      style="min-width: 32px; padding: 0.15rem 0.5rem; font-size: 0.75rem; border-radius: 0.2rem;"
                    >
                      删除
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
          </tbody>
        </table>
      </div>

      <!-- 分页 -->
      <div v-if="totalPages > 1" class="card-footer d-flex justify-content-center">
        <nav>
          <ul class="pagination pagination-sm mb-0">
            <li class="page-item" :class="{ disabled: currentPage === 1 }">
              <a class="page-link" href="#" @click.prevent="changePage(currentPage - 1)">
                <i class="bi bi-chevron-left"></i>
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
                <i class="bi bi-chevron-right"></i>
              </a>
            </li>
          </ul>
        </nav>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import useMessage from '../composables/useMessage'
import DateInput from '../components/DateInput.vue'
import StockSelector from '../components/StockSelector.vue'
import TransactionItem from '../components/TransactionItem.vue'

const router = useRouter()
const { message } = useMessage()
const loading = ref(false)
const showDialog = ref(false)
const editData = ref(null)
const transactions = ref([])
const allStocks = ref([])
const currentPage = ref(1)
const totalPages = ref(1)
const totalItems = ref(0)
const pageSize = 15
const searchVisible = ref(true)

// 搜索表单
const searchForm = ref({
  startDate: '',
  endDate: '',
  market: '',
  stockCodes: [],
  transactionCode: ''
})

// 日期处理
const startDateDisplayValue = ref('')
const endDateDisplayValue = ref('')

// 引用
const startDate = ref(null)
const endDate = ref(null)
const transactionCode = ref(null)
const market = ref(null)
const searchBtn = ref(null)

// 焦点控制
const focusNext = (event, target) => {
  event.preventDefault()
  switch(target) {
    case 'endDate':
      endDate.value?.focus()
      break
    case 'market':
      market.value?.focus()
      break
    case 'transactionCode':
      transactionCode.value?.focus()
      break
    case 'search':
      searchBtn.value?.focus()
      search()
      break
  }
}

const handleStartDateInput = (event) => {
  const value = event.target.value
  startDateDisplayValue.value = value
  searchForm.value.startDate = value
}

const handleStartDateBlur = () => {
  if (!startDateDisplayValue.value) {
    searchForm.value.startDate = ''
    return
  }

  const value = startDateDisplayValue.value.trim()
  let formattedDate = null

  // 处理快捷输入
  if (/^[a-zA-Z]+$/.test(value)) {
    const now = new Date()
    switch (value.toLowerCase()) {
      case 't':
      case 'today':
        formattedDate = formatDate(now)
        break
      case 'y':
      case 'yday':
        now.setDate(now.getDate() - 1)
        formattedDate = formatDate(now)
        break
      case 'tm':
      case 'tmr':
        now.setDate(now.getDate() + 1)
        formattedDate = formatDate(now)
        break
    }
  }

  // 处理相对日期（如：+7 表示7天后，-7 表示7天前）
  if (/^[+-]\d+$/.test(value)) {
    const days = parseInt(value)
    const date = new Date()
    date.setDate(date.getDate() + days)
    formattedDate = formatDate(date)
  }

  // 处理 MMDD 格式
  if (/^\d{3,4}$/.test(value)) {
    const now = new Date()
    const year = now.getFullYear()
    let month, day

    if (value.length === 3) {
      month = parseInt(value[0])
      day = parseInt(value.slice(1))
    } else {
      month = parseInt(value.slice(0, 2))
      day = parseInt(value.slice(2))
    }

    if (month >= 1 && month <= 12 && day >= 1 && day <= 31) {
      const date = new Date(year, month - 1, day)
      if (isValidDate(date)) {
        formattedDate = formatDate(date)
      }
    }
  }

  // 处理 M-D、M.D 或 M/D 格式
  const separators = ['-', '.', '/']
  for (const separator of separators) {
    if (value.includes(separator)) {
      const [month, day] = value.split(separator).map(Number)
      const now = new Date()
      const year = now.getFullYear()

      if (month >= 1 && month <= 12 && day >= 1 && day <= 31) {
        const date = new Date(year, month - 1, day)
        if (isValidDate(date)) {
          formattedDate = formatDate(date)
          break
        }
      }
    }
  }

  // 处理标准格式
  if (!formattedDate) {
    const date = new Date(value)
    if (isValidDate(date)) {
      formattedDate = formatDate(date)
    }
  }

  if (formattedDate) {
    startDateDisplayValue.value = formattedDate
    searchForm.value.startDate = formattedDate
    // 如果开始日期大于结束日期，更新结束日期
    if (searchForm.value.endDate && formattedDate > searchForm.value.endDate) {
      searchForm.value.endDate = formattedDate
      endDateDisplayValue.value = formattedDate
    }
  }
}

const handleEndDateInput = (event) => {
  const value = event.target.value
  endDateDisplayValue.value = value
  searchForm.value.endDate = value
}

const handleEndDateBlur = () => {
  if (!endDateDisplayValue.value) {
    searchForm.value.endDate = ''
    return
  }

  const value = endDateDisplayValue.value.trim()
  let formattedDate = null

  // 处理快捷输入
  if (/^[a-zA-Z]+$/.test(value)) {
    const now = new Date()
    switch (value.toLowerCase()) {
      case 't':
      case 'today':
        formattedDate = formatDate(now)
        break
      case 'y':
      case 'yday':
        now.setDate(now.getDate() - 1)
        formattedDate = formatDate(now)
        break
      case 'tm':
      case 'tmr':
        now.setDate(now.getDate() + 1)
        formattedDate = formatDate(now)
        break
    }
  }

  // 处理相对日期（如：+7 表示7天后，-7 表示7天前）
  if (/^[+-]\d+$/.test(value)) {
    const days = parseInt(value)
    const date = new Date()
    date.setDate(date.getDate() + days)
    formattedDate = formatDate(date)
  }

  // 处理 MMDD 格式
  if (/^\d{3,4}$/.test(value)) {
    const now = new Date()
    const year = now.getFullYear()
    let month, day

    if (value.length === 3) {
      month = parseInt(value[0])
      day = parseInt(value.slice(1))
    } else {
      month = parseInt(value.slice(0, 2))
      day = parseInt(value.slice(2))
    }

    if (month >= 1 && month <= 12 && day >= 1 && day <= 31) {
      const date = new Date(year, month - 1, day)
      if (isValidDate(date)) {
        formattedDate = formatDate(date)
      }
    }
  }

  // 处理 M-D、M.D 或 M/D 格式
  const separators = ['-', '.', '/']
  for (const separator of separators) {
    if (value.includes(separator)) {
      const [month, day] = value.split(separator).map(Number)
      const now = new Date()
      const year = now.getFullYear()

      if (month >= 1 && month <= 12 && day >= 1 && day <= 31) {
        const date = new Date(year, month - 1, day)
        if (isValidDate(date)) {
          formattedDate = formatDate(date)
          break
        }
      }
    }
  }

  // 处理标准格式
  if (!formattedDate) {
    const date = new Date(value)
    if (isValidDate(date)) {
      formattedDate = formatDate(date)
    }
  }

  if (formattedDate) {
    endDateDisplayValue.value = formattedDate
    searchForm.value.endDate = formattedDate
    // 如果结束日期小于开始日期，更新开始日期
    if (searchForm.value.startDate && formattedDate < searchForm.value.startDate) {
      searchForm.value.startDate = formattedDate
      startDateDisplayValue.value = formattedDate
    }
  }
}

// 验证日期是否有效
const isValidDate = (date) => {
  return date instanceof Date && !isNaN(date)
}

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
    if (searchForm.value.startDate) params.append('start_date', searchForm.value.startDate)
    if (searchForm.value.endDate) params.append('end_date', searchForm.value.endDate)
    if (searchForm.value.market) params.append('market', searchForm.value.market)
    if (searchForm.value.stockCodes.length > 0) {
      searchForm.value.stockCodes.forEach(code => params.append('stock_codes[]', code))
    }
    if (searchForm.value.transactionCode) {
      params.append('transaction_code', searchForm.value.transactionCode)
    }
    params.append('page', currentPage.value)
    params.append('per_page', pageSize)
    // 添加时间戳参数避免缓存
    params.append('_t', Date.now())
    
    const response = await axios.get('/api/stock/transactions/', { 
      params,
      headers: {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content'),
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      withCredentials: true
    })
    
    if (response.data.success) {
      transactions.value = response.data.data.items
      totalPages.value = response.data.data.pages
      
      // 如果当前页大于总页数，跳转到最后一页
      if (currentPage.value > totalPages.value && totalPages.value > 0) {
        currentPage.value = totalPages.value
        await fetchTransactions()
        return
      }
    }
  } catch (error) {
    if (error.response?.status === 401) {
      message.error('登录已过期，请重新登录')
      router.push('/login')
      return
    }
    message.error('获取交易记录失败，请稍后重试')
  } finally {
    loading.value = false
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

const searchAndClear = () => {
  search()
  searchForm.value.transactionCode = ''
}

const resetSearch = () => {
  searchForm.value = {
    startDate: '',
    endDate: '',
    market: '',
    stockCodes: [],
    transactionCode: ''
  }
  startDateDisplayValue.value = ''
  endDateDisplayValue.value = ''
  search()
}

// 删除交易记录
const confirmDelete = async (transaction) => {
  if (!window.confirm('确定要删除这条交易记录吗？')) {
    return
  }
  
  try {
    loading.value = true
    const response = await axios.delete(`/api/stock/transactions/${transaction.id}`, {
      headers: {
        'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content'),
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      withCredentials: true
    })
    
    if (response.data.success) {
      message.success('交易记录删除成功')
      
      // 如果当前页只有一条记录，且不是第一页，则跳转到上一页
      if (transactions.value.length === 1 && currentPage.value > 1) {
        currentPage.value--
      }
      
      // 重新获取数据
      await fetchTransactions()
      await fetchStocks()
    } else {
      throw new Error(response.data.message || '删除失败')
    }
  } catch (error) {
    console.error('删除交易记录失败:', error)
    if (error.response?.status === 401) {
      message.error('登录已过期，请重新登录')
      router.push('/login')
    } else if (error.response?.status === 404) {
      message.error('交易记录不存在或已被删除')
      // 刷新列表以获取最新数据
      await fetchTransactions()
    } else {
      message.error(error.response?.data?.message || error.message || '删除失败，请稍后重试')
    }
  } finally {
    loading.value = false
  }
}

// 编辑交易记录
const editTransaction = async (transaction) => {
  try {
    const response = await axios.get(`/api/stock/transactions/${transaction.id}`)
    if (!response.data.success) {
      throw new Error('交易记录不存在或已被删除')
    }
    router.push(`/transactions/edit/${transaction.id}`)
  } catch (error) {
    showToast(error.message || '编辑交易记录失败，请稍后重试', 'danger')
  }
}

// 添加交易记录
const addTransaction = () => {
  router.push('/transactions/add')
}

// 工具函数
const formatDate = (date) => {
  if (!date) return '-'
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

// 切换页码
const changePage = (page) => {
  if (page < 1 || page > totalPages.value || page === currentPage.value) return
  currentPage.value = page
  fetchTransactions()
}

// 计算显示的页码范围
const displayedPages = computed(() => {
  const delta = 2
  const range = []
  let left = currentPage.value - delta
  let right = currentPage.value + delta + 1
  
  // 处理左边界
  if (left < 1) {
    left = 1
    right = Math.min(1 + delta * 2, totalPages.value + 1)
  }
  
  // 处理右边界
  if (right > totalPages.value) {
    right = totalPages.value + 1
    left = Math.max(1, totalPages.value - delta * 2)
  }
  
  // 生成页码数组
  for (let i = left; i < right; i++) {
    range.push(i)
  }
  
  // 添加省略号
  if (left > 1) {
    range.unshift('...')
    range.unshift(1)
  }
  if (right <= totalPages.value) {
    range.push('...')
    range.push(totalPages.value)
  }
  
  return range
})

// 在 script setup 部分修改计算属性
const sortedTransactions = computed(() => {
  return [...transactions.value].sort((a, b) => {
    // 首先按交易日期降序排序
    const dateA = new Date(a.transaction_date).getTime()
    const dateB = new Date(b.transaction_date).getTime()
    if (dateA !== dateB) {
      return dateB - dateA
    }
    
    // 如果日期相同，按创建时间降序排序
    const createdAtA = new Date(a.created_at).getTime()
    const createdAtB = new Date(b.created_at).getTime()
    if (createdAtA !== createdAtB) {
      return createdAtB - createdAtA
    }
    
    // 如果创建时间也相同，按ID降序排序
    return b.id - a.id
  })
})

// 初始化
onMounted(() => {
  fetchStocks()
  fetchTransactions()
})
</script>

<style scoped>
.card {
  margin: 1.5rem auto;
  max-width: 1400px;
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
  border-radius: 0.5rem;
  background-color: #fff;
}

.card-header {
  background-color: #fff;
  border-bottom: 1px solid #dee2e6;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem 0.5rem 0 0;
}

.card-body {
  padding: 0.75rem;
}

.card-body.p-0 {
  padding: 0 !important;
}

.card-footer {
  background-color: #fff;
  border-top: 1px solid #dee2e6;
  padding: 0.75rem 1rem;
  border-radius: 0 0 0.5rem 0.5rem;
}

.table {
  margin-bottom: 0;
  font-size: 0.8125rem;
}

.table th {
  white-space: nowrap;
  font-weight: 500;
  padding: 0.4rem;
  background-color: #f8f9fa;
  color: #495057;
  border-bottom: 2px solid #dee2e6;
  font-size: 0.8125rem;
}

.table td {
  padding: 0.4rem;
  vertical-align: middle;
  border-bottom: 1px solid #dee2e6;
  white-space: nowrap;
  font-size: 0.8125rem;
}

.text-muted {
  font-size: 0.75rem;
}

.badge {
  padding: 0.2rem 0.4rem;
  font-weight: normal;
  font-size: 0.75rem;
}

.bg-danger {
  background-color: #e6071d !important;
}

.bg-success {
  background-color: #549359 !important;
}

.btn-group .btn {
  padding: 0.25rem 0.5rem;
}

.btn-group .btn i {
  font-size: 0.875rem;
}

.text-danger {
  color: #e6071d !important;
}

.text-success {
  color: #549359 !important;
}

.pagination {
  margin-bottom: 0;
}

.page-link {
  padding: 0.2rem 0.4rem;
  font-size: 0.75rem;
  min-width: 26px;
  text-align: center;
}

.page-link:hover {
  color: #0a58ca;
  background-color: #e9ecef;
  border-color: #dee2e6;
}

.page-item.active .page-link {
  background-color: #0d6efd;
  border-color: #0d6efd;
  color: #fff;
}

.page-item.disabled .page-link {
  color: #6c757d;
  pointer-events: none;
  background-color: #fff;
  border-color: #dee2e6;
}

/* 搜索表单样式优化 */
.form-control,
.form-select {
  padding: 0.25rem 0.5rem;
  font-size: 0.8125rem;
  height: calc(1.75rem + 2px);
  line-height: 1.2;
}

.form-label {
  font-size: 0.8125rem;
  margin-bottom: 0.25rem;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.8125rem;
  height: calc(1.75rem + 2px);
  line-height: 1.2;
}

/* 搜索区域间距优化 */
.row.g-2 {
  --bs-gutter-x: 0.5rem;
  --bs-gutter-y: 0.5rem;
  margin-right: 0;
  margin-left: 0;
}

.card-body.border-bottom {
  padding: 0.75rem;
}

/* 调整搜索区域的下拉框样式 */
.stock-selector {
  min-width: unset !important;
}

.stock-selector .dropdown-menu {
  min-width: 300px;
}

/* 操作按钮样式优化 */
.btn-xs {
  font-size: 0.75rem;
  line-height: 1.2;
  padding: 0.15rem 0.4rem;
  min-width: 36px;
}

.btn-link.btn-xs {
  padding: 0.15rem 0.4rem;
}

/* 分页样式优化 */
.pagination {
  margin-bottom: 0;
}

.page-link {
  padding: 0.2rem 0.4rem;
  font-size: 0.75rem;
  min-width: 26px;
  text-align: center;
}

/* 表格内容对齐和间距优化 */
.table td.text-end,
.table th.text-end {
  padding-right: 0.5rem;
}

.table td.text-center,
.table th.text-center {
  padding-left: 0.25rem;
  padding-right: 0.25rem;
}

/* 操作列按钮组样式 */
.d-flex.gap-1 {
  gap: 0.25rem !important;
}

/* 调整股票代码和名称的显示 */
td.text-center small {
  display: block;
  line-height: 1.2;
  margin-top: 0.1rem;
}

/* 调整成交明细的显示 */
td > div {
  line-height: 1.2;
  margin: 0;
  white-space: nowrap;
}

.text-nowrap {
  white-space: nowrap;
}
</style> 