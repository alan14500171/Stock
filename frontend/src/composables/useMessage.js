import { ref } from 'vue'
import { Toast } from 'bootstrap'

// 创建一个全局消息队列
const messages = ref([])
let messageId = 0

// 消息提示组合式函数
export function useMessage() {
  const showMessage = (message, type = 'primary', duration = 3000) => {
    // 创建toast元素
    const toastEl = document.createElement('div')
    toastEl.className = `toast align-items-center text-white bg-${type} border-0`
    toastEl.setAttribute('role', 'alert')
    toastEl.setAttribute('aria-live', 'assertive')
    toastEl.setAttribute('aria-atomic', 'true')
    
    // 设置toast内容
    toastEl.innerHTML = `
      <div class="d-flex">
        <div class="toast-body">
          ${message}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
    `
    
    // 创建toast容器（如果不存在）
    let toastContainer = document.getElementById('toast-container')
    if (!toastContainer) {
      toastContainer = document.createElement('div')
      toastContainer.id = 'toast-container'
      toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3'
      toastContainer.style.zIndex = '1080'
      document.body.appendChild(toastContainer)
    }
    
    // 添加toast到容器
    toastContainer.appendChild(toastEl)
    
    // 初始化并显示toast
    const toast = new Toast(toastEl, {
      autohide: true,
      delay: duration
    })
    
    toast.show()
    
    // 自动移除元素
    toastEl.addEventListener('hidden.bs.toast', () => {
      toastEl.remove()
    })
  }
  
  // 成功消息
  const success = (message, duration) => {
    showMessage(message, 'success', duration)
  }
  
  // 错误消息
  const error = (message, duration) => {
    showMessage(message, 'danger', duration)
  }
  
  // 警告消息
  const warning = (message, duration) => {
    showMessage(message, 'warning', duration)
  }
  
  // 信息消息
  const info = (message, duration) => {
    showMessage(message, 'info', duration)
  }
  
  return {
    success,
    error,
    warning,
    info
  }
} 