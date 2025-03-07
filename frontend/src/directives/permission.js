import { usePermissionStore } from '../stores/permission'

/**
 * 权限指令
 * 用法：v-permission="'system:user:add'"
 * 如果用户没有指定权限，则元素不会渲染
 */
export const permission = {
  mounted(el, binding) {
    const permissionStore = usePermissionStore()
    const permission = binding.value
    
    if (permission && !permissionStore.hasPermission(permission)) {
      // 如果没有权限，则移除元素
      el.parentNode && el.parentNode.removeChild(el)
    }
  }
}

/**
 * 角色指令
 * 用法：v-role="'admin'"
 * 如果用户没有指定角色，则元素不会渲染
 */
export const role = {
  mounted(el, binding) {
    const permissionStore = usePermissionStore()
    const role = binding.value
    
    if (role && !permissionStore.hasRole(role)) {
      // 如果没有角色，则移除元素
      el.parentNode && el.parentNode.removeChild(el)
    }
  }
}

export default {
  install(app) {
    app.directive('permission', permission)
    app.directive('role', role)
  }
} 