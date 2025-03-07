<template>
  <div class="container-fluid py-3">
    <div class="card">
      <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="mb-0" data-testid="stock-manager-title">股票管理</h5>
        <div class="btn-group">
          <button 
            class="btn btn-primary btn-sm" 
            @click="showAddDialog" 
            v-permission="'stock:list:add'"
            data-testid="add-stock-btn"
          >
            <i class="bi bi-plus-lg"></i> 添加股票
          </button>
          <button class="btn btn-outline-secondary btn-sm" @click="toggleSearch" data-testid="toggle-search-btn">
            <i :class="['bi', searchVisible ? 'bi-chevron-up' : 'bi-search']"></i> {{ searchVisible ? '收起' : '搜索' }}
          </button>
        </div>
      </div>

      <!-- 搜索表单 -->
      <div v-show="searchVisible" class="card-body border-bottom" v-permission="'stock:list:view'">
        <form @submit.prevent="search" class="row g-2 align-items-end">
          <div class="col-md-3">
            <select class="form-select form-select-sm" v-model="searchForm.market" @change="search" data-testid="stock-market-select">
              <option value="">市场</option>
              <option value="HK">香港</option>
              <option value="US">美国</option>
            </select>
          </div>
          <div class="col-md-6">
            <input
              type="text"
              class="form-control form-control-sm"
              v-model="searchForm.keyword"
              placeholder="搜索股票代码或名称"
              @keyup.enter="search"
              data-testid="stock-search-input"
            />
          </div>
          <div class="col-md-3">
            <button class="btn btn-primary btn-sm px-4" type="button" @click="search" data-testid="stock-search-btn" v-permission="'stock:list:view'">
              查询
            </button>
          </div>
        </form>
      </div>

      <div class="card-body p-0" v-permission="'stock:list:view'">
        <div class="table-responsive" data-testid="stock-table-container">
          <table class="table table-hover align-middle mb-0">
            <thead>
              <tr>
                <th style="width: 60px">市场</th>
                <th style="width: 80px">代码</th>
                <th style="width: 120px">名称</th>
                <th style="width: 200px">谷歌查询代码</th>
                <th style="width: 100px">当前股价</th>
                <th style="width: 140px">更新时间</th>
                <th style="width: 80px" class="text-end">操作</th>
              </tr>
            </thead>
            <tbody>
              <template v-if="!loading">
                <template v-if="stocks.length">
                  <tr v-for="stock in stocks" :key="stock.id" :data-testid="'stock-row-' + stock.code">
                    <td class="text-center">
                      <span class="badge" :class="stock.market === 'HK' ? 'bg-danger' : 'bg-primary'">
                        {{ stock.market }}
                      </span>
                    </td>
                    <td class="font-monospace">{{ stock.code }}</td>
                    <td>{{ stock.code_name }}</td>
                    <td>{{ stock.google_name || '-' }}</td>
                    <td>{{ formatPrice(stock.current_price, stock.market) }}</td>
                    <td>{{ formatDateTime(stock.price_updated_at) }}</td>
                    <td>
                      <div class="d-flex justify-content-end gap-1">
                        <button class="btn btn-link btn-xs p-0 text-primary" title="编辑" @click="editStock(stock)" :data-testid="'edit-stock-btn-' + stock.code" v-permission="'stock:list:edit'">
                          编辑
                        </button>
                        <button class="btn btn-link btn-xs p-0 text-danger ms-2" title="删除" @click="confirmDelete(stock)" :data-testid="'delete-stock-btn-' + stock.code" v-permission="'stock:list:delete'">
                          删除
                        </button>
                      </div>
                    </td>
                  </tr>
                </template>
                <tr v-else>
                  <td colspan="7" class="text-center py-3">
                    <div class="text-muted">暂无数据</div>
                  </td>
                </tr>
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

        <!-- 分页 -->
        <div v-if="totalPages > 1" class="card-footer d-flex justify-content-between align-items-center py-2" v-permission="'stock:list:view'">
          <div class="small text-muted">
            共 {{ totalItems }} 条记录
          </div>
          <nav>
            <ul class="pagination pagination-sm mb-0">
              <li class="page-item" :class="{ disabled: currentPage === 1 }">
                <a class="page-link" href="#" @click.prevent="changePage(currentPage - 1)" title="上一页" data-testid="prev-page-btn">
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
                  <a class="page-link" href="#" @click.prevent="changePage(page)" :data-testid="'page-btn-' + page">{{ page }}</a>
                </template>
              </li>
              <li class="page-item" :class="{ disabled: currentPage === totalPages }">
                <a class="page-link" href="#" @click.prevent="changePage(currentPage + 1)" title="下一页" data-testid="next-page-btn">
                  <i class="fas fa-chevron-right"></i>
                </a>
              </li>
            </ul>
          </nav>
        </div>
      </div>

      <!-- 添加/编辑股票对话框 -->
      <stock-add-dialog
        v-model="showDialog"
        :edit-data="editData"
        @submit="handleDialogSubmit"
        @close="handleDialogClose"
      />

      <!-- 删除确认对话框 -->
      <div class="modal fade" id="deleteConfirmModal" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">确认删除</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
              <p>确定要删除股票 <strong>{{ selectedStock?.name }} ({{ selectedStock?.code }})</strong> 吗？</p>
              <div class="alert alert-warning">
                <i class="bi bi-exclamation-triangle-fill me-2"></i>
                此操作将删除该股票的所有相关交易记录，且不可恢复！
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
              <button type="button" class="btn btn-danger" @click="deleteStock">确认删除</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import StockAddDialog from '../components/StockAddDialog.vue'

const loading = ref(false)
const showDialog = ref(false)
const editData = ref(null)
const stocks = ref([])
const currentPage = ref(1)
const totalPages = ref(1)
const totalItems = ref(0)
const pageSize = 15
const searchVisible = ref(false)

// 搜索表单
const searchForm = ref({
  market: '',
  keyword: ''
})

// 显示添加对话框
const showAddDialog = () => {
  editData.value = null
  showDialog.value = true
}

// 编辑股票
const editStock = (stock) => {
  editData.value = stock
  showDialog.value = true
}

// 处理添加/编辑成功
const handleSuccess = () => {
  fetchStocks()
}

// 搜索
const search = () => {
  currentPage.value = 1
  fetchStocks()
}

// 获取股票列表
const fetchStocks = async () => {
  if (loading.value) return
  
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (searchForm.value.market) params.append('market', searchForm.value.market)
    if (searchForm.value.keyword) params.append('keyword', searchForm.value.keyword)
    params.append('page', currentPage.value)
    params.append('per_page', pageSize)
    
    const response = await axios.get('/api/stock/stocks', { params })
    
    if (response.data.success) {
      stocks.value = response.data.data.items
      totalPages.value = Math.ceil(response.data.data.total / pageSize)
      totalItems.value = response.data.data.total
      currentPage.value = response.data.data.page
    }
  } catch (error) {
    console.error('获取股票列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 重置搜索
const resetSearch = () => {
  searchForm.value = {
    market: '',
    keyword: ''
  }
  currentPage.value = 1
  fetchStocks()
}

// 删除股票
const confirmDelete = async (stock) => {
  if (!confirm(`确定要删除股票 ${stock.code} - ${stock.code_name} 吗？`)) return
  
  try {
    loading.value = true  // 添加加载状态
    const response = await axios.delete(`/api/stock/stocks/${stock.id}`)
    if (response.data.success) {
      // 显示成功消息
      alert('删除成功')
      // 如果当前页只有一条数据，且不是第一页，则跳转到上一页
      if (stocks.value.length === 1 && currentPage.value > 1) {
        currentPage.value--
      }
      await fetchStocks()  // 使用 await 确保获取最新数据
    } else {
      throw new Error(response.data.message || '删除失败')
    }
  } catch (error) {
    console.error('删除股票失败:', error)
    alert(error.response?.data?.message || error.message || '删除失败，请重试')
  } finally {
    loading.value = false  // 清除加载状态
  }
}

// 切换页码
const changePage = (page) => {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  fetchStocks()
}

// 计算显示的页码
const displayedPages = computed(() => {
  const pages = []
  const maxPages = 5
  
  if (totalPages.value <= maxPages) {
    for (let i = 1; i <= totalPages.value; i++) {
      pages.push(i)
    }
  } else {
    pages.push(1)
    
    let start = currentPage.value - 1
    let end = currentPage.value + 1
    
    if (start <= 2) {
      start = 2
      end = start + 2
    } else if (end >= totalPages.value - 1) {
      end = totalPages.value - 1
      start = end - 2
    }
    
    if (start > 2) pages.push('...')
    for (let i = start; i <= end; i++) {
      pages.push(i)
    }
    if (end < totalPages.value - 1) pages.push('...')
    
    pages.push(totalPages.value)
  }
  
  return pages
})

// 添加格式化函数
const formatPrice = (price, market) => {
  if (!price) return '-'
  const currency = market === 'HK' ? 'HKD' : 'USD'
  return `${price} ${currency}`
}

const formatDateTime = (datetime) => {
  if (!datetime) return '-'
  return new Date(datetime).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  }).replace(/\//g, '-')
}

// 初始化
onMounted(() => {
  fetchStocks()
})

// 添加股票管理相关的权限控制
const toggleSearch = () => {
  searchVisible.value = !searchVisible.value
}

const handleDialogSubmit = () => {
  // 处理添加/编辑成功后的逻辑
  fetchStocks()
}

const handleDialogClose = () => {
  // 处理关闭对话框后的逻辑
  fetchStocks()
}

const deleteStock = () => {
  // 处理删除股票后的逻辑
  fetchStocks()
}
</script>

<style scoped>
.card {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border: 1px solid #dee2e6;
  background-color: #fff;
  margin: 1.5rem 2.5rem;
  border-radius: 0.5rem;
  max-width: 1600px;
}

.container-fluid {
  padding: 0;
  display: flex;
  justify-content: center;
}

.card-header {
  background-color: #fff;
  border-bottom: 1px solid #dee2e6;
  padding: 1.25rem 1.5rem;
  border-top-left-radius: 0.5rem;
  border-top-right-radius: 0.5rem;
}

.card-body {
  padding: 1rem 1.25rem !important;
}

.table-responsive {
  margin: 0;
  border: 1·px solid #dee2e6;
  border-radius: 0.375rem;
  background-color: #fff;
}

.table {
  margin-bottom: 0;
  font-size: 0.875rem;
  background-color: #fff;
}

.table th:first-child {
  border-top-left-radius: 0.375rem;
}

.table th:last-child {
  border-top-right-radius: 0.375rem;
}

.table tr:last-child td:first-child {
  border-bottom-left-radius: 0.375rem;
}

.table tr:last-child td:last-child {
  border-bottom-right-radius: 0.375rem;
}

.table th {
  padding: 0.75rem 1rem;
  font-weight: 500;
  border-bottom: 1px solid #dee2e6;
  background-color: #f8f9fa;
  white-space: nowrap;
  color: #495057;
}

.table td {
  padding: 0.75rem 1rem;
  vertical-align: middle;
  border-bottom: 1px solid #dee2e6;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-footer {
  background-color: #fff;
  border-top: 1px solid #dee2e6;
  padding: 0.75rem 1.5rem;
  border-bottom-left-radius: 0.5rem;
  border-bottom-right-radius: 0.5rem;
}

.btn-link {
  text-decoration: none;
}

.btn-link:hover {
  text-decoration: underline;
}

.form-select,
.form-control {
  border-color: #dee2e6;
  padding: 0.375rem 0.75rem;
}

.form-select:focus,
.form-control:focus {
  border-color: #80bdff;
  box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25);
}

.btn-primary {
  padding: 0.375rem 1rem;
}

.text-primary {
  color: #0d6efd !important;
}

.text-danger {
  color: #dc3545 !important;
}

.pagination {
  margin-bottom: 0;
}

.page-link {
  padding: 0.25rem 0.4rem;
  font-size: 0.75rem;
}

.badge {
  font-weight: normal;
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  min-width: 45px;
}

.bg-danger {
  background-color: #e6071d !important;
}

.bg-primary {
  background-color: #0d6efd !important;
}

.font-monospace {
  font-family: SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 0.875rem;
}

.btn-xs {
  padding: 0.1rem 0.3rem;
  font-size: 0.75rem;
  line-height: 1.2;
}

.table-responsive {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}
</style> 