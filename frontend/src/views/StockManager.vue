<template>
  <div class="card">
    <div class="card-header d-flex justify-content-between align-items-center">
      <h4 class="mb-0">股票管理</h4>
      <div class="btn-group">
        <button type="button" class="btn btn-sm btn-outline-secondary" @click="toggleSearch">
          <i :class="['bi', searchVisible ? 'bi-chevron-up' : 'bi-search']"></i>
          {{ searchVisible ? '收起' : '搜索' }}
        </button>
        <button type="button" class="btn btn-sm btn-outline-primary" @click="refreshPrices" :disabled="loading">
          <i :class="['bi', loading ? 'bi-arrow-clockwise bi-spin' : 'bi-arrow-clockwise']"></i>
          刷新价格
        </button>
        <button type="button" class="btn btn-sm btn-primary" @click="showAddModal">
          <i class="bi bi-plus-lg"></i> 添加股票
        </button>
      </div>
    </div>

    <!-- 搜索表单 -->
    <div v-show="searchVisible" class="card-body border-bottom">
      <form @submit.prevent="search" class="row g-3">
        <div class="col-md-2">
          <label class="form-label small">市场</label>
          <select class="form-select form-select-sm" v-model="searchForm.market">
            <option value="">全部</option>
            <option value="HK">HK</option>
            <option value="USA">USA</option>
          </select>
        </div>
        <div class="col-md-6">
          <label class="form-label small">搜索</label>
          <input type="text" class="form-control form-control-sm" v-model="searchForm.keyword"
                 placeholder="输入代码或名称搜索">
        </div>
        <div class="col-md-2 d-flex align-items-end">
          <button type="submit" class="btn btn-sm btn-primary w-100" :disabled="loading">查询</button>
        </div>
        <div class="col-md-2 d-flex align-items-end">
          <button type="button" class="btn btn-sm btn-outline-secondary w-100" @click="resetSearch">重置</button>
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
              <th>代码</th>
              <th>名称</th>
              <th>谷歌查询代码</th>
              <th class="text-end">当前股价</th>
              <th>更新时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <template v-if="!loading">
              <template v-for="stock in stocks" :key="stock.id">
                <tr>
                  <td class="text-center">
                    <button class="btn btn-sm btn-outline-secondary expand-btn" @click="toggleDetails(stock)">
                      <i class="bi" :class="expandedStocks.includes(stock.id) ? 'bi-dash-circle' : 'bi-plus-circle'"></i>
                    </button>
                  </td>
                  <td>{{ stock.market }}</td>
                  <td>{{ stock.code }}</td>
                  <td>
                    <span v-if="!stock.editing" @dblclick="startEdit(stock)">{{ stock.name || '-' }}</span>
                    <div v-else class="input-group input-group-sm">
                      <input type="text" class="form-control form-control-sm" v-model="stock.editName"
                             @keyup.enter="saveEdit(stock)" @keyup.esc="cancelEdit(stock)">
                      <button class="btn btn-success" @click="saveEdit(stock)">
                        <i class="bi bi-check"></i>
                      </button>
                      <button class="btn btn-outline-secondary" @click="cancelEdit(stock)">
                        <i class="bi bi-x"></i>
                      </button>
                    </div>
                  </td>
                  <td>
                    <span v-if="!stock.editingFullName" @dblclick="startEditFullName(stock)">
                      {{ stock.full_name || '-' }}
                    </span>
                    <div v-else class="input-group input-group-sm">
                      <input type="text" class="form-control form-control-sm" v-model="stock.editFullName"
                             @keyup.enter="saveEditFullName(stock)" @keyup.esc="cancelEditFullName(stock)">
                      <button class="btn btn-success" @click="saveEditFullName(stock)">
                        <i class="bi bi-check"></i>
                      </button>
                      <button class="btn btn-outline-secondary" @click="cancelEditFullName(stock)">
                        <i class="bi bi-x"></i>
                      </button>
                    </div>
                  </td>
                  <td class="text-end">
                    {{ formatNumber(stock.current_price, 3) }}
                    <small v-if="stock.current_price" class="text-muted">
                      {{ stock.market === 'HK' ? 'HKD' : 'USD' }}
                    </small>
                  </td>
                  <td>{{ formatDateTime(stock.updated_at) }}</td>
                  <td>
                    <div class="btn-group btn-group-sm">
                      <button class="btn btn-outline-primary" @click="showEditModal(stock)">
                        <i class="bi bi-pencil"></i>
                      </button>
                      <button class="btn btn-outline-danger" @click="confirmDelete(stock)">
                        <i class="bi bi-trash"></i>
                      </button>
                    </div>
                  </td>
                </tr>
                <!-- 交易明细行 -->
                <tr v-if="expandedStocks.includes(stock.id)">
                  <td colspan="8" class="p-0">
                    <div class="transaction-details">
                      <table class="table table-sm table-bordered mb-0">
                        <thead class="table-light">
                          <tr>
                            <th>交易日期</th>
                            <th>交易编号</th>
                            <th>类型</th>
                            <th class="text-end">数量</th>
                            <th class="text-end">价格</th>
                            <th class="text-end">金额</th>
                            <th class="text-end">费用</th>
                            <th class="text-end">汇率</th>
                            <th class="text-end">港币金额</th>
                          </tr>
                        </thead>
                        <tbody>
                          <template v-if="transactionDetails[stock.id]">
                            <tr v-for="detail in transactionDetails[stock.id]" :key="detail.id">
                              <td>{{ formatDate(detail.transaction_date) }}</td>
                              <td>{{ detail.transaction_code }}</td>
                              <td>{{ detail.transaction_type === 'BUY' ? '买入' : '卖出' }}</td>
                              <td class="text-end">{{ formatNumber(detail.total_quantity, 0) }}</td>
                              <td class="text-end">
                                <template v-for="(d, index) in detail.details" :key="index">
                                  {{ formatNumber(d.price, 3) }}<br v-if="index < detail.details.length - 1">
                                </template>
                              </td>
                              <td class="text-end">{{ formatNumber(detail.total_amount) }}</td>
                              <td class="text-end">{{ formatNumber(detail.total_fees_hkd) }}</td>
                              <td class="text-end">{{ formatNumber(detail.exchange_rate, 4) }}</td>
                              <td class="text-end">{{ formatNumber(detail.total_amount_hkd) }}</td>
                            </tr>
                          </template>
                          <tr v-else>
                            <td colspan="9" class="text-center py-2">
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
            <tr v-else>
              <td colspan="7" class="text-center py-3">
                <div class="spinner-border spinner-border-sm text-primary me-2"></div>
                加载中...
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 分页导航 -->
      <div v-if="pagination.total_pages > 1" class="card-footer d-flex justify-content-center">
        <nav>
          <ul class="pagination pagination-sm mb-0">
            <li :class="['page-item', { disabled: !pagination.has_prev }]">
              <a class="page-link" href="#" @click.prevent="changePage(pagination.current_page - 1)">
                <i class="bi bi-chevron-left"></i>
              </a>
            </li>
            
            <template v-for="page in pageNumbers" :key="page">
              <li v-if="page === '...'" class="page-item disabled">
                <span class="page-link">...</span>
              </li>
              <li v-else :class="['page-item', { active: page === pagination.current_page }]">
                <a class="page-link" href="#" @click.prevent="changePage(page)">{{ page }}</a>
              </li>
            </template>
            
            <li :class="['page-item', { disabled: !pagination.has_next }]">
              <a class="page-link" href="#" @click.prevent="changePage(pagination.current_page + 1)">
                <i class="bi bi-chevron-right"></i>
              </a>
            </li>
          </ul>
        </nav>
      </div>
    </div>

    <!-- 添加/编辑股票模态框 -->
    <div class="modal fade" id="stockModal" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ editingStock ? '编辑股票' : '添加股票' }}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="submitStock">
              <div class="mb-3">
                <label class="form-label">市场</label>
                <select class="form-select" v-model="stockForm.market" :disabled="!!editingStock"
                        :class="{ 'is-invalid': stockErrors.market }">
                  <option value="HK">HK</option>
                  <option value="USA">USA</option>
                </select>
                <div class="invalid-feedback">{{ stockErrors.market }}</div>
              </div>
              <div class="mb-3">
                <label class="form-label">代码</label>
                <input type="text" class="form-control" v-model="stockForm.code" :disabled="!!editingStock"
                       :class="{ 'is-invalid': stockErrors.code }">
                <div class="invalid-feedback">{{ stockErrors.code }}</div>
              </div>
              <div class="mb-3">
                <label class="form-label">名称</label>
                <input type="text" class="form-control" v-model="stockForm.name"
                       :class="{ 'is-invalid': stockErrors.name }">
                <div class="invalid-feedback">{{ stockErrors.name }}</div>
              </div>
              <div class="mb-3">
                <label class="form-label">谷歌查询代码</label>
                <input type="text" class="form-control" v-model="stockForm.fullName">
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
            <button type="button" class="btn btn-primary" @click="submitStock" :disabled="submitting">
              <i :class="['bi', submitting ? 'bi-arrow-clockwise bi-spin' : 'bi-save']"></i>
              保存
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'
import { Modal } from 'bootstrap'

// 状态
const loading = ref(false)
const submitting = ref(false)
const searchVisible = ref(false)
const stocks = ref([])
const editingStock = ref(null)
const stockModal = ref(null)
const pagination = reactive({
  current_page: 1,
  total_pages: 1,
  has_prev: false,
  has_next: false
})

// 表单数据
const searchForm = reactive({
  market: '',
  keyword: ''
})

const stockForm = reactive({
  market: 'HK',
  code: '',
  name: '',
  fullName: ''
})

const stockErrors = reactive({
  market: '',
  code: '',
  name: ''
})

// 计算分页页码
const pageNumbers = computed(() => {
  const current = pagination.current_page
  const total = pagination.total_pages
  const delta = 2
  const range = []
  const rangeWithDots = []
  let l

  for (let i = 1; i <= total; i++) {
    if (i === 1 || i === total || (i >= current - delta && i <= current + delta)) {
      range.push(i)
    }
  }

  range.forEach(i => {
    if (l) {
      if (i - l === 2) {
        rangeWithDots.push(l + 1)
      } else if (i - l !== 1) {
        rangeWithDots.push('...')
      }
    }
    rangeWithDots.push(i)
    l = i
  })

  return rangeWithDots
})

// 格式化函数
const formatDateTime = (dateStr) => {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  }).replace(/\//g, '-')
}

const formatNumber = (value, decimals = 2) => {
  if (value === null || value === undefined) return '-'
  return Number(value).toLocaleString('zh-HK', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })
}

// 搜索相关方法
const toggleSearch = () => {
  searchVisible.value = !searchVisible.value
}

// 获取数据
const fetchData = async (page = 1) => {
  if (loading.value) return
  
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('page', page)
    if (searchForm.market) params.append('market', searchForm.market)
    if (searchForm.keyword) params.append('keyword', searchForm.keyword)
    
    const response = await axios.get(`/api/stock/stocks?${params.toString()}`)
    if (response.data.success) {
      stocks.value = response.data.data.items.map(stock => ({
        ...stock,
        editing: false,
        editName: stock.name,
        editingFullName: false,
        editFullName: stock.full_name
      }))
      Object.assign(pagination, response.data.data.pagination)
    } else {
      throw new Error(response.data.error)
    }
  } catch (error) {
    console.error('获取股票列表失败:', error)
    // TODO: 显示错误提示
  } finally {
    loading.value = false
  }
}

// 刷新价格
const refreshPrices = async () => {
  if (loading.value) return
  
  loading.value = true
  try {
    const response = await axios.get('/api/stocks/prices')
    if (response.data.success) {
      // 更新股票价格
      const priceMap = new Map(response.data.data.map(item => [
        `${item.market}:${item.code}`,
        item.current_price
      ]))
      
      stocks.value.forEach(stock => {
        const key = `${stock.market}:${stock.code}`
        if (priceMap.has(key)) {
          stock.current_price = priceMap.get(key)
          stock.updated_at = new Date().toISOString()
        }
      })
    } else {
      throw new Error(response.data.error)
    }
  } catch (error) {
    console.error('刷新价格失败:', error)
    // TODO: 显示错误提示
  } finally {
    loading.value = false
  }
}

// 搜索
const search = () => {
  pagination.current_page = 1
  fetchData(1)
}

// 重置搜索
const resetSearch = () => {
  searchForm.market = ''
  searchForm.keyword = ''
  search()
}

// 分页
const changePage = (page) => {
  if (page < 1 || page > pagination.total_pages) return
  pagination.current_page = page
  fetchData(page)
}

// 模态框相关方法
const initModal = () => {
  stockModal.value = new Modal(document.getElementById('stockModal'))
}

const showAddModal = () => {
  editingStock.value = null
  Object.assign(stockForm, {
    market: 'HK',
    code: '',
    name: '',
    fullName: ''
  })
  Object.assign(stockErrors, {
    market: '',
    code: '',
    name: ''
  })
  stockModal.value.show()
}

const showEditModal = (stock) => {
  editingStock.value = stock
  Object.assign(stockForm, {
    market: stock.market,
    code: stock.code,
    name: stock.name,
    fullName: stock.full_name
  })
  Object.assign(stockErrors, {
    market: '',
    code: '',
    name: ''
  })
  stockModal.value.show()
}

// 表单提交
const validateForm = () => {
  let isValid = true
  stockErrors.market = ''
  stockErrors.code = ''
  stockErrors.name = ''

  if (!stockForm.market) {
    stockErrors.market = '请选择市场'
    isValid = false
  }

  if (!stockForm.code) {
    stockErrors.code = '请输入股票代码'
    isValid = false
  }

  if (!stockForm.name) {
    stockErrors.name = '请输入股票名称'
    isValid = false
  }

  return isValid
}

const submitStock = async () => {
  if (!validateForm() || submitting.value) return
  
  submitting.value = true
  try {
    const data = {
      market: stockForm.market,
      code: stockForm.code,
      name: stockForm.name,
      full_name: stockForm.fullName
    }
    
    let response
    if (editingStock.value) {
      response = await axios.put(`/api/stocks/${editingStock.value.id}`, data)
    } else {
      response = await axios.post('/api/stocks', data)
    }
    
    if (response.data.success) {
      stockModal.value.hide()
      // 重新加载数据
      fetchData(pagination.current_page)
    } else {
      throw new Error(response.data.error)
    }
  } catch (error) {
    console.error('保存股票失败:', error)
    // TODO: 显示错误提示
  } finally {
    submitting.value = false
  }
}

// 行内编辑相关方法
const startEdit = (stock) => {
  stock.editing = true
  stock.editName = stock.name
}

const saveEdit = async (stock) => {
  if (!stock.editName) {
    // TODO: 显示错误提示
    return
  }
  
  try {
    const response = await axios.put(`/api/stocks/${stock.id}`, {
      market: stock.market,
      code: stock.code,
      name: stock.editName,
      full_name: stock.full_name
    })
    
    if (response.data.success) {
      stock.name = stock.editName
      stock.editing = false
    } else {
      throw new Error(response.data.error)
    }
  } catch (error) {
    console.error('保存股票名称失败:', error)
    // TODO: 显示错误提示
  }
}

const cancelEdit = (stock) => {
  stock.editing = false
  stock.editName = stock.name
}

const startEditFullName = (stock) => {
  stock.editingFullName = true
  stock.editFullName = stock.full_name
}

const saveEditFullName = async (stock) => {
  try {
    const response = await axios.put(`/api/stocks/${stock.id}`, {
      market: stock.market,
      code: stock.code,
      name: stock.name,
      full_name: stock.editFullName
    })
    
    if (response.data.success) {
      stock.full_name = stock.editFullName
      stock.editingFullName = false
    } else {
      throw new Error(response.data.error)
    }
  } catch (error) {
    console.error('保存谷歌查询代码失败:', error)
    // TODO: 显示错误提示
  }
}

const cancelEditFullName = (stock) => {
  stock.editingFullName = false
  stock.editFullName = stock.full_name
}

// 删除确认
const confirmDelete = async (stock) => {
  if (!confirm(`确定要删除这支股票吗？\n${stock.market}:${stock.code}`)) return
  
  try {
    const response = await axios.delete(`/api/stocks/${stock.id}`)
    if (response.data.success) {
      // 重新加载当前页数据
      fetchData(pagination.current_page)
    } else {
      throw new Error(response.data.error)
    }
  } catch (error) {
    console.error('删除股票失败:', error)
    // TODO: 显示错误提示
  }
}

// 添加展开/收起状态管理
const expandedStocks = ref([])
const transactionDetails = ref({})

// 添加切换明细显示方法
const toggleDetails = async (stock) => {
  const index = expandedStocks.value.indexOf(stock.id)
  if (index === -1) {
    // 展开并获取数据
    expandedStocks.value.push(stock.id)
    
    try {
      const params = new URLSearchParams()
      params.append('market', stock.market)
      params.append('stock_codes[]', stock.code)
      
      const response = await axios.get(`/api/profit/?${params.toString()}`)
      console.log('获取到的响应:', response.data)
      
      if (response.data.success) {
        const key = `${stock.market}-${stock.code}`
        if (response.data.data.transaction_details && response.data.data.transaction_details[key]) {
          transactionDetails.value[stock.id] = response.data.data.transaction_details[key]
        } else {
          transactionDetails.value[stock.id] = []
        }
      }
    } catch (error) {
      console.error('获取交易明细失败:', error)
      transactionDetails.value[stock.id] = []
    }
  } else {
    // 收起
    expandedStocks.value.splice(index, 1)
  }
}

// 添加日期格式化方法
const formatDate = (date) => {
  return new Date(date).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).replace(/\//g, '-')
}

// 初始化
onMounted(() => {
  initModal()
  fetchData(1)
})
</script>

<style scoped>
.table th {
  white-space: nowrap;
  font-size: 0.875rem;
}

.btn-group-sm > .btn {
  padding: 0.25rem 0.5rem;
}

.pagination {
  margin-bottom: 0;
}

.page-link {
  padding: 0.375rem 0.75rem;
}

.modal-body {
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}

.input-group-sm > .form-control {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
}

.input-group-sm > .btn {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
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

.expand-btn .bi {
  font-size: 1.25rem;
}

.expand-btn .bi-plus-circle {
  color: #0d6efd;
}

.expand-btn .bi-dash-circle {
  color: #dc3545;
}

.expand-btn:hover .bi-plus-circle {
  color: #0a58ca;
}

.expand-btn:hover .bi-dash-circle {
  color: #b02a37;
}

/* 按钮中的图标通用样式 */
.btn .bi {
  font-size: 1rem;
  margin-right: 0.25rem;
}

.btn-group-sm .btn .bi {
  font-size: 0.875rem;
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

/* 交易明细样式 */
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
</style> 