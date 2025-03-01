import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

export const usePermissionStore = defineStore('permission', () => {
  // 用户权限列表
  const permissions = ref([])
  // 用户角色列表
  const roles = ref([])
  // 是否已加载权限
  const loaded = ref(false)
  // 加载状态
  const loading = ref(false)

  // 加载用户权限
  const loadPermissions = async () => {
    if (loaded.value) {
      console.log('权限已加载，跳过加载过程')
      return
    }
    
    console.log('开始加载用户权限')
    loading.value = true
    try {
      // 检查用户是否是管理员
      let isAdmin = false
      try {
        const user = JSON.parse(localStorage.getItem('user') || '{}')
        isAdmin = user.username === 'alan' || user.username === 'admin'
        console.log('当前用户:', user.username, '是否管理员:', isAdmin)
      } catch (e) {
        console.error('解析用户信息失败:', e)
      }
      
      // 如果是管理员用户，直接设置所有权限
      if (isAdmin) {
        console.log('管理员用户，设置所有权限')
        setAdminPermissions()
        return
      }
      
      try {
        console.log('发送请求获取用户信息和权限')
        const response = await axios.get('/api/system/user/info')
        console.log('获取用户信息响应:', response.data)
        
        if (response.data.success) {
          // 处理权限数据
          // 后端返回的权限可能是字符串数组或对象数组，需要统一处理
          const permissionsData = response.data.data.permissions || []
          console.log('后端返回的权限数据类型:', typeof permissionsData, Array.isArray(permissionsData) ? '数组' : '非数组')
          console.log('后端返回的权限数据:', permissionsData)
          
          if (permissionsData.length > 0) {
            // 检查第一个元素是否为字符串
            const firstItem = permissionsData[0]
            console.log('权限数据第一项类型:', typeof firstItem)
            
            if (typeof firstItem === 'string') {
              // 如果是字符串数组，转换为对象数组
              permissions.value = permissionsData.map(code => ({ code }))
              console.log('将权限字符串数组转换为对象数组:', permissions.value)
            } else {
              // 如果已经是对象数组，直接使用
              permissions.value = permissionsData
            }
          } else {
            permissions.value = []
            console.log('权限数据为空，设置为空数组')
          }
          
          // 处理角色数据
          const rolesData = response.data.data.roles || []
          console.log('后端返回的角色数据:', rolesData)
          roles.value = rolesData
          loaded.value = true
          
          console.log('成功加载权限:', permissions.value.length, '个权限,', roles.value.length, '个角色')
          console.log('权限列表:', permissions.value.map(p => p.code || p))
          console.log('角色列表:', roles.value.map(r => r.name || r))
        } else {
          console.error('加载权限失败:', response.data.message)
          // 设置默认权限，允许用户访问基本功能
          setDefaultPermissions()
        }
      } catch (error) {
        console.error('加载权限请求失败:', error)
        // 设置默认权限，允许用户访问基本功能
        setDefaultPermissions()
      }
    } finally {
      loading.value = false
    }
  }

  // 设置管理员权限
  const setAdminPermissions = () => {
    console.log('设置管理员权限')
    permissions.value = [
      { code: 'system:user:view' },
      { code: 'system:role:view' },
      { code: 'system:permission:view' },
      { code: 'system:user:add' },
      { code: 'system:user:edit' },
      { code: 'system:user:delete' },
      { code: 'system:role:add' },
      { code: 'system:role:edit' },
      { code: 'system:role:delete' },
      { code: 'system:permission:add' },
      { code: 'system:permission:edit' },
      { code: 'system:permission:delete' },
      { code: 'system:user:list' },
      { code: 'system:role:list' },
      { code: 'system:permission:list' }
    ]
    roles.value = [{ name: 'admin' }]
    loaded.value = true
    console.log('管理员权限设置完成')
  }

  // 设置默认权限
  const setDefaultPermissions = () => {
    // 默认只设置基本权限
    console.log('设置默认权限（基本权限）')
    permissions.value = []
    roles.value = []
    loaded.value = true
  }

  // 检查是否有指定权限
  const hasPermission = (permission) => {
    // 检查用户是否是管理员
    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}')
      if (user.username === 'alan' || user.username === 'admin') {
        console.log('管理员用户，自动通过权限检查:', permission)
        return true
      }
    } catch (e) {
      console.error('解析用户信息失败:', e)
    }
    
    // 如果没有传入权限标识，或者权限列表为空，则返回 false
    if (!permission || permissions.value.length === 0) {
      console.log('权限检查失败:', permission, '权限列表为空或未指定权限')
      return false
    }
    
    // 检查是否包含指定权限
    const result = permissions.value.some(p => {
      // 处理权限对象或字符串
      const permCode = typeof p === 'string' ? p : p.code
      return permCode === permission
    })
    console.log('权限检查:', permission, result ? '通过' : '未通过')
    return result
  }

  // 检查是否有指定角色
  const hasRole = (role) => {
    // 检查用户是否是管理员
    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}')
      if (user.username === 'alan' || user.username === 'admin') {
        console.log('管理员用户，自动通过角色检查:', role)
        return true
      }
    } catch (e) {
      console.error('解析用户信息失败:', e)
    }
    
    // 如果没有传入角色标识，或者角色列表为空，则返回 false
    if (!role || roles.value.length === 0) {
      console.log('角色检查失败:', role, '角色列表为空或未指定角色')
      return false
    }
    
    // 检查是否包含指定角色
    const result = roles.value.some(r => {
      // 处理角色对象或字符串
      const roleName = typeof r === 'string' ? r : r.name
      return roleName === role
    })
    console.log('角色检查:', role, result ? '通过' : '未通过')
    return result
  }

  // 重置权限状态
  const resetPermissions = () => {
    console.log('重置权限状态')
    permissions.value = []
    roles.value = []
    loaded.value = false
  }

  return {
    permissions,
    roles,
    loaded,
    loading,
    loadPermissions,
    hasPermission,
    hasRole,
    resetPermissions,
    setAdminPermissions,
    setDefaultPermissions
  }
}) 