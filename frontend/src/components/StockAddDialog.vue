<template>
  <div v-if="modelValue">
    <div class="modal fade" :class="{ show: modelValue }" tabindex="-1" data-testid="stock-add-dialog">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" data-testid="dialog-title">{{ editData ? '编辑股票' : '添加新股票' }}</h5>
            <button type="button" class="btn-close" @click="handleClose" data-testid="close-btn"></button>
          </div>
          <div class="modal-body" v-permission="editData ? 'stock:list:edit' : 'stock:list:add'">
            <form @submit.prevent="handleSubmit">
              <div class="mb-3">
                <label class="form-label" data-testid="stock-code-label">股票代码</label>
                <input 
                  type="text" 
                  class="form-control" 
                  v-model="form.code"
                  :class="{ 'is-invalid': errors.code }"
                  placeholder="输入股票代码后将自动查询股票信息"
                  @keydown.enter.prevent="handleCodeEnter"
                  @keydown.tab.prevent="handleCodeEnter"
                  :readonly="!!editData"
                  data-testid="stock-code-input"
                />
                <div class="invalid-feedback" data-testid="stock-code-error">{{ errors.code }}</div>
              </div>

              <div class="mb-3">
                <label class="form-label" data-testid="stock-market-label">市场</label>
                <input 
                  type="text" 
                  class="form-control" 
                  v-model="form.market"
                  :class="{ 'is-invalid': errors.market }"
                  :readonly="true"
                  data-testid="stock-market-input"
                />
                <div class="invalid-feedback" data-testid="stock-market-error">{{ errors.market }}</div>
              </div>

              <div class="mb-3">
                <label class="form-label" data-testid="stock-name-label">股票名称</label>
                <input 
                  type="text" 
                  class="form-control" 
                  v-model="form.code_name"
                  :class="{ 'is-invalid': errors.code_name }"
                  :readonly="!editData"
                  data-testid="stock-name-input"
                />
                <div class="invalid-feedback" data-testid="stock-name-error">{{ errors.code_name }}</div>
              </div>

              <div class="mb-3">
                <label class="form-label" data-testid="google-code-label">谷歌查询代码</label>
                <input 
                  type="text" 
                  class="form-control" 
                  v-model="form.google_code"
                  :readonly="!editData"
                  data-testid="google-code-input"
                />
              </div>

              <div class="mb-3">
                <label class="form-label" data-testid="current-price-label">当前股价</label>
                <input 
                  type="text" 
                  class="form-control" 
                  :value="form.current_price"
                  readonly
                  data-testid="current-price-input"
                />
                <div v-if="alertMessage" :class="{ 
                    'text-danger': alertMessage.includes('已存在'), 
                    'text-primary': alertMessage.includes('查询失败')
                  }"
                  data-testid="alert-message"
                >
                  {{ alertMessage }}
                </div>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="handleClose" data-testid="cancel-btn">取消</button>
            <button 
              type="button" 
              class="btn btn-primary" 
              @click="handleSubmit"
              :disabled="submitting"
              data-testid="submit-btn"
              v-permission="editData ? 'stock:list:edit' : 'stock:list:add'"
            >
              <span v-if="submitting" class="spinner-border spinner-border-sm me-1"></span>
              {{ editData ? '保存修改' : '确认添加' }}
            </button>
          </div>
        </div>
      </div>
    </div>
    <div class="modal-backdrop fade show" data-testid="modal-backdrop"></div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import axios from 'axios'
import { useMessage } from '../composables/useMessage'

const props = defineProps({
  modelValue: Boolean,
  editData: {
    type: Object,
    default: () => null
  }
})

const emit = defineEmits(['update:modelValue', 'success'])
const message = useMessage()

const submitting = ref(false)
const errors = ref({})
const alertMessage = ref('')
const stockSelected = ref(false)

// 表单数据
const form = ref({
  market: '',
  code: '',
  code_name: '',
  google_code: '',
  current_price: null
})

const resetFormExceptCode = () => {
  const currentCode = form.value.code
  form.value = {
    market: '',
    code: currentCode,
    code_name: '',
    google_code: '',
    current_price: null
  }
  errors.value = {}
}

// 添加计算属性判断是否是错误消息
const isErrorMessage = computed(() => {
  return alertMessage.value && (
    alertMessage.value.includes('已存在') ||
    alertMessage.value.includes('添加失败')
  )
})

// 在 script 部分添加
const displayPrice = computed(() => {
  return form.value.current_price || ''
})

// 处理股票代码回车和Tab事件
const handleCodeEnter = async (event) => {
  event.preventDefault()
  if (!form.value.code) {
    return
  }
  
  errors.value = {}
  alertMessage.value = ''
  
  try {
    // 查询股票信息
    const response = await axios.get(`/api/stock/search_stock?code=${encodeURIComponent(form.value.code)}`)
    
    if (response.data.success && response.data.data.length > 0) {
      const stockData = response.data.data[0]
      stockData.market = stockData.market === 'HK' || stockData.exchange === 'HKG' ? 'HK' : 'USA'

      // 检查股票是否已存在
      const checkResponse = await axios.get('/api/stock/stocks', {
        params: {
          search: form.value.code
        }
      })
      
      if (checkResponse.data.success && checkResponse.data.data.items.length > 0) {
        const existingStock = checkResponse.data.data.items.find(
          stock => stock.code === form.value.code
        )
        if (existingStock) {
          alertMessage.value = '该股票代码已存在'
          resetFormExceptCode()
          return
        }
      }

      // 更新表单数据,保持原始代码
      form.value.current_price = stockData.price
      form.value.google_code = stockData.query
      form.value.code_name = stockData.code_name || stockData.name || ''
      form.value.market = stockData.market
      
      if (form.value.code_name) {
        stockSelected.value = true
      } else {
        errors.value.code_name = '未能获取公司名称'
      }
    } else {
      alertMessage.value = '未找到股票信息，请检查股票代码是否正确'
      resetFormExceptCode()
    }
  } catch (error) {
    alertMessage.value = '查询失败，请检查股票代码是否正确'
    resetFormExceptCode()
  }
}

// 监听股票代码变化
watch(() => form.value.code, (newCode) => {
  if (!newCode) {
    resetForm()
  } else if (stockSelected.value) {
    // 如果已经选择了股票，且代码发生变化，重置选择状态
    stockSelected.value = false
  }
})

// 重置表单
const resetForm = () => {
  form.value = {
    market: '',
    code: '',
    code_name: '',
    google_code: '',
    current_price: null
  }
  errors.value = {}
  alertMessage.value = ''
  stockSelected.value = false
}

// 表单验证
const validateForm = () => {
  errors.value = {}
  let isValid = true

  if (!form.value.code || !form.value.code.trim()) {
    errors.value.code = '请输入股票代码'
    isValid = false
  }

  if (!form.value.market || !form.value.market.trim()) {
    errors.value.market = '请选择市场'
    isValid = false
  }

  if (!form.value.code_name || !form.value.code_name.trim()) {
    errors.value.code_name = '请输入股票名称'
    isValid = false
  }

  if (!form.value.google_code || !form.value.google_code.trim()) {
    errors.value.google_code = '请输入谷歌查询代码'
    isValid = false
  }

  return isValid
}

// 关闭对话框
const handleClose = () => {
  emit('update:modelValue', false)
  resetForm()
}

// 监听 editData 变化
watch(() => props.editData, (newData) => {
  if (newData) {
    // 直接使用原始数据,不做任何格式处理
    form.value = {
      code: newData.code,
      market: newData.market,
      code_name: newData.code_name,
      google_code: newData.google_name,
      current_price: newData.current_price
    }
    stockSelected.value = true
  } else {
    resetForm()
  }
}, { immediate: true })

// 修改提交表单方法
const handleSubmit = async () => {
  if (!validateForm() || submitting.value) return
  
  try {
    submitting.value = true
    
    // 检查并记录表单数据
    console.log('提交前的表单数据:', form.value)
    
    // 确保所有必要字段都存在且不为空
    if (!form.value.code_name || !form.value.code_name.trim()) {
      throw new Error('股票名称不能为空')
    }
    
    const stock = {
      code: form.value.code.trim(),
      market: form.value.market.trim(),
      code_name: form.value.code_name.trim(),
      google_name: form.value.google_code.trim(),
      currency: form.value.market === 'HK' ? 'HKD' : 'USD'
    }
    
    // 打印提交的数据，方便调试
    console.log('提交的股票数据:', stock)
    
    const url = props.editData ? `/api/stock/stocks/${props.editData.id}` : '/api/stock/stocks'
    const method = props.editData ? 'put' : 'post'
    
    const response = await axios[method](url, stock)
    
    if (response.data.success) {
      message.success(props.editData ? '股票更新成功' : '股票添加成功')
      emit('success')
      handleClose()
    } else {
      throw new Error(response.data.message || '操作失败')
    }
  } catch (error) {
    console.error('提交失败:', error)
    message.error(error.message || '操作失败，请重试')
    errors.value.code_name = error.message
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.modal {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 1055;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.modal.show {
  pointer-events: auto;
}

.modal-dialog {
  max-width: 500px;
  margin: 1.75rem auto;
  position: relative;
  width: 100%;
  z-index: 1056;
  pointer-events: auto;
}

.modal-content {
  position: relative;
  background-color: #fff;
  border-radius: 0.375rem;
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
  width: 100%;
}

.modal-header {
  padding: 1rem;
  border-bottom: 1px solid #dee2e6;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-header h5 {
  font-size: 1rem;
  margin: 0;
}

.modal-body {
  padding: 1rem;
}

.modal-footer {
  padding: 0.75rem;
  border-top: 1px solid #dee2e6;
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}

.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 1054;
}

.form-label {
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: #333;
}

.form-control,
.form-select {
  font-size: 0.875rem;
  padding: 0.5rem 0.75rem;
  border-color: #dee2e6;
  border-radius: 0.25rem;
}

.form-control:disabled {
  background-color: #f8f9fa;
  cursor: not-allowed;
}

.form-control::placeholder {
  color: #adb5bd;
  font-size: 0.875rem;
}

.invalid-feedback {
  font-size: 0.75rem;
  color: #dc3545;
  margin-top: 0.25rem;
}

.btn {
  font-size: 0.875rem;
  padding: 0.5rem 1rem;
  border-radius: 0.25rem;
}

.btn-close {
  padding: 0.5rem;
  margin: -0.5rem -0.5rem -0.5rem auto;
  font-size: 1rem;
}

.mb-3 {
  margin-bottom: 1rem;
}

.text-danger {
  color: #dc3545 !important;
}

.text-primary {
  color: #0d6efd !important;
}
</style> 