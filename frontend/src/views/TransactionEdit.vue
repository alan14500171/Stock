# 创建新的编辑页面
<template>
  <div class="card" data-testid="transaction-edit-container">
    <div class="card-header d-flex justify-content-between align-items-center">
      <h5 class="mb-0" data-testid="transaction-edit-title">编辑交易记录</h5>
      <button class="btn btn-outline-secondary btn-sm" @click="$router.back()">
        返回列表
      </button>
    </div>
    
    <div class="card-body">
      <form @submit.prevent="submitForm">
        <!-- 基本信息 -->
        <div class="row mb-4">
          <div class="col-md-3">
            <label class="form-label" data-testid="transaction-date-label">交易日期</label>
            <input
              type="date"
              class="form-control"
              v-model="form.transaction_date"
              :class="{ 'is-invalid': errors.transaction_date }"
              readonly
              disabled
              data-testid="transaction-date-input"
            />
            <div class="invalid-feedback" data-testid="transaction-date-error">{{ errors.transaction_date }}</div>
          </div>

          <div class="col-md-3">
            <label class="form-label" data-testid="stock-code-label">股票代码</label>
            <input
              type="text"
              class="form-control"
              v-model="form.stock_code"
              :class="{ 'is-invalid': errors.stock_code }"
              readonly
              disabled
              data-testid="stock-code-input"
            />
            <div class="invalid-feedback" data-testid="stock-code-error">{{ errors.stock_code }}</div>
          </div>

          <div class="col-md-3">
            <label class="form-label" data-testid="transaction-code-label">交易编号</label>
            <input
              type="text"
              class="form-control"
              v-model="form.transaction_code"
              :class="{ 'is-invalid': errors.transaction_code }"
              readonly
              disabled
              data-testid="transaction-code-input"
            />
            <div class="invalid-feedback" data-testid="transaction-code-error">{{ errors.transaction_code }}</div>
          </div>

          <div class="col-md-3">
            <label class="form-label" data-testid="transaction-type-label">买卖</label>
            <select
              class="form-select"
              v-model="form.transaction_type"
              :class="{ 'is-invalid': errors.transaction_type }"
              disabled
              data-testid="transaction-type-input"
            >
              <option value="buy">买入</option>
              <option value="sell">卖出</option>
            </select>
            <div class="invalid-feedback" data-testid="transaction-type-error">{{ errors.transaction_type }}</div>
          </div>
        </div>

        <!-- 成交明细 -->
        <div class="mb-4">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <label class="form-label mb-0" data-testid="transaction-details-label">成交明细</label>
            <button 
              type="button" 
              class="btn btn-sm btn-outline-primary" 
              @click="addDetail"
              data-testid="add-detail-btn"
            >
              添加成交记录
            </button>
          </div>

          <div class="border rounded p-3" data-testid="transaction-details-container">
            <div v-for="(detail, index) in form.details" :key="index" class="row g-2 mb-2" :data-testid="'detail-row-' + index">
              <div class="col-md-5">
                <label class="form-label" :data-testid="'quantity-label-' + index">数量</label>
                <input
                  type="number"
                  class="form-control"
                  v-model="detail.quantity"
                  :data-testid="'quantity-input-' + index"
                />
              </div>

              <div class="col-md-5">
                <label class="form-label" :data-testid="'price-label-' + index">价格</label>
                <input
                  type="number"
                  class="form-control"
                  v-model="detail.price"
                  step="0.001"
                  :class="{ 'is-invalid': errors[`price_${index}`] }"
                  :data-testid="'price-input-' + index"
                />
                <div class="invalid-feedback" :data-testid="'price-error-' + index">{{ errors[`price_${index}`] }}</div>
              </div>

              <div class="col-md-2 d-flex align-items-end">
                <button
                  type="button"
                  class="btn btn-outline-danger w-100"
                  @click="removeDetail(index)"
                  :disabled="form.details.length === 1"
                  :data-testid="'remove-detail-btn-' + index"
                >
                  删除
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 费用明细 -->
        <div class="mb-4">
          <label class="form-label" data-testid="fees-label">费用明细</label>
          <div class="border rounded p-3" data-testid="fees-container">
            <div class="row g-3">
              <div class="col-md-4">
                <label class="form-label" data-testid="broker-fee-label">经纪佣金</label>
                <input
                  type="number"
                  class="form-control"
                  v-model="form.broker_fee"
                  step="0.01"
                  data-testid="broker-fee-input"
                />
              </div>

              <div class="col-md-4">
                <label class="form-label" data-testid="transaction-levy-label">交易征费</label>
                <input
                  type="number"
                  class="form-control"
                  v-model="form.transaction_levy"
                  step="0.01"
                  data-testid="transaction-levy-input"
                />
              </div>

              <div class="col-md-4">
                <label class="form-label" data-testid="stamp-duty-label">印花税</label>
                <input
                  type="number"
                  class="form-control"
                  v-model="form.stamp_duty"
                  step="0.01"
                  data-testid="stamp-duty-input"
                />
              </div>

              <div class="col-md-4">
                <label class="form-label" data-testid="trading-fee-label">交易费</label>
                <input
                  type="number"
                  class="form-control"
                  v-model="form.trading_fee"
                  step="0.01"
                  data-testid="trading-fee-input"
                />
              </div>

              <div class="col-md-4">
                <label class="form-label" data-testid="deposit-fee-label">存入证券费</label>
                <input
                  type="number"
                  class="form-control"
                  v-model="form.deposit_fee"
                  step="0.01"
                  data-testid="deposit-fee-input"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- 按钮组 -->
        <div class="d-flex justify-content-center gap-2">
          <button 
            type="button" 
            class="btn btn-secondary" 
            @click="$router.back()"
            data-testid="cancel-btn"
          >
            取消
          </button>
          <button 
            type="submit" 
            class="btn btn-primary" 
            :disabled="submitting"
            data-testid="save-btn"
          >
            <span v-if="submitting" class="spinner-border spinner-border-sm me-1"></span>
            保存修改
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import 'bootstrap'

const router = useRouter()
const route = useRoute()
const submitting = ref(false)
const errors = ref({})

// 表单数据
const form = ref({
  transaction_date: '',
  stock_code: '',
  stock_name: '',
  transaction_code: '',
  transaction_type: '',
  details: [{ quantity: null, price: null }],
  broker_fee: 0,
  transaction_levy: 0,
  stamp_duty: 0,
  trading_fee: 0,
  deposit_fee: 0,
  market: '',
  prev_quantity: 0,
  prev_cost: 0,
  prev_avg_cost: 0,
  current_quantity: 0,
  current_cost: 0,
  current_avg_cost: 0
})

// 加载交易记录数据
const loadTransaction = async () => {
  try {
    const response = await axios.get(`/api/stock/transactions/${route.params.id}`)
    if (!response.data.success) {
      throw new Error(response.data.message || '加载交易记录失败')
    }

    const transaction = response.data.data
    if (!transaction) {
      throw new Error('交易记录不存在')
    }

    // 更新表单数据
    form.value = {
      transaction_date: transaction.transaction_date,
      stock_code: transaction.stock_code,
      stock_name: transaction.stock_name,
      transaction_code: transaction.transaction_code,
      transaction_type: transaction.transaction_type.toLowerCase(),
      details: transaction.details && transaction.details.length > 0 
        ? transaction.details 
        : [{ quantity: transaction.total_quantity, price: transaction.total_amount / transaction.total_quantity }],
      broker_fee: transaction.broker_fee || 0,
      transaction_levy: transaction.transaction_levy || 0,
      stamp_duty: transaction.stamp_duty || 0,
      trading_fee: transaction.trading_fee || 0,
      deposit_fee: transaction.deposit_fee || 0,
      market: transaction.market,
      prev_quantity: transaction.prev_quantity || 0,
      prev_cost: transaction.prev_cost || 0,
      prev_avg_cost: transaction.prev_avg_cost || 0,
      current_quantity: transaction.current_quantity || 0,
      current_cost: transaction.current_cost || 0,
      current_avg_cost: transaction.current_avg_cost || 0
    }
  } catch (error) {
    showToast(error.message || '加载交易记录失败，请稍后重试', 'danger')
    throw error
  }
}

// 表单验证
const validateForm = () => {
  try {
    errors.value = {}
    let isValid = true

    // 验证明细
    form.value.details.forEach((detail, index) => {
      if (!detail.price || detail.price <= 0) {
        errors.value[`price_${index}`] = '请输入有效的价格'
        isValid = false
      }
    })

    return isValid
  } catch (error) {
    return false
  }
}

// 提交表单
const submitForm = async () => {
  try {
    if (!validateForm() || submitting.value) return

    submitting.value = true
    
    // 计算总数量和总金额
    const totalQuantity = form.value.details.reduce((sum, detail) => {
      const quantity = parseFloat(detail.quantity) || 0
      return sum + quantity
    }, 0)
    
    const totalAmount = form.value.details.reduce((sum, detail) => {
      const quantity = parseFloat(detail.quantity) || 0
      const price = parseFloat(detail.price) || 0
      return sum + (quantity * price)
    }, 0)
    
    console.log('提交交易数据:', {
      总数量: totalQuantity,
      总金额: totalAmount,
      明细: form.value.details
    })
    
    const submitData = {
      transaction_date: form.value.transaction_date,
      stock_code: form.value.stock_code,
      transaction_code: form.value.transaction_code,
      transaction_type: form.value.transaction_type.toLowerCase(),
      details: form.value.details.map(d => ({
        quantity: parseFloat(d.quantity) || 0,
        price: parseFloat(d.price) || 0
      })),
      total_quantity: totalQuantity,
      total_amount: totalAmount,
      broker_fee: parseFloat(form.value.broker_fee) || 0,
      transaction_levy: parseFloat(form.value.transaction_levy) || 0,
      stamp_duty: parseFloat(form.value.stamp_duty) || 0,
      trading_fee: parseFloat(form.value.trading_fee) || 0,
      deposit_fee: parseFloat(form.value.deposit_fee) || 0,
      market: form.value.market
    }
    
    const response = await axios.put(`/api/stock/transactions/${route.params.id}`, submitData)

    if (response.data.success) {
      showToast('交易记录更新成功', 'success')
      router.back()
    } else {
      throw new Error(response.data.message || '操作失败')
    }
  } catch (error) {
    showToast(error.response?.data?.message || error.message || '更新失败，请稍后重试', 'danger')
    console.error('更新交易记录失败:', error.response?.data || error)
  } finally {
    submitting.value = false
  }
}

// 添加明细
const addDetail = () => {
  form.value.details.push({ quantity: null, price: null })
}

// 删除明细
const removeDetail = (index) => {
  if (form.value.details.length > 1) {
    form.value.details.splice(index, 1)
  }
}

// Toast 提示
const showToast = (message, type = 'danger') => {
  const toastContainer = document.getElementById('toast-container') || (() => {
    const container = document.createElement('div')
    container.id = 'toast-container'
    container.className = 'position-fixed top-0 end-0 p-3'
    container.style.zIndex = '1050'
    document.body.appendChild(container)
    return container
  })()

  const toastElement = document.createElement('div')
  toastElement.className = `toast align-items-center text-white bg-${type} border-0`
  toastElement.setAttribute('role', 'alert')
  toastElement.setAttribute('aria-live', 'assertive')
  toastElement.setAttribute('aria-atomic', 'true')
  
  toastElement.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">
        ${message}
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
    </div>
  `
  
  toastContainer.appendChild(toastElement)
  const toast = new bootstrap.Toast(toastElement)
  toast.show()
  
  toastElement.addEventListener('hidden.bs.toast', () => {
    toastElement.remove()
  })
}

// 监听交易类型变化
watch(() => form.value.transaction_type, (newType) => {
  if (newType === 'buy') {
    form.value.stamp_duty = 0
  }
})

// 组件挂载时加载数据
onMounted(async () => {
  try {
    await loadTransaction()
  } catch (error) {
    showToast('加载交易记录失败，请稍后重试', 'danger')
  }
})
</script>

<style scoped>
.card {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: none;
  max-width: 1000px;
  margin: 0 auto;
}

.card-header {
  background-color: #fff;
  border-bottom: 1px solid #dee2e6;
  padding: 0.75rem 1rem;
}

.card-body {
  padding: 1rem;
}

.form-label {
  font-weight: 500;
  color: #333;
  font-size: 0.875rem;
}

.input-group-text {
  background-color: #f8f9fa;
  min-width: 80px;
  border-color: #dee2e6;
  color: #495057;
  font-size: 0.875rem;
}

.form-control,
.form-select {
  border-color: #dee2e6;
  font-size: 0.875rem;
}

.btn {
  font-weight: 500;
  font-size: 0.875rem;
}

.invalid-feedback {
  font-size: 0.75rem;
}

.border {
  border-color: #dee2e6 !important;
}

.btn-outline-danger {
  height: calc(2rem + 2px);
  line-height: 1;
}

.form-control:disabled,
.form-select:disabled {
  background-color: #f8f9fa;
  opacity: 1;
  cursor: not-allowed;
}

.form-control[readonly],
.form-select[readonly] {
  background-color: #f8f9fa;
  opacity: 1;
}
</style> 