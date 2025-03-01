<template>
  <div class="container mt-3">
    <div class="card">
      <div class="card-header d-flex justify-content-between align-items-center">
        <h5 data-testid="user-management-title">用户管理</h5>
        <div class="d-flex">
          <div class="input-group me-2">
            <input 
              type="text" 
              class="form-control" 
              placeholder="搜索用户名/姓名" 
              v-model="searchName"
              @keyup.enter="loadUsers"
              data-testid="user-search-input"
            >
            <button class="btn btn-outline-secondary" type="button" @click="loadUsers" v-permission="'system:user:view'" data-testid="user-search-btn">
              <i class="bi bi-search"></i>
            </button>
          </div>
          <button 
            class="btn btn-primary" 
            @click="showAddUserModal" 
            v-permission="'system:user:add'"
            data-testid="add-user-btn"
          >
            <i class="bi bi-plus-lg"></i> 添加用户
          </button>
        </div>
      </div>
      <div class="card-body" v-permission="'system:user:view'" data-testid="user-table-container">
        <div class="table-responsive">
          <table class="table table-striped table-hover">
            <thead>
              <tr>
                <th>ID</th>
                <th>用户名</th>
                <th>姓名</th>
                <th>邮箱</th>
                <th>角色</th>
                <th>状态</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in users" :key="user.id" :data-testid="'user-row-' + user.id">
                <td>{{ user.id }}</td>
                <td>{{ user.username }}</td>
                <td>{{ user.name }}</td>
                <td>{{ user.email }}</td>
                <td>
                  <span 
                    v-for="role in user.roles" 
                    :key="role.id" 
                    class="badge bg-primary me-1"
                    :data-testid="'user-role-badge-' + user.id + '-' + role.id"
                  >
                    {{ role.name }}
                  </span>
                </td>
                <td>
                  <span 
                    :class="user.status === 1 ? 'badge bg-success' : 'badge bg-danger'"
                    :data-testid="'user-status-badge-' + user.id"
                  >
                    {{ user.status === 1 ? '启用' : '禁用' }}
                  </span>
                </td>
                <td>{{ formatDate(user.created_at) }}</td>
                <td>
                  <div class="btn-group">
                    <button 
                      class="btn btn-sm btn-outline-primary" 
                      @click="showEditUserModal(user)"
                      v-permission="'system:user:edit'"
                      :data-testid="'edit-user-btn-' + user.id"
                    >
                      <i class="bi bi-pencil"></i>
                    </button>
                    <button 
                      class="btn btn-sm btn-outline-danger" 
                      @click="confirmDeleteUser(user)"
                      v-permission="'system:user:delete'"
                      :data-testid="'delete-user-btn-' + user.id"
                    >
                      <i class="bi bi-trash"></i>
                    </button>
                    <button 
                      class="btn btn-sm btn-outline-success" 
                      @click="showAssignRolesModal(user)"
                      v-permission="'system:user:assign'"
                      :data-testid="'assign-roles-btn-' + user.id"
                    >
                      <i class="bi bi-people"></i>
                    </button>
                    <button 
                      class="btn btn-sm btn-outline-warning" 
                      @click="toggleUserStatus(user)"
                      v-permission="'system:user:edit'"
                      :data-testid="'toggle-status-btn-' + user.id"
                    >
                      <i :class="user.status === 1 ? 'bi bi-x-circle' : 'bi bi-check-circle'"></i>
                    </button>
                  </div>
                </td>
              </tr>
              <tr v-if="users.length === 0">
                <td colspan="8" class="text-center" data-testid="no-users-message">暂无数据</td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <!-- 分页 -->
        <nav v-if="totalPages > 1" data-testid="pagination-container">
          <ul class="pagination justify-content-center">
            <li class="page-item" :class="{ disabled: currentPage === 1 }">
              <a class="page-link" href="#" @click.prevent="changePage(currentPage - 1)" data-testid="prev-page-btn">上一页</a>
            </li>
            <li 
              v-for="page in displayedPages" 
              :key="page" 
              class="page-item"
              :class="{ active: currentPage === page }"
            >
              <a class="page-link" href="#" @click.prevent="changePage(page)" :data-testid="'page-btn-' + page">{{ page }}</a>
            </li>
            <li class="page-item" :class="{ disabled: currentPage === totalPages }">
              <a class="page-link" href="#" @click.prevent="changePage(currentPage + 1)" data-testid="next-page-btn">下一页</a>
            </li>
          </ul>
        </nav>
      </div>
    </div>

    <!-- 添加/编辑用户模态框 -->
    <div class="modal fade" id="userModal" tabindex="-1" ref="userModal">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ isEditing ? '编辑用户' : '添加用户' }}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="submitUserForm">
              <div class="mb-3">
                <label for="username" class="form-label">用户名</label>
                <input 
                  type="text" 
                  class="form-control" 
                  id="username" 
                  v-model="userForm.username"
                  :disabled="isEditing"
                  required
                >
              </div>
              <div class="mb-3">
                <label for="name" class="form-label">姓名</label>
                <input 
                  type="text" 
                  class="form-control" 
                  id="name" 
                  v-model="userForm.name"
                  required
                >
              </div>
              <div class="mb-3">
                <label for="email" class="form-label">邮箱</label>
                <input 
                  type="email" 
                  class="form-control" 
                  id="email" 
                  v-model="userForm.email"
                >
              </div>
              <div class="mb-3" v-if="isEditing">
                <div class="form-check">
                  <input 
                    type="checkbox" 
                    class="form-check-input" 
                    id="changePassword" 
                    v-model="userForm.changePassword"
                  >
                  <label class="form-check-label" for="changePassword">修改密码</label>
                </div>
              </div>
              <div class="mb-3" v-if="!isEditing || userForm.changePassword">
                <label for="password" class="form-label">{{ isEditing ? '新密码' : '密码' }}</label>
                <input 
                  type="password" 
                  class="form-control" 
                  id="password" 
                  v-model="userForm.password"
                  :required="!isEditing"
                >
              </div>
              <div class="mb-3">
                <label class="form-label">状态</label>
                <div class="form-check">
                  <input 
                    type="radio" 
                    class="form-check-input" 
                    id="statusActive" 
                    value="1" 
                    v-model="userForm.status"
                  >
                  <label class="form-check-label" for="statusActive">启用</label>
                </div>
                <div class="form-check">
                  <input 
                    type="radio" 
                    class="form-check-input" 
                    id="statusInactive" 
                    value="0" 
                    v-model="userForm.status"
                  >
                  <label class="form-check-label" for="statusInactive">禁用</label>
                </div>
              </div>
              <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                <button type="submit" class="btn btn-primary">保存</button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>

    <!-- 分配角色模态框 -->
    <div class="modal fade" id="assignRolesModal" tabindex="-1" ref="assignRolesModal">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">分配角色</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">用户: {{ selectedUser?.username }}</label>
            </div>
            <div class="mb-3">
              <label class="form-label">角色列表</label>
              <div class="form-check" v-for="role in allRoles" :key="role.id">
                <input 
                  class="form-check-input" 
                  type="checkbox" 
                  :id="'role-' + role.id" 
                  :value="role.id" 
                  v-model="selectedRoles"
                >
                <label class="form-check-label" :for="'role-' + role.id">
                  {{ role.name }} - {{ role.description }}
                </label>
              </div>
            </div>
            <div class="text-end">
              <button type="button" class="btn btn-secondary me-2" data-bs-dismiss="modal">取消</button>
              <button type="button" class="btn btn-primary" @click="assignRoles">保存</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 删除确认模态框 -->
    <div class="modal fade" id="deleteConfirmModal" tabindex="-1" ref="deleteConfirmModal">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">确认删除</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <p>确定要删除用户 "{{ selectedUser?.username }}" 吗？此操作不可撤销。</p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
            <button type="button" class="btn btn-danger" @click="deleteUser">删除</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { Modal } from 'bootstrap'
import { useMessage } from '@/composables/useMessage'

// 消息提示
const message = useMessage()

// 用户列表数据
const users = ref([])
const searchName = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

// 分页显示逻辑
const displayedPages = computed(() => {
  const pages = []
  const maxVisiblePages = 5
  
  if (totalPages.value <= maxVisiblePages) {
    for (let i = 1; i <= totalPages.value; i++) {
      pages.push(i)
    }
  } else {
    let startPage = Math.max(1, currentPage.value - Math.floor(maxVisiblePages / 2))
    let endPage = startPage + maxVisiblePages - 1
    
    if (endPage > totalPages.value) {
      endPage = totalPages.value
      startPage = Math.max(1, endPage - maxVisiblePages + 1)
    }
    
    for (let i = startPage; i <= endPage; i++) {
      pages.push(i)
    }
  }
  
  return pages
})

// 模态框引用
const userModal = ref(null)
const assignRolesModal = ref(null)
const deleteConfirmModal = ref(null)

// 表单数据
const userForm = ref({
  username: '',
  password: '',
  name: '',
  email: '',
  status: '1',
  changePassword: false
})

// 编辑状态
const isEditing = ref(false)
const selectedUser = ref(null)

// 角色相关
const allRoles = ref([])
const selectedRoles = ref([])

// 加载用户列表
const loadUsers = async () => {
  try {
    const params = {
      page: currentPage.value,
      size: pageSize.value
    }
    
    if (searchName.value) {
      params.name = searchName.value
    }
    
    const response = await axios.get('/api/system/user/list', { params })
    users.value = response.data.data.items
    total.value = response.data.data.total
  } catch (err) {
    message.error('加载用户列表失败: ' + (err.response?.data?.message || err.message))
  }
}

// 加载所有角色
const loadAllRoles = async () => {
  try {
    const response = await axios.get('/api/system/role/all')
    allRoles.value = response.data.data
  } catch (err) {
    message.error('加载角色列表失败: ' + (err.response?.data?.message || err.message))
  }
}

// 显示添加用户模态框
const showAddUserModal = () => {
  isEditing.value = false
  userForm.value = {
    username: '',
    password: '',
    name: '',
    email: '',
    status: '1'
  }
  new Modal(userModal.value).show()
}

// 显示编辑用户模态框
const showEditUserModal = (user) => {
  isEditing.value = true
  selectedUser.value = user
  userForm.value = {
    id: user.id,
    username: user.username,
    name: user.display_name || '',
    email: user.email || '',
    status: user.is_active ? '1' : '0',
    password: '',
    changePassword: false
  }
  new Modal(userModal.value).show()
}

// 显示分配角色模态框
const showAssignRolesModal = async (user) => {
  selectedUser.value = user
  await loadAllRoles()
  
  // 设置已选角色
  selectedRoles.value = user.roles.map(role => role.id)
  
  new Modal(assignRolesModal.value).show()
}

// 显示删除确认模态框
const confirmDeleteUser = (user) => {
  selectedUser.value = user
  new Modal(deleteConfirmModal.value).show()
}

// 提交用户表单
const submitUserForm = async () => {
  try {
    const formData = {
      username: userForm.value.username,
      name: userForm.value.name,
      email: userForm.value.email,
      is_active: userForm.value.status === '1'
    }

    if (!isEditing.value || userForm.value.changePassword) {
      if (!userForm.value.password) {
        message.error('请输入密码')
        return
      }
      formData.password = userForm.value.password
    }

    if (!isEditing.value) {
      await axios.post('/api/system/user/add', formData)
      message.success('添加用户成功')
    } else {
      await axios.put(`/api/system/user/update/${userForm.value.id}`, formData)
      message.success('更新用户成功')
    }

    // 关闭模态框并刷新列表
    try {
      if (userModal.value) {
        const modalInstance = Modal.getInstance(userModal.value)
        if (modalInstance) {
          modalInstance.hide()
        } else {
          // 如果无法获取模态框实例，使用原生方法关闭
          userModal.value.classList.remove('show')
          userModal.value.style.display = 'none'
          document.body.classList.remove('modal-open')
          const backdrop = document.querySelector('.modal-backdrop')
          if (backdrop && backdrop.parentNode) {
            backdrop.parentNode.removeChild(backdrop)
          }
        }
      }
    } catch (modalError) {
      console.error('关闭模态框失败:', modalError)
    }

    await loadUsers()
  } catch (err) {
    message.error((isEditing.value ? '更新用户失败' : '添加用户失败') + ': ' + (err.response?.data?.message || err.message))
  }
}

// 分配角色
const assignRoles = async () => {
  try {
    await axios.post(`/api/system/user/assign-roles/${selectedUser.value.id}`, {
      role_ids: selectedRoles.value
    })
    message.success('角色分配成功')
    
    // 关闭模态框并刷新列表
    try {
      if (assignRolesModal.value) {
        const modalInstance = Modal.getInstance(assignRolesModal.value)
        if (modalInstance) {
          modalInstance.hide()
        } else {
          // 如果无法获取模态框实例，使用原生方法关闭
          assignRolesModal.value.classList.remove('show')
          assignRolesModal.value.style.display = 'none'
          document.body.classList.remove('modal-open')
          const backdrop = document.querySelector('.modal-backdrop')
          if (backdrop && backdrop.parentNode) {
            backdrop.parentNode.removeChild(backdrop)
          }
        }
      }
    } catch (modalError) {
      console.error('关闭模态框失败:', modalError)
    }
    
    loadUsers()
  } catch (err) {
    message.error('角色分配失败: ' + (err.response?.data?.message || err.message))
  }
}

// 删除用户
const deleteUser = async () => {
  try {
    await axios.delete(`/api/system/user/delete/${selectedUser.value.id}`)
    message.success('用户删除成功')
    
    // 关闭模态框并刷新列表
    try {
      if (deleteConfirmModal.value) {
        const modalInstance = Modal.getInstance(deleteConfirmModal.value)
        if (modalInstance) {
          modalInstance.hide()
        } else {
          // 如果无法获取模态框实例，使用原生方法关闭
          deleteConfirmModal.value.classList.remove('show')
          deleteConfirmModal.value.style.display = 'none'
          document.body.classList.remove('modal-open')
          const backdrop = document.querySelector('.modal-backdrop')
          if (backdrop && backdrop.parentNode) {
            backdrop.parentNode.removeChild(backdrop)
          }
        }
      }
    } catch (modalError) {
      console.error('关闭模态框失败:', modalError)
    }
    
    loadUsers()
  } catch (err) {
    message.error('删除失败: ' + (err.response?.data?.message || err.message))
  }
}

// 切换用户状态
const toggleUserStatus = async (user) => {
  try {
    const newStatus = user.status === 1 ? 0 : 1
    await axios.put(`/api/system/user/update/${user.id}`, {
      status: newStatus
    })
    message.success(`用户${newStatus === 1 ? '启用' : '禁用'}成功`)
    loadUsers()
  } catch (err) {
    message.error('操作失败: ' + (err.response?.data?.message || err.message))
  }
}

// 切换页码
const changePage = (page) => {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  loadUsers()
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString()
}

// 页面加载时获取数据
onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.container {
  max-width: 1200px;
  margin: 0 auto;
}

.card {
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
}

.table th {
  font-weight: 600;
}

.badge {
  font-weight: 500;
}

.btn-group .btn {
  margin-right: 0.25rem;
}

.btn-group .btn:last-child {
  margin-right: 0;
}
</style> 