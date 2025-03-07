<template>
  <div class="container-fluid py-3">
    <div class="card">
      <div class="card-header d-flex justify-content-between align-items-center">
        <h4 class="mb-0" data-testid="holder-title">持有人管理</h4>
        <button 
          class="btn btn-primary" 
          @click="openAddModal" 
          data-testid="add-holder-btn"
        >
          <i class="bi bi-plus-circle"></i> 添加持有人
        </button>
      </div>

      <!-- 搜索区域 -->
      <div class="card-body border-bottom">
        <form @submit.prevent="loadHolders" class="row g-3 align-items-end" data-testid="search-form">
          <div class="col-md-3">
            <label class="form-label" data-testid="holder-name-label">持有人姓名</label>
            <input
              type="text"
              class="form-control"
              v-model="searchForm.name"
              placeholder="输入持有人姓名"
              data-testid="holder-name-input"
            />
          </div>
          <div class="col-md-3">
            <label class="form-label" data-testid="holder-type-label">类型</label>
            <select class="form-select" v-model="searchForm.type" data-testid="holder-type-select">
              <option value="">全部</option>
              <option value="individual">个人</option>
              <option value="institution">机构</option>
            </select>
          </div>
          <div class="col-md-3">
            <label class="form-label" data-testid="holder-status-label">状态</label>
            <select class="form-select" v-model="searchForm.status" data-testid="holder-status-select">
              <option value="">全部</option>
              <option value="1">启用</option>
              <option value="0">禁用</option>
            </select>
          </div>
          <div class="col-md-3">
            <button class="btn btn-primary me-2" type="submit" data-testid="search-btn">
              <i class="bi bi-search"></i> 查询
            </button>
            <button class="btn btn-secondary" type="button" @click="resetSearch" data-testid="reset-btn">
              <i class="bi bi-arrow-counterclockwise"></i> 重置
            </button>
          </div>
        </form>
      </div>

      <!-- 数据表格 -->
      <div class="card-body">
        <div class="table-responsive" data-testid="holder-table-container">
          <table class="table table-bordered table-hover">
            <thead>
              <tr>
                <th style="width: 60px;">ID</th>
                <th>持有人姓名</th>
                <th>类型</th>
                <th>关联用户</th>
                <th>状态</th>
                <th>创建时间</th>
                <th>更新时间</th>
                <th style="width: 150px;">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="holder in holders" :key="holder.id" :data-testid="'holder-row-' + holder.id">
                <td>{{ holder.id }}</td>
                <td>{{ holder.name }}</td>
                <td>{{ holder.type === 'individual' ? '个人' : '机构' }}</td>
                <td>{{ holder.username || '未关联' }}</td>
                <td>
                  <span
                    :class="holder.status === 1 ? 'badge bg-success' : 'badge bg-danger'"
                    :data-testid="'holder-status-badge-' + holder.id"
                  >
                    {{ holder.status === 1 ? '启用' : '禁用' }}
                  </span>
                </td>
                <td>{{ holder.created_at }}</td>
                <td>{{ holder.updated_at }}</td>
                <td>
                  <button 
                    class="btn btn-sm btn-info me-1" 
                    @click="openEditModal(holder)" 
                    :data-testid="'edit-holder-btn-' + holder.id"
                  >
                    编辑
                  </button>
                  <button
                    class="btn btn-sm btn-danger"
                    @click="confirmDelete(holder)"
                    :disabled="loading"
                    :data-testid="'delete-holder-btn-' + holder.id"
                  >
                    删除
                  </button>
                </td>
              </tr>
              <tr v-if="holders.length === 0">
                <td colspan="8" class="text-center py-3" data-testid="no-data-message">暂无数据</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 加载中显示 -->
      <div v-if="loading" class="card-body text-center py-5 position-absolute top-0 start-0 w-100 h-100 bg-white bg-opacity-75" data-testid="loading-indicator">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">加载中...</span>
        </div>
        <p class="mt-2">加载数据中，请稍候...</p>
      </div>
    </div>

    <!-- 添加/编辑持有人模态框 -->
    <div class="modal fade" id="holderModal" tabindex="-1" aria-hidden="true" data-testid="holder-modal">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" data-testid="modal-title">{{ isEdit ? '编辑持有人' : '添加持有人' }}</h5>
            <button
              type="button"
              class="btn-close"
              @click="closeHolderModal"
              aria-label="Close"
              data-testid="close-modal-btn"
            ></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="saveHolder" data-testid="holder-form">
              <div class="mb-3">
                <label class="form-label" data-testid="holder-name-form-label">持有人姓名 <span class="text-danger">*</span></label>
                <input
                  type="text"
                  class="form-control"
                  v-model="holderForm.name"
                  required
                  placeholder="请输入持有人姓名"
                  data-testid="holder-name-form-input"
                  id="holder-name"
                />
              </div>
              <div class="mb-3">
                <label class="form-label" data-testid="holder-type-form-label">类型 <span class="text-danger">*</span></label>
                <select class="form-select" v-model="holderForm.type" required data-testid="holder-type-form-select" id="holder-type">
                  <option value="individual">个人</option>
                  <option value="institution">机构</option>
                </select>
              </div>
              <div class="mb-3">
                <label class="form-label" data-testid="holder-user-form-label">关联用户</label>
                <select class="form-select" v-model="holderForm.user_id" data-testid="holder-user-form-select" id="holder-user">
                  <option value="">不关联用户</option>
                  <option v-for="user in availableUsers" :key="user.id" :value="user.id">
                    {{ user.username }}
                  </option>
                </select>
              </div>
              <div class="mb-3">
                <label class="form-label" data-testid="holder-status-form-label">状态</label>
                <select class="form-select" v-model="holderForm.status" data-testid="holder-status-form-select" id="holder-status">
                  <option :value="1">启用</option>
                  <option :value="0">禁用</option>
                </select>
              </div>
              <div class="text-end">
                <button
                  type="button"
                  class="btn btn-secondary me-2"
                  @click="closeHolderModal"
                  data-testid="cancel-form-btn"
                >
                  取消
                </button>
                <button type="submit" class="btn btn-primary" :disabled="saving" data-testid="save-holder-btn">
                  {{ saving ? '保存中...' : '保存' }}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>

    <!-- 删除确认模态框 -->
    <div class="modal fade" id="deleteModal" tabindex="-1" aria-hidden="true" data-testid="delete-modal">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" data-testid="delete-modal-title">确认删除</h5>
            <button
              type="button"
              class="btn-close"
              @click="closeDeleteModal"
              aria-label="Close"
              data-testid="close-delete-modal-btn"
            ></button>
          </div>
          <div class="modal-body">
            <p data-testid="delete-confirmation-message">确定要删除持有人 <strong>{{ currentHolder?.name }}</strong> 吗？</p>
            <p class="text-danger" data-testid="delete-warning">注意：如果该持有人已被交易记录引用，将只会被禁用而非删除。</p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeDeleteModal" data-testid="cancel-delete-btn">取消</button>
            <button
              type="button"
              class="btn btn-danger"
              @click="deleteHolder"
              :disabled="deleting"
              data-testid="confirm-delete-btn"
            >
              {{ deleting ? '删除中...' : '确认删除' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useToast } from 'vue-toastification'
import axios from 'axios'
import { Modal } from 'bootstrap'

const toast = useToast()

// 数据状态
const holders = ref([])
const availableUsers = ref([])
const loading = ref(false)
const saving = ref(false)
const deleting = ref(false)
const isEdit = ref(false)
const currentHolder = ref(null)
let holderModal = null
let deleteModal = null

// 搜索表单
const searchForm = ref({
  name: '',
  type: '',
  status: ''
})

// 持有人表单
const holderForm = ref({
  name: '',
  type: 'individual',
  user_id: '',
  status: 1
})

// 初始化模态框
const initModals = () => {
  console.log('开始初始化模态框...')
  
  try {
    const holderModalEl = document.getElementById('holderModal')
    const deleteModalEl = document.getElementById('deleteModal')
    
    if (holderModalEl) {
      // 先销毁可能存在的实例
      const existingModal = bootstrap.Modal.getInstance(holderModalEl)
      if (existingModal) {
        existingModal.dispose()
        console.log('销毁已存在的持有人模态框实例')
      }
      
      // 创建新实例
      holderModal = new bootstrap.Modal(holderModalEl, {
        backdrop: 'static',
        keyboard: false
      })
      console.log('持有人模态框初始化成功')
    } else {
      console.error('未找到持有人模态框元素')
    }
    
    if (deleteModalEl) {
      // 先销毁可能存在的实例
      const existingModal = bootstrap.Modal.getInstance(deleteModalEl)
      if (existingModal) {
        existingModal.dispose()
        console.log('销毁已存在的删除确认模态框实例')
      }
      
      // 创建新实例
      deleteModal = new bootstrap.Modal(deleteModalEl, {
        backdrop: 'static',
        keyboard: false
      })
      console.log('删除确认模态框初始化成功')
    } else {
      console.error('未找到删除确认模态框元素')
    }
    
    console.log('模态框初始化完成')
  } catch (error) {
    console.error('初始化模态框时出错:', error)
  }
}

// 清理模态框背景和样式
const cleanupModalEffects = () => {
  // 移除模态框背景遮罩
  const modalBackdrops = document.querySelectorAll('.modal-backdrop')
  modalBackdrops.forEach(backdrop => {
    backdrop.classList.remove('show')
    setTimeout(() => {
      backdrop.remove()
    }, 150)
  })
  
  // 移除body上的modal-open类
  document.body.classList.remove('modal-open')
  document.body.style.overflow = ''
  document.body.style.paddingRight = ''
}

// 加载持有人列表
const loadHolders = async () => {
  console.log('开始加载持有人列表...')
  loading.value = true
  try {
    console.log('发送GET请求到 /api/holders')
    const response = await axios.get('/api/holders')
    console.log('获取持有人列表响应:', response.data)
    
    if (response.data.success) {
      holders.value = response.data.data
      console.log(`成功加载 ${holders.value.length} 个持有人`)
      
      // 打印每个持有人的用户信息
      holders.value.forEach(holder => {
        console.log(`持有人ID: ${holder.id}, 姓名: ${holder.name}, 用户名: ${holder.username}, 显示名称: ${holder.user_display_name}`)
      })
    } else {
      console.error('加载持有人列表失败:', response.data.message)
      toast.error('加载持有人列表失败: ' + response.data.message)
    }
  } catch (error) {
    console.error('加载持有人列表失败:', error)
    toast.error('加载持有人列表失败，请稍后重试')
  } finally {
    loading.value = false
    console.log('持有人列表加载完成')
  }
}

// 加载可用用户列表
const loadAvailableUsers = async () => {
  try {
    console.log('开始加载可用用户列表...')
    const response = await axios.get('/api/system/user/available')
    console.log('获取可用用户列表响应:', response.data)
    
    if (response.data.success) {
      availableUsers.value = response.data.data
      console.log(`成功加载 ${availableUsers.value.length} 个可用用户`)
      
      // 打印每个用户的信息
      availableUsers.value.forEach(user => {
        console.log(`用户ID: ${user.id}, 用户名: ${user.username}, 显示名称: ${user.display_name}`)
      })
    } else {
      console.error('加载可用用户列表失败:', response.data.message)
    }
  } catch (error) {
    console.error('加载可用用户列表失败:', error)
    toast.error('加载可用用户列表失败，请稍后重试')
  }
}

// 重置搜索条件
const resetSearch = () => {
  searchForm.value = {
    name: '',
    type: '',
    status: ''
  }
  loadHolders()
}

// 打开添加模态框
const openAddModal = () => {
  console.log('打开添加持有人模态框')
  isEdit.value = false
  holderForm.value = {
    name: '',
    type: 'individual',
    user_id: '',
    status: 1
  }
  
  // 使用Bootstrap实例方法打开模态框
  if (holderModal) {
    holderModal.show()
    console.log('模态框已显示')
  } else {
    console.error('模态框实例不存在')
    // 尝试重新初始化
    initModals()
    setTimeout(() => {
      if (holderModal) {
        holderModal.show()
        console.log('重新初始化后模态框已显示')
      } else {
        console.error('重新初始化后模态框实例仍不存在')
        toast.error('打开模态框失败，请刷新页面重试')
      }
    }, 100)
  }
}

// 打开编辑模态框
const openEditModal = (holder) => {
  console.log('准备编辑持有人', holder)
  isEdit.value = true
  holderForm.value = {
    id: holder.id,
    name: holder.name,
    type: holder.type,
    user_id: holder.user_id || '',
    status: holder.status
  }
  
  // 如果是编辑模式且已有关联用户，需要将当前关联的用户添加到可选列表中
  if (holder.user_id && holder.username) {
    // 检查当前用户是否已在列表中
    const userExists = availableUsers.value.some(u => u.id === holder.user_id);
    if (!userExists) {
      availableUsers.value.push({
        id: holder.user_id,
        username: holder.username,
        display_name: holder.user_display_name
      });
    }
  }
  
  // 使用Bootstrap实例方法打开模态框
  if (holderModal) {
    holderModal.show()
    console.log('编辑模态框已显示')
  } else {
    console.error('编辑模态框实例不存在')
    // 尝试重新初始化
    initModals()
    setTimeout(() => {
      if (holderModal) {
        holderModal.show()
        console.log('重新初始化后编辑模态框已显示')
      } else {
        console.error('重新初始化后编辑模态框实例仍不存在')
        toast.error('打开编辑模态框失败，请刷新页面重试')
      }
    }, 100)
  }
}

// 保存持有人
const saveHolder = async () => {
  if (!holderForm.value.name) {
    toast.warning('请输入持有人姓名')
    return
  }

  saving.value = true
  try {
    console.log('准备保存持有人数据:', JSON.stringify(holderForm.value))
    let response
    if (isEdit.value) {
      console.log(`发送PUT请求到 /api/holders/${holderForm.value.id}`)
      response = await axios.put(`/api/holders/${holderForm.value.id}`, holderForm.value)
    } else {
      console.log('发送POST请求到 /api/holders')
      response = await axios.post('/api/holders', holderForm.value)
    }

    console.log('服务器响应:', response.data)
    if (response.data.success) {
      toast.success(response.data.message || (isEdit.value ? '更新持有人成功' : '添加持有人成功'))
      
      // 关闭模态框
      closeHolderModal()
      
      loadHolders()
    } else {
      toast.error(response.data.message || '操作失败')
    }
  } catch (error) {
    console.error('保存持有人失败:', error)
    console.error('错误详情:', error.response?.data || '无详细信息')
    toast.error(error.response?.data?.message || '保存失败，请稍后重试')
  } finally {
    saving.value = false
  }
}

// 确认删除
const confirmDelete = (holder) => {
  console.log('准备删除持有人', holder)
  currentHolder.value = holder
  
  // 使用Bootstrap实例方法打开模态框
  if (deleteModal) {
    deleteModal.show()
    console.log('删除确认模态框已显示')
  } else {
    console.error('删除确认模态框实例不存在')
    // 尝试重新初始化
    initModals()
    setTimeout(() => {
      if (deleteModal) {
        deleteModal.show()
        console.log('重新初始化后删除确认模态框已显示')
      } else {
        console.error('重新初始化后删除确认模态框实例仍不存在')
        toast.error('打开删除确认模态框失败，请刷新页面重试')
      }
    }, 100)
  }
}

// 删除持有人
const deleteHolder = async () => {
  if (!currentHolder.value) return

  deleting.value = true
  try {
    console.log(`准备删除持有人ID: ${currentHolder.value.id}`)
    const response = await axios.delete(`/api/holders/${currentHolder.value.id}`)
    console.log('服务器响应:', response.data)
    if (response.data.success) {
      toast.success(response.data.message || '删除持有人成功')
      
      // 关闭模态框
      closeDeleteModal()
      
      loadHolders()
    } else {
      toast.error(response.data.message || '删除失败')
    }
  } catch (error) {
    console.error('删除持有人失败:', error)
    console.error('错误详情:', error.response?.data || '无详细信息')
    toast.error(error.response?.data?.message || '删除失败，请稍后重试')
  } finally {
    deleting.value = false
  }
}

// 重新初始化模态框
const reinitModals = () => {
  console.log('重新初始化模态框')
  initModals()
}

// 初始化
onMounted(() => {
  loadHolders()
  loadAvailableUsers()
  
  // 延迟初始化模态框，确保DOM已完全加载
  setTimeout(() => {
    initModals()
    console.log('模态框初始化完成')
  }, 500)
  
  // 添加全局事件监听器
  window.addEventListener('load', reinitModals)
  document.addEventListener('DOMContentLoaded', reinitModals)
  
  // 添加模态框隐藏事件监听器
  const holderModalEl = document.getElementById('holderModal')
  if (holderModalEl) {
    holderModalEl.addEventListener('hidden.bs.modal', () => {
      console.log('持有人模态框隐藏事件触发')
      cleanupModalEffects()
    })
  }
  
  const deleteModalEl = document.getElementById('deleteModal')
  if (deleteModalEl) {
    deleteModalEl.addEventListener('hidden.bs.modal', () => {
      console.log('删除确认模态框隐藏事件触发')
      cleanupModalEffects()
    })
  }
})

// 组件卸载时移除事件监听器
onUnmounted(() => {
  window.removeEventListener('load', reinitModals)
  document.removeEventListener('DOMContentLoaded', reinitModals)
  
  // 移除模态框隐藏事件监听器
  const holderModalEl = document.getElementById('holderModal')
  if (holderModalEl) {
    holderModalEl.removeEventListener('hidden.bs.modal', cleanupModalEffects)
  }
  
  const deleteModalEl = document.getElementById('deleteModal')
  if (deleteModalEl) {
    deleteModalEl.removeEventListener('hidden.bs.modal', cleanupModalEffects)
  }
})

// 关闭持有人模态框
const closeHolderModal = () => {
  console.log('关闭持有人模态框')
  if (holderModal) {
    holderModal.hide()
    console.log('持有人模态框已隐藏')
    cleanupModalEffects()
  } else {
    console.error('持有人模态框实例不存在')
  }
}

// 关闭删除确认模态框
const closeDeleteModal = () => {
  console.log('关闭删除确认模态框')
  if (deleteModal) {
    deleteModal.hide()
    console.log('删除确认模态框已隐藏')
    cleanupModalEffects()
  } else {
    console.error('删除确认模态框实例不存在')
  }
}
</script>

<style scoped>
.card {
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
  border-radius: 0.5rem;
}

.table th {
  background-color: #f8f9fa;
}

.badge {
  font-weight: normal;
  padding: 0.35em 0.65em;
}
</style> 