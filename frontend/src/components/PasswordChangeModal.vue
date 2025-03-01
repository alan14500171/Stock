<template>
  <div class="password-change-modal">
    <!-- 弹窗 -->
    <div class="modal fade" id="passwordChangeModal" tabindex="-1" aria-labelledby="passwordChangeModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="passwordChangeModalLabel">修改密码</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <!-- 成功提示 -->
            <div v-if="success" class="alert alert-success alert-dismissible fade show" role="alert">
              {{ success }}
              <button type="button" class="btn-close" @click="success = ''"></button>
            </div>
            
            <!-- 错误提示 -->
            <div v-if="error" class="alert alert-danger alert-dismissible fade show" role="alert">
              {{ error }}
              <button type="button" class="btn-close" @click="error = ''"></button>
            </div>
            
            <!-- 提示信息 -->
            <div class="alert alert-info mb-4">
              <i class="bi bi-info-circle me-2"></i>
              为了保障账户安全，请定期修改密码。建议使用包含字母、数字和特殊字符的强密码。
            </div>

            <form @submit.prevent="handleChangePassword">
              <!-- 当前密码 -->
              <div class="form-floating mb-3">
                <input 
                  type="password" 
                  class="form-control" 
                  id="currentPassword" 
                  v-model="form.currentPassword"
                  placeholder="当前密码"
                  autocomplete="current-password"
                  required
                  :disabled="loading"
                >
                <label for="currentPassword">当前密码</label>
              </div>

              <!-- 新密码 -->
              <div class="form-floating mb-3">
                <input 
                  type="password" 
                  class="form-control" 
                  id="newPassword" 
                  v-model="form.newPassword"
                  placeholder="新密码"
                  autocomplete="new-password"
                  required
                  :disabled="loading"
                >
                <label for="newPassword">新密码</label>
              </div>

              <!-- 确认新密码 -->
              <div class="form-floating mb-3">
                <input 
                  type="password" 
                  class="form-control" 
                  id="confirmPassword" 
                  v-model="form.confirmPassword"
                  placeholder="确认新密码"
                  autocomplete="new-password"
                  required
                  :disabled="loading"
                >
                <label for="confirmPassword">确认新密码</label>
                <div v-if="passwordMismatch" class="text-danger mt-1 small">
                  两次输入的新密码不一致
                </div>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
            <button 
              type="button" 
              class="btn btn-primary"
              @click="handleChangePassword"
              :disabled="loading || !isFormValid"
            >
              <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
              {{ loading ? '提交中...' : '修改密码' }}
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
import { useMessage } from '../composables/useMessage'

// 引入Bootstrap的Modal
let passwordModal = null
// 标志位，防止自动打开
const autoOpenPrevented = ref(true)

onMounted(() => {
  // 动态导入Bootstrap的Modal组件
  import('bootstrap/js/dist/modal').then(module => {
    const Modal = module.default
    // 初始化Modal
    passwordModal = new Modal(document.getElementById('passwordChangeModal'))
    
    // 防止自动打开模态框
    const modalElement = document.getElementById('passwordChangeModal')
    if (modalElement) {
      modalElement.addEventListener('show.bs.modal', (event) => {
        if (autoOpenPrevented.value) {
          event.preventDefault()
          console.log('防止密码修改模态框自动打开')
          autoOpenPrevented.value = false // 重置标志位，以便后续手动打开
        }
      })
    }
  })
})

const message = useMessage()

const form = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const loading = ref(false)
const error = ref('')
const success = ref('')

// 检查两次输入的密码是否一致
const passwordMismatch = computed(() => {
  return form.newPassword && form.confirmPassword && 
         form.newPassword !== form.confirmPassword
})

// 表单验证
const isFormValid = computed(() => {
  return form.currentPassword && 
         form.newPassword && 
         form.confirmPassword && 
         form.newPassword === form.confirmPassword
})

// 打开弹窗
const openModal = () => {
  if (passwordModal) {
    // 重置表单
    form.currentPassword = ''
    form.newPassword = ''
    form.confirmPassword = ''
    error.value = ''
    success.value = ''
    
    // 允许打开模态框
    autoOpenPrevented.value = false
    passwordModal.show()
  }
}

// 关闭弹窗
const closeModal = () => {
  if (passwordModal) {
    passwordModal.hide()
  }
}

const handleChangePassword = async () => {
  if (loading.value) return
  
  // 清除提示信息
  error.value = ''
  success.value = ''
  
  // 验证表单
  if (!isFormValid.value) {
    if (passwordMismatch.value) {
      error.value = '两次输入的新密码不一致'
    } else {
      error.value = '请填写所有必填字段'
    }
    return
  }
  
  loading.value = true
  
  try {
    const response = await axios.post('/api/auth/change_password', {
      current_password: form.currentPassword,
      new_password: form.newPassword
    })
    
    if (response.data.success) {
      success.value = '密码修改成功'
      message.success('密码修改成功')
      
      // 清空表单
      form.currentPassword = ''
      form.newPassword = ''
      form.confirmPassword = ''
      
      // 3秒后关闭弹窗
      setTimeout(() => {
        closeModal()
      }, 3000)
    } else {
      error.value = response.data.message || '密码修改失败'
    }
  } catch (err) {
    console.error('密码修改失败:', err)
    error.value = err.response?.data?.message || '密码修改失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

// 导出方法供外部使用
defineExpose({
  openModal,
  closeModal
})
</script>

<style scoped>
.modal-content {
  border: none;
  border-radius: 10px;
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
}

.modal-header {
  border-bottom: 1px solid #e9ecef;
  background-color: #f8f9fa;
  border-top-left-radius: 10px;
  border-top-right-radius: 10px;
}

.modal-footer {
  border-top: 1px solid #e9ecef;
  background-color: #f8f9fa;
  border-bottom-left-radius: 10px;
  border-bottom-right-radius: 10px;
}

.form-floating > label {
  color: #6c757d;
}

.form-control:focus {
  border-color: #0d6efd;
  box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
}

.btn-primary {
  background-color: #0d6efd;
  border-color: #0d6efd;
}

.btn-primary:hover {
  background-color: #0b5ed7;
  border-color: #0a58ca;
}

.alert {
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.spinner-border {
  width: 1rem;
  height: 1rem;
}

.alert-info {
  background-color: #cff4fc;
  border-color: #b6effb;
  color: #055160;
}
</style> 