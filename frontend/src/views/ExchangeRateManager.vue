<template>
  <div class="card">
    <div class="card-header d-flex justify-content-between align-items-center">
      <h4 class="mb-0">汇率管理</h4>
      <div class="btn-group">
        <button type="button" class="btn btn-sm btn-outline-secondary" @click="toggleSearch">
          <i :class="['fas', searchVisible ? 'fa-chevron-up' : 'fa-search']"></i>
          {{ searchVisible ? '收起' : '搜索' }}
        </button>
        <button type="button" class="btn btn-sm btn-outline-secondary" @click="fetchMissingRates">
          <i class="fas fa-sync-alt"></i> 获取缺失汇率
        </button>
        <button type="button" class="btn btn-sm btn-primary" @click="openAddModal">
          <i class="fas fa-plus"></i> 添加汇率
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
          <label class="form-label small">货币</label>
          <select class="form-select form-select-sm" v-model="searchForm.currency">
            <option value="">全部</option>
            <option value="USD">USD</option>
            <option value="CNY">CNY</option>
          </select>
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
              <th>货币</th>
              <th class="text-end">汇率</th>
              <th>数据来源</th>
              <th>更新时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <template v-if="!loading">
              <tr v-for="rate in exchangeRates" :key="rate.id">
                <td>{{ formatDate(rate.rate_date) }}</td>
                <td>{{ rate.currency }}/HKD</td>
                <td class="text-end">{{ formatNumber(rate.rate, 4) }}</td>
                <td>{{ rate.source || '-' }}</td>
                <td>{{ formatDateTime(rate.created_at) }}</td>
                <td>
                  <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" @click="openEditModal(rate)">
                      <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-outline-danger" @click="confirmDelete(rate)">
                      <i class="fas fa-trash"></i>
                    </button>
                  </div>
                </td>
              </tr>
            </template>
            <tr v-else>
              <td colspan="6" class="text-center py-3">
                <div class="spinner-border spinner-border-sm text-primary me-2"></div>
                加载中...
              </td>
            </tr>
            <tr v-if="!loading && exchangeRates.length === 0">
              <td colspan="6" class="text-center py-4">
                <p class="text-muted mb-2">暂无汇率记录</p>
                <button class="btn btn-primary btn-sm" @click="openAddModal">
                  添加第一条记录
                </button>
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

    <!-- 添加/编辑汇率模态框 -->
    <div class="modal fade" id="rateModal" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ isEdit ? '编辑汇率' : '添加汇率' }}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="submitForm">
              <div class="mb-3">
                <label class="form-label">日期</label>
                <date-input v-model="form.rateDate" :class="{ 'is-invalid': errors.rateDate }" />
                <div class="invalid-feedback">{{ errors.rateDate }}</div>
              </div>
              <div class="mb-3">
                <label class="form-label">货币</label>
                <select class="form-select" v-model="form.currency" :class="{ 'is-invalid': errors.currency }">
                  <option value="">请选择货币</option>
                  <option value="USD">USD</option>
                  <option value="CNY">CNY</option>
                </select>
                <div class="invalid-feedback">{{ errors.currency }}</div>
              </div>
              <div class="mb-3">
                <label class="form-label">汇率</label>
                <input type="number" class="form-control" v-model="form.rate" step="0.0001" min="0"
                       :class="{ 'is-invalid': errors.rate }" />
                <div class="invalid-feedback">{{ errors.rate }}</div>
              </div>
              <div class="mb-3">
                <label class="form-label">数据来源</label>
                <input type="text" class="form-control" v-model="form.source" />
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
            <button type="button" class="btn btn-primary" @click="submitForm" :disabled="submitting">
              {{ submitting ? '保存中...' : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { Modal } from 'bootstrap/dist/js/bootstrap.bundle.min.js'
import DateInput from '../components/DateInput.vue'
import axios from 'axios'

// 状态
const loading = ref(false)
const submitting = ref(false)
const searchVisible = ref(false)
const isEdit = ref(false)
const exchangeRates = ref([])
const currentPage = ref(1)
const totalPages = ref(1)
const pageSize = 15
let modal = null

// 搜索表单
const searchForm = reactive({
  startDate: '',
  endDate: '',
  currency: ''
})

// 编辑表单
const form = reactive({
  id: null,
  rateDate: '',
  currency: '',
  rate: '',
  source: ''
})

// 表单错误
const errors = reactive({
  rateDate: '',
  currency: '',
  rate: ''
})

// 分页计算
const displayedPages = computed(() => {
  const pages = []
  const maxDisplayed = 7
  const sidePages = 2
  
  if (totalPages.value <= maxDisplayed) {
    for (let i = 1; i <= totalPages.value; i++) {
      pages.push(i)
    }
  } else {
    if (currentPage.value <= sidePages + 3) {
      for (let i = 1; i <= sidePages + 3; i++) {
        pages.push(i)
      }
      pages.push('...')
      pages.push(totalPages.value)
    } else if (currentPage.value >= totalPages.value - (sidePages + 2)) {
      pages.push(1)
      pages.push('...')
      for (let i = totalPages.value - (sidePages + 2); i <= totalPages.value; i++) {
        pages.push(i)
      }
    } else {
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

// 获取汇率列表
const fetchRates = async () => {
  if (loading.value) return
  
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (searchForm.startDate) params.append('start_date', searchForm.startDate)
    if (searchForm.endDate) params.append('end_date', searchForm.endDate)
    if (searchForm.currency) params.append('currency', searchForm.currency)
    params.append('page', currentPage.value)
    params.append('per_page', pageSize)
    
    const response = await axios.get(`/stock/exchange_rates?${params.toString()}`)
    if (response.data.success) {
      exchangeRates.value = response.data.data.items
      totalPages.value = Math.ceil(response.data.data.total / pageSize)
    }
  } catch (error) {
    console.error('获取汇率列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 获取缺失汇率
const fetchMissingRates = async () => {
  if (loading.value) return
  
  loading.value = true
  try {
    const response = await axios.post('/stock/exchange_rates/fetch_missing')
    if (response.data.success) {
      // 重新加载数据
      await fetchRates()
    }
  } catch (error) {
    console.error('获取缺失汇率失败:', error)
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
  fetchRates()
}

const resetSearch = () => {
  searchForm.startDate = ''
  searchForm.endDate = ''
  searchForm.currency = ''
  currentPage.value = 1
  fetchRates()
}

// 分页相关
const changePage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
    fetchRates()
  }
}

// 模态框相关
const initModal = () => {
  modal = new Modal(document.getElementById('rateModal'))
}

const openAddModal = () => {
  isEdit.value = false
  resetForm()
  modal.show()
}

const openEditModal = (rate) => {
  isEdit.value = true
  resetForm()
  form.id = rate.id
  form.rateDate = rate.rate_date
  form.currency = rate.currency
  form.rate = rate.rate
  form.source = rate.source || ''
  modal.show()
}

const resetForm = () => {
  form.id = null
  form.rateDate = ''
  form.currency = ''
  form.rate = ''
  form.source = ''
  Object.keys(errors).forEach(key => errors[key] = '')
}

// 表单提交
const submitForm = async () => {
  if (submitting.value) return
  
  // 验证表单
  let isValid = true
  if (!form.rateDate) {
    errors.rateDate = '请选择日期'
    isValid = false
  }
  if (!form.currency) {
    errors.currency = '请选择货币'
    isValid = false
  }
  if (!form.rate) {
    errors.rate = '请输入汇率'
    isValid = false
  }
  
  if (!isValid) return
  
  submitting.value = true
  try {
    const url = isEdit.value 
      ? `/stock/exchange_rates/edit/${form.id}`
      : '/stock/exchange_rates/add'
    
    const response = await axios.post(url, {
      rate_date: form.rateDate,
      currency: form.currency,
      rate: form.rate,
      source: form.source
    })
    
    if (response.data.success) {
      modal.hide()
      await fetchRates()
    }
  } catch (error) {
    console.error('保存汇率失败:', error)
  } finally {
    submitting.value = false
  }
}

// 删除汇率
const confirmDelete = async (rate) => {
  if (!confirm('确定要删除这条汇率记录吗？')) return
  
  try {
    const response = await axios.post(`/stock/exchange_rates/delete/${rate.id}`)
    if (response.data.success) {
      await fetchRates()
    }
  } catch (error) {
    console.error('删除汇率失败:', error)
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

const formatDateTime = (datetime) => {
  return new Date(datetime).toLocaleString('zh-CN', {
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

// 初始化
onMounted(() => {
  initModal()
  fetchRates()
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