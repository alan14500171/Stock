<template>
  <div class="container mt-3">
    <div class="card">
      <div class="card-header d-flex justify-content-between align-items-center">
        <h5>角色管理</h5>
        <div class="d-flex">
          <div class="input-group me-2">
            <input 
              type="text" 
              class="form-control" 
              placeholder="搜索角色名称" 
              v-model="searchName"
              @keyup.enter="loadRoles"
            >
            <button class="btn btn-outline-secondary" type="button" @click="loadRoles">
              <i class="bi bi-search"></i>
            </button>
          </div>
          <button 
            class="btn btn-primary" 
            @click="showAddRoleModal"
          >
            <i class="bi bi-plus-lg"></i> 添加角色
          </button>
        </div>
      </div>
      <div class="card-body">
        <div class="table-responsive">
          <table class="table table-striped table-hover">
            <thead>
              <tr>
                <th>ID</th>
                <th>角色名称</th>
                <th>描述</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="role in roles" :key="role.id">
                <td>{{ role.id }}</td>
                <td>{{ role.name }}</td>
                <td>{{ role.description }}</td>
                <td>{{ formatDate(role.created_at) }}</td>
                <td>
                  <div class="btn-group">
                    <button 
                      class="btn btn-sm btn-outline-primary" 
                      @click="showEditRoleModal(role)"
                    >
                      <i class="bi bi-pencil"></i>
                    </button>
                    <button 
                      class="btn btn-sm btn-outline-success" 
                      @click="showAssignPermissionsModal(role)"
                    >
                      <i class="bi bi-key"></i>
                    </button>
                    <button 
                      class="btn btn-sm btn-outline-danger" 
                      @click="confirmDeleteRole(role)"
                    >
                      <i class="bi bi-trash"></i>
                    </button>
                  </div>
                </td>
              </tr>
              <tr v-if="roles.length === 0">
                <td colspan="5" class="text-center">暂无数据</td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <!-- 分页 -->
        <nav v-if="totalPages > 1">
          <ul class="pagination justify-content-center">
            <li class="page-item" :class="{ disabled: currentPage === 1 }">
              <a class="page-link" href="#" @click.prevent="changePage(currentPage - 1)">上一页</a>
            </li>
            <li 
              v-for="page in displayedPages" 
              :key="page" 
              class="page-item"
              :class="{ active: currentPage === page }"
            >
              <a class="page-link" href="#" @click.prevent="changePage(page)">{{ page }}</a>
            </li>
            <li class="page-item" :class="{ disabled: currentPage === totalPages }">
              <a class="page-link" href="#" @click.prevent="changePage(currentPage + 1)">下一页</a>
            </li>
          </ul>
        </nav>
      </div>
    </div>

    <!-- 添加/编辑角色模态框 -->
    <div class="modal fade" id="roleModal" tabindex="-1" ref="roleModal">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ isEditing ? '编辑角色' : '添加角色' }}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="submitRoleForm">
              <div class="mb-3">
                <label for="name" class="form-label">角色名称</label>
                <input 
                  type="text" 
                  class="form-control" 
                  id="name" 
                  v-model="roleForm.name"
                  required
                >
              </div>
              <div class="mb-3">
                <label for="description" class="form-label">描述</label>
                <textarea 
                  class="form-control" 
                  id="description" 
                  v-model="roleForm.description"
                  rows="3"
                ></textarea>
              </div>
              <div class="text-end">
                <button type="button" class="btn btn-secondary me-2" data-bs-dismiss="modal">取消</button>
                <button type="submit" class="btn btn-primary">保存</button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>

    <!-- 分配权限模态框 -->
    <div class="modal fade" id="assignPermissionsModal" tabindex="-1" ref="assignPermissionsModal">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">分配权限</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">角色: {{ selectedRole?.name }}</label>
            </div>
            <div class="mb-3">
              <label class="form-label">权限列表</label>
              <div class="permission-tree">
                <div v-for="module in permissionTree" :key="module.id" class="permission-module">
                  <div class="form-check">
                    <input 
                      class="form-check-input" 
                      type="checkbox" 
                      :id="'module-' + module.id" 
                      :value="module.id" 
                      v-model="selectedPermissions"
                      @change="toggleModulePermissions(module)"
                    >
                    <label class="form-check-label fw-bold" :for="'module-' + module.id">
                      {{ module.name }}
                    </label>
                  </div>
                  <div class="ms-4 mt-2">
                    <div v-for="menu in module.children" :key="menu.id" class="permission-menu mb-2">
                      <div class="form-check">
                        <input 
                          class="form-check-input" 
                          type="checkbox" 
                          :id="'menu-' + menu.id" 
                          :value="menu.id" 
                          v-model="selectedPermissions"
                          @change="toggleMenuPermissions(menu)"
                        >
                        <label class="form-check-label fw-bold" :for="'menu-' + menu.id">
                          {{ menu.name }}
                        </label>
                      </div>
                      <!-- 渲染第三级权限（按钮权限） -->
                      <div class="ms-4 mt-1" v-if="menu.children && menu.children.length > 0">
                        <div v-for="button in menu.children" :key="button.id" class="form-check">
                          <input 
                            class="form-check-input" 
                            type="checkbox" 
                            :id="'button-' + button.id" 
                            :value="button.id" 
                            v-model="selectedPermissions"
                          >
                          <label class="form-check-label" :for="'button-' + button.id">
                            {{ button.name }}
                          </label>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="text-end">
              <button type="button" class="btn btn-secondary me-2" data-bs-dismiss="modal">取消</button>
              <button type="button" class="btn btn-primary" @click="assignPermissions">保存</button>
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
            <p>确定要删除角色 "{{ selectedRole?.name }}" 吗？此操作不可撤销。</p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
            <button type="button" class="btn btn-danger" @click="deleteRole">删除</button>
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

// 角色列表数据
const roles = ref([])
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
const roleModal = ref(null)
const assignPermissionsModal = ref(null)
const deleteConfirmModal = ref(null)

// 表单数据
const roleForm = ref({
  name: '',
  description: ''
})

// 编辑状态
const isEditing = ref(false)
const selectedRole = ref(null)

// 权限相关
const permissionTree = ref([])
const selectedPermissions = ref([])

// 加载角色列表
const loadRoles = async () => {
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    
    if (searchName.value) {
      params.name = searchName.value
    }
    
    const response = await axios.get('/api/system/role/list', { params })
    if (response.data.success) {
      roles.value = response.data.data.items
      total.value = response.data.data.total
    } else {
      message.error('加载角色列表失败: ' + response.data.message)
    }
  } catch (err) {
    message.error('加载角色列表失败: ' + (err.response?.data?.message || err.message))
  }
}

// 加载权限树
const loadPermissionTree = async () => {
  try {
    const response = await axios.get('/api/system/permission/tree')
    if (response.data.success) {
      permissionTree.value = response.data.data
    } else {
      message.error('加载权限树失败: ' + response.data.message)
    }
  } catch (err) {
    message.error('加载权限树失败: ' + (err.response?.data?.message || err.message))
  }
}

// 显示添加角色模态框
const showAddRoleModal = () => {
  isEditing.value = false
  roleForm.value = {
    name: '',
    description: ''
  }
  new Modal(roleModal.value).show()
}

// 显示编辑角色模态框
const showEditRoleModal = (role) => {
  isEditing.value = true
  selectedRole.value = role
  roleForm.value = {
    id: role.id,
    name: role.name,
    description: role.description || ''
  }
  new Modal(roleModal.value).show()
}

// 显示分配权限模态框
const showAssignPermissionsModal = async (role) => {
  selectedRole.value = role
  await loadPermissionTree()
  
  // 获取角色详情，包括已分配的权限
  try {
    const response = await axios.get(`/api/system/role/detail/${role.id}`)
    if (response.data.success) {
      const roleDetail = response.data.data
      
      // 设置已选权限
      selectedPermissions.value = roleDetail.permissions.map(permission => permission.id)
    } else {
      message.error('获取角色详情失败: ' + response.data.message)
      return
    }
  } catch (err) {
    message.error('获取角色详情失败: ' + (err.response?.data?.message || err.message))
    return
  }
  
  new Modal(assignPermissionsModal.value).show()
}

// 显示删除确认模态框
const confirmDeleteRole = (role) => {
  selectedRole.value = role
  new Modal(deleteConfirmModal.value).show()
}

// 提交角色表单
const submitRoleForm = async () => {
  try {
    if (isEditing.value) {
      // 编辑角色
      const response = await axios.put(`/api/system/role/update/${roleForm.value.id}`, roleForm.value)
      if (response.data.success) {
        message.success('角色更新成功')
      } else {
        message.error('角色更新失败: ' + response.data.message)
        return
      }
    } else {
      // 添加角色
      const response = await axios.post('/api/system/role/add', roleForm.value)
      if (response.data.success) {
        message.success('角色添加成功')
      } else {
        message.error('角色添加失败: ' + response.data.message)
        return
      }
    }
    
    // 关闭模态框并刷新列表
    try {
      if (roleModal.value) {
        const modalInstance = Modal.getInstance(roleModal.value)
        if (modalInstance) {
          modalInstance.hide()
        }
      }
    } catch (modalError) {
      console.error('关闭模态框失败:', modalError)
    }
    
    loadRoles()
  } catch (err) {
    message.error('操作失败: ' + (err.response?.data?.message || err.message))
  }
}

// 切换模块下所有权限
const toggleModulePermissions = (module) => {
  const moduleSelected = selectedPermissions.value.includes(module.id)
  
  // 获取模块下所有子权限ID
  const childPermissionIds = []
  
  // 收集所有子菜单及其按钮权限
  module.children.forEach(menu => {
    childPermissionIds.push(menu.id)
    
    // 收集菜单下的按钮权限
    if (menu.children && menu.children.length > 0) {
      menu.children.forEach(button => {
        childPermissionIds.push(button.id)
      })
    }
  })
  
  if (moduleSelected) {
    // 如果选中模块，则添加所有子权限
    childPermissionIds.forEach(id => {
      if (!selectedPermissions.value.includes(id)) {
        selectedPermissions.value.push(id)
      }
    })
  } else {
    // 如果取消选中模块，则移除所有子权限
    selectedPermissions.value = selectedPermissions.value.filter(id => !childPermissionIds.includes(id))
  }
}

// 切换菜单下所有按钮权限
const toggleMenuPermissions = (menu) => {
  const menuSelected = selectedPermissions.value.includes(menu.id)
  
  // 获取菜单下所有按钮权限ID
  const buttonPermissionIds = menu.children ? menu.children.map(button => button.id) : []
  
  if (menuSelected) {
    // 如果选中菜单，则添加所有按钮权限
    buttonPermissionIds.forEach(id => {
      if (!selectedPermissions.value.includes(id)) {
        selectedPermissions.value.push(id)
      }
    })
  } else {
    // 如果取消选中菜单，则移除所有按钮权限
    selectedPermissions.value = selectedPermissions.value.filter(id => !buttonPermissionIds.includes(id))
  }
}

// 分配权限
const assignPermissions = async () => {
  try {
    const response = await axios.post(`/api/system/role/assign-permissions/${selectedRole.value.id}`, {
      permission_ids: selectedPermissions.value
    })
    
    if (response.data.success) {
      message.success('权限分配成功')
      
      // 关闭模态框并刷新列表
      try {
        if (assignPermissionsModal.value) {
          const modalInstance = Modal.getInstance(assignPermissionsModal.value)
          if (modalInstance) {
            modalInstance.hide()
          }
        }
      } catch (modalError) {
        console.error('关闭模态框失败:', modalError)
      }
      
      loadRoles()
    } else {
      message.error('权限分配失败: ' + response.data.message)
    }
  } catch (err) {
    message.error('权限分配失败: ' + (err.response?.data?.message || err.message))
  }
}

// 删除角色
const deleteRole = async () => {
  try {
    const response = await axios.delete(`/api/system/role/delete/${selectedRole.value.id}`)
    if (response.data.success) {
      message.success('角色删除成功')
      
      // 关闭模态框并刷新列表
      try {
        if (deleteConfirmModal.value) {
          const modalInstance = Modal.getInstance(deleteConfirmModal.value)
          if (modalInstance) {
            modalInstance.hide()
          }
        }
      } catch (modalError) {
        console.error('关闭模态框失败:', modalError)
      }
      
      loadRoles()
    } else {
      message.error('删除失败: ' + response.data.message)
    }
  } catch (err) {
    message.error('删除失败: ' + (err.response?.data?.message || err.message))
  }
}

// 切换页码
const changePage = (page) => {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  loadRoles()
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString()
}

// 页面加载时获取数据
onMounted(() => {
  loadRoles()
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

.btn-group .btn {
  margin-right: 0.25rem;
}

.btn-group .btn:last-child {
  margin-right: 0;
}

.permission-tree {
  max-height: 500px;
  overflow-y: auto;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
  padding: 1rem;
}

.permission-module {
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px dashed #e9ecef;
}

.permission-module:last-child {
  margin-bottom: 0;
  border-bottom: none;
  padding-bottom: 0;
}

.permission-menu {
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px dotted #f8f9fa;
}

.permission-menu:last-child {
  margin-bottom: 0;
  border-bottom: none;
  padding-bottom: 0;
}

.form-check-label.fw-bold {
  font-weight: 600;
}

/* 权限类型标识 */
.permission-module > .form-check > .form-check-label::after {
  content: " (模块)";
  font-size: 0.75rem;
  color: #0d6efd;
  font-weight: normal;
}

.permission-menu > .form-check > .form-check-label::after {
  content: " (菜单)";
  font-size: 0.75rem;
  color: #198754;
  font-weight: normal;
}
</style> 