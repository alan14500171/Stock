<template>
  <div class="container mt-3">
    <div class="card">
      <div class="card-header d-flex justify-content-between align-items-center">
        <h5>权限管理</h5>
        <div class="d-flex">
          <button 
            class="btn btn-primary" 
            @click="showAddPermissionModal" 
            v-permission="'system:permission:add'"
          >
            <i class="bi bi-plus-lg"></i> 添加权限
          </button>
        </div>
      </div>
      <div class="card-body" v-permission="'system:permission:view'">
        <div class="permission-tree-container">
          <!-- 使用 Element Plus 的树形控件 -->
          <el-tree
            :data="permissionTree"
            :props="defaultProps"
            node-key="id"
            :default-expanded-keys="[]"
            :expand-on-click-node="false"
            highlight-current
          >
            <template #default="{ node, data }">
              <div class="custom-tree-node">
                <div class="node-content">
                  <span class="node-label">{{ data.name }}</span>
                  <el-tag size="small" :type="getTagType(data.type)" class="ml-2">
                    {{ getTypeName(data.type) }}
                  </el-tag>
                  <span class="permission-code">{{ data.code }}</span>
                </div>
                <div class="node-actions">
                  <el-button
                    type="primary"
                    size="small"
                    circle
                    @click="showEditPermissionModal(data)"
                    v-permission="'system:permission:edit'"
                  >
                    <el-icon><Edit /></el-icon>
                  </el-button>
                  <el-button
                    type="danger"
                    size="small"
                    circle
                    @click="confirmDeletePermission(data)"
                    v-permission="'system:permission:delete'"
                  >
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
            </template>
          </el-tree>
        </div>
      </div>
    </div>

    <!-- 添加/编辑权限模态框 -->
    <el-dialog
      v-model="permissionDialogVisible"
      :title="isEditing ? '编辑权限' : '添加权限'"
      width="500px"
    >
      <el-form :model="permissionForm" label-width="100px" :rules="rules" ref="permissionFormRef">
        <el-form-item label="权限名称" prop="name">
          <el-input v-model="permissionForm.name" placeholder="请输入权限名称"></el-input>
        </el-form-item>
        <el-form-item label="权限标识" prop="code">
          <el-input v-model="permissionForm.code" placeholder="请输入权限标识">
            <template #append>
              <el-button @click="generatePermissionCode" title="根据父级权限和名称自动生成权限标识">
                <el-icon><Plus /></el-icon>
              </el-button>
            </template>
          </el-input>
          <div class="el-form-item-helper">例如：system:user:view</div>
        </el-form-item>
        <el-form-item label="权限类型" prop="type">
          <el-select v-model="permissionForm.type" placeholder="请选择权限类型" class="w-100">
            <el-option label="模块" value="1"></el-option>
            <el-option label="菜单" value="2"></el-option>
            <el-option label="按钮" value="3"></el-option>
            <el-option label="数据" value="4"></el-option>
            <el-option label="接口" value="5"></el-option>
          </el-select>
          <div class="el-form-item-helper">
            <el-tag size="small" type="primary" class="me-1">模块</el-tag>: 顶级功能模块
            <el-tag size="small" type="success" class="me-1 ms-2">菜单</el-tag>: 可导航的菜单项
            <el-tag size="small" type="info" class="me-1 ms-2">按钮</el-tag>: 页面上的操作按钮
            <el-tag size="small" type="warning" class="me-1 ms-2">数据</el-tag>: 数据访问权限
            <el-tag size="small" type="danger" class="me-1 ms-2">接口</el-tag>: API接口调用权限
          </div>
        </el-form-item>
        <el-form-item label="父级权限" prop="parent_id">
          <el-input
            v-model="parentSearchQuery"
            placeholder="搜索权限..."
            @input="filterParentPermissions"
            class="mb-2"
          >
            <template #append>
              <el-button @click="parentSearchQuery = ''; filterParentPermissions()">
                <el-icon><CircleClose /></el-icon>
              </el-button>
            </template>
          </el-input>
          <el-select v-model="permissionForm.parent_id" placeholder="请选择父级权限" class="w-100">
            <el-option label="无 (作为顶级权限)" value="0"></el-option>
            <el-option
              v-for="parent in filteredParentPermissions"
              :key="parent.id"
              :label="'│'.repeat(parent.level) + (parent.level > 0 ? '├─ ' : '') + parent.name + ' (' + getTypeName(parent.type) + ')'"
              :value="parent.id.toString()"
            ></el-option>
          </el-select>
          <div class="el-form-item-helper">
            选择适当的父级权限，建立清晰的权限层级结构。模块通常作为顶级权限，菜单作为模块的子权限，按钮作为菜单的子权限。
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="permissionDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitPermissionForm" :loading="submitting">
            {{ isEditing ? '更新' : '添加' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 删除确认对话框 -->
    <el-dialog
      v-model="deleteDialogVisible"
      title="确认删除"
      width="400px"
    >
      <div>
        确定要删除权限 <strong>{{ selectedPermission?.name }}</strong> 吗？
        <p class="text-danger mt-2">
          <i class="el-icon-warning"></i> 
          此操作将同时删除该权限下的所有子权限，且不可恢复！
        </p>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="deleteDialogVisible = false">取消</el-button>
          <el-button type="danger" @click="deletePermission" :loading="submitting">
            确认删除
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { useMessage } from '@/composables/useMessage'
import { Edit, Delete, Plus, Search, CircleClose } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

// 消息提示
const message = useMessage()

// 权限列表数据
const permissions = ref([])
const permissionTree = ref([])

// 树形控件配置
const defaultProps = {
  children: 'children',
  label: 'name'
}

// 对话框可见性
const permissionDialogVisible = ref(false)
const deleteDialogVisible = ref(false)

// 表单引用
const permissionFormRef = ref(null)

// 表单数据
const permissionForm = ref({
  name: '',
  code: '',
  type: '2',
  parent_id: '0'
})

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入权限名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入权限标识', trigger: 'blur' },
    { pattern: /^[a-z0-9:]+$/, message: '权限标识只能包含小写字母、数字和冒号', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择权限类型', trigger: 'change' }
  ]
}

// 编辑状态
const isEditing = ref(false)
const selectedPermission = ref(null)

// 父级权限选项（排除当前编辑的权限及其子权限）
const parentPermissions = ref([])

// 父级权限搜索
const parentSearchQuery = ref('')
const filteredParentPermissions = ref([])

// 加载权限列表
const loadPermissions = async () => {
  try {
    // 获取权限树
    const response = await axios.get('/api/system/permission/tree')
    permissionTree.value = response.data.data
    
    // 同时获取扁平列表用于其他操作
    const listResponse = await axios.get('/api/system/permission/list')
    permissions.value = listResponse.data.data
  } catch (err) {
    ElMessage.error('加载权限列表失败: ' + (err.response?.data?.message || err.message))
  }
}

// 加载可选的父级权限
const loadParentPermissions = async () => {
  try {
    // 获取所有权限
    const response = await axios.get('/api/system/permission/list')
    const allPermissions = response.data.data
    
    // 如果是编辑模式，需要排除当前权限及其子权限
    if (isEditing.value && selectedPermission.value) {
      // 获取当前权限的所有子权限ID（包括自身）
      const childIds = getChildPermissionIds(allPermissions, selectedPermission.value.id)
      
      // 过滤掉子权限
      parentPermissions.value = allPermissions.filter(p => !childIds.includes(p.id))
    } else {
      parentPermissions.value = allPermissions
    }
  } catch (err) {
    ElMessage.error('加载父级权限失败: ' + (err.response?.data?.message || err.message))
  }
  
  // 初始化过滤后的父级权限
  filteredParentPermissions.value = parentPermissions.value
}

// 获取权限的所有子权限ID（包括自身）
const getChildPermissionIds = (permissions, parentId) => {
  if (!parentId) return []
  
  const ids = [parentId]
  
  const findChildren = (parentId) => {
    if (!parentId) return
    
    permissions.forEach(p => {
      if (p.parent_id && p.parent_id.toString() === parentId.toString()) {
        ids.push(p.id)
        findChildren(p.id)
      }
    })
  }
  
  findChildren(parentId)
  return ids
}

// 显示添加权限模态框
const showAddPermissionModal = async () => {
  isEditing.value = false
  permissionForm.value = {
    name: '',
    code: '',
    type: '2',
    parent_id: '0'
  }
  
  await loadParentPermissions()
  permissionDialogVisible.value = true
}

// 显示编辑权限模态框
const showEditPermissionModal = async (permission) => {
  isEditing.value = true
  selectedPermission.value = permission
  permissionForm.value = {
    id: permission.id,
    name: permission.name || '',
    code: permission.code || '',
    type: permission.type !== null && permission.type !== undefined ? permission.type.toString() : '3',
    parent_id: permission.parent_id !== null && permission.parent_id !== undefined ? permission.parent_id.toString() : '0'
  }
  
  await loadParentPermissions()
  permissionDialogVisible.value = true
}

// 显示删除确认模态框
const confirmDeletePermission = (permission) => {
  selectedPermission.value = permission
  deleteDialogVisible.value = true
}

// 提交权限表单
const submitPermissionForm = async () => {
  try {
    if (isEditing.value) {
      // 编辑权限
      await axios.put(`/api/system/permission/update/${permissionForm.value.id}`, permissionForm.value)
      ElMessage.success('权限更新成功')
    } else {
      // 添加权限
      await axios.post('/api/system/permission/add', permissionForm.value)
      ElMessage.success('权限添加成功')
    }
    
    // 关闭模态框并刷新列表
    permissionDialogVisible.value = false
    loadPermissions()
  } catch (err) {
    ElMessage.error('操作失败: ' + (err.response?.data?.message || err.message))
  }
}

// 删除权限
const deletePermission = async () => {
  try {
    await axios.delete(`/api/system/permission/delete/${selectedPermission.value.id}`)
    ElMessage.success('权限删除成功')
    
    // 关闭模态框并刷新列表
    deleteDialogVisible.value = false
    loadPermissions()
  } catch (err) {
    ElMessage.error('删除失败: ' + (err.response?.data?.message || err.message))
  }
}

// 根据父级权限和名称自动生成权限标识
const generatePermissionCode = async () => {
  if (!permissionForm.value.name) {
    ElMessage.warning('请先输入权限名称')
    return
  }
  
  // 获取父级权限的code
  let parentCode = ''
  if (permissionForm.value.parent_id && permissionForm.value.parent_id !== '0') {
    const parent = parentPermissions.value.find(p => p.id.toString() === permissionForm.value.parent_id)
    if (parent) {
      parentCode = parent.code
    } else {
      ElMessage.warning('找不到所选的父级权限')
      return
    }
  }
  
  // 将权限名称转换为拼音或英文（简单处理，实际可能需要更复杂的转换）
  const nameCode = permissionForm.value.name
    .toLowerCase()
    .replace(/[^\w\s]/gi, '')
    .replace(/\s+/g, '_')
  
  // 生成权限标识
  if (parentCode) {
    permissionForm.value.code = `${parentCode}:${nameCode}`
  } else {
    permissionForm.value.code = nameCode
  }
}

// 过滤父级权限
const filterParentPermissions = () => {
  if (!parentSearchQuery.value) {
    filteredParentPermissions.value = parentPermissions.value
    return
  }
  
  const query = parentSearchQuery.value.toLowerCase()
  filteredParentPermissions.value = parentPermissions.value.filter(p => 
    p.name.toLowerCase().includes(query) || 
    p.code.toLowerCase().includes(query)
  )
}

// 获取权限类型名称
const getTypeName = (type) => {
  const types = {
    1: '模块',
    2: '菜单',
    3: '按钮',
    4: '数据',
    5: '接口'
  }
  return types[type] || '未知'
}

// 获取Element Plus标签类型
const getTagType = (type) => {
  const types = {
    1: 'primary',
    2: 'success',
    3: 'info',
    4: 'warning',
    5: 'danger'
  }
  return types[type] || 'info'
}

// 页面加载时获取权限列表
onMounted(() => {
  loadPermissions()
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

.permission-tree-container {
  min-height: 400px;
}

.custom-tree-node {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  padding-right: 8px;
  width: 100%;
}

.node-content {
  display: flex;
  align-items: center;
}

.node-label {
  font-weight: 500;
  margin-right: 8px;
}

.permission-code {
  color: #909399;
  margin-left: 8px;
  font-size: 12px;
  font-family: monospace;
}

.node-actions {
  margin-left: 8px;
}

.node-actions .el-button {
  margin-left: 6px;
}

.el-form-item-helper {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.w-100 {
  width: 100%;
}

.ml-2 {
  margin-left: 8px;
}

.me-1 {
  margin-right: 4px;
}

.ms-2 {
  margin-left: 8px;
}

.mb-2 {
  margin-bottom: 8px;
}
</style>