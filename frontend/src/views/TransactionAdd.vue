<template>
  <div class="card" v-permission="'transaction:records:add'">
    <div class="card-header">
      <h5 class="mb-0" data-testid="transaction-add-title">添加交易记录</h5>
    </div>
    
    <div class="card-body">
      <!-- 基本信息 -->
      <div class="row mb-4">
        <div class="col-md-4">
          <label class="form-label" data-testid="transaction-date-label">交易日期</label>
          <div class="date-input">
            <input
              type="text"
              class="form-control"
              v-model="form.transaction_date"
              @blur="handleDateBlur"
              @keydown="handleKeyNavigation($event, 'transaction_date')"
              :class="{ 'is-invalid': errors.transaction_date }"
              placeholder="YYYY-MM-DD"
              :ref="el => inputRefs.transaction_date.value = el"
              data-testid="transaction-date-input"
            />
            <div class="invalid-feedback" data-testid="transaction-date-error">{{ errors.transaction_date }}</div>
          </div>
        </div>

        <div class="col-md-4">
          <label class="form-label" data-testid="stock-code-label">股票代码</label>
          <div class="position-relative">
            <div class="stock-input-wrapper">
              <input
                type="text"
                class="form-control"
                v-model="form.stock_code"
                :ref="el => inputRefs.stock_code.value = el"
                @input="handleStockCodeInput"
                @blur="handleStockCodeBlur"
                @focus="handleStockCodeFocus"
                @keydown="handleKeyNavigation($event, 'stock_code')"
                @keydown.down.prevent="navigateStockList('down')"
                @keydown.up.prevent="navigateStockList('up')"
                @keydown.enter.prevent="handleStockSelect"
                @keydown.esc="closeStockList"
                :class="{ 'is-invalid': errors.stock_code }"
                placeholder="输入代码或名称搜索"
                data-testid="stock-code-input"
              />
              <span v-if="form.stock_code && form.stock_name" class="selected-stock" data-testid="selected-stock-info">
                <span :class="['market-tag', form.market === 'HK' ? 'hk' : 'usa']" data-testid="selected-stock-market">{{ form.market }}</span>
                {{ form.stock_code }} {{ form.stock_name }}
              </span>
            </div>
            <div class="invalid-feedback" data-testid="stock-code-error">{{ errors.stock_code }}</div>
            
            <!-- 股票搜索结果下拉列表 -->
            <div v-if="showStockList && filteredStocks.length > 0" class="stock-list" data-testid="stock-search-list">
              <a
                v-for="(stock, index) in filteredStocks"
                :key="stock.code"
                href="#"
                class="stock-item"
                :class="{ 'active': index === currentStockIndex }"
                @click.prevent="selectStock(stock)"
                @mouseover="currentStockIndex = index"
                :data-testid="'stock-item-' + stock.code"
              >
                <span :class="['market-tag', stock.market === 'HK' ? 'hk' : 'usa']">{{ stock.market }}</span>
                {{ stock.code }} - {{ stock.name }}
              </a>
            </div>
          </div>
        </div>

        <div class="col-md-4">
          <label class="form-label" data-testid="transaction-code-label">交易编号</label>
          <input
            type="text"
            class="form-control"
            v-model="form.transaction_code"
            :ref="el => inputRefs.transaction_code.value = el"
            @input="handleTransactionCodeInput"
            @blur="handleTransactionCodeBlur"
            @keydown="handleKeyNavigation($event, 'transaction_code')"
            :class="{ 'is-invalid': errors.transaction_code }"
            data-testid="transaction-code-input"
          />
          <div class="invalid-feedback" data-testid="transaction-code-error">{{ errors.transaction_code }}</div>
        </div>
      </div>

      <div class="row mb-4">
        <div class="col-md-4">
          <label class="form-label" data-testid="transaction-type-label">交易类型</label>
          <input
            type="text"
            class="form-control"
            v-model="form.transaction_type"
            :ref="el => inputRefs.transaction_type.value = el"
            @keydown="handleKeyNavigation($event, 'transaction_type')"
            :class="{ 'is-invalid': errors.transaction_type }"
            placeholder="P-买入 S-卖出"
            data-testid="transaction-type-input"
          />
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
            :ref="el => inputRefs.addDetailBtn.value = el"
            data-testid="add-detail-button"
          >
            添加成交记录
          </button>
        </div>

        <div class="border rounded p-3" data-testid="transaction-details-container">
          <div v-for="(detail, index) in form.details" :key="index" class="row g-2 mb-2" :data-testid="'detail-row-' + index">
            <div class="col-md-5">
              <label class="form-label" :data-testid="'quantity-label-' + index">数量</label>
              <input
                type="text"
                class="form-control"
                v-model="detail.quantity"
                :ref="el => setQuantityRef(el, index)"
                @keydown="handleKeyNavigation($event, `quantity_${index}`)"
                :data-testid="'quantity-input-' + index"
              />
            </div>

            <div class="col-md-5">
              <label class="form-label" :data-testid="'price-label-' + index">价格</label>
              <input
                type="text"
                class="form-control"
                v-model="detail.price"
                :ref="el => setPriceRef(el, index)"
                @keydown="handleKeyNavigation($event, `price_${index}`)"
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
                :data-testid="'remove-detail-button-' + index"
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
                type="text"
                class="form-control"
                v-model="form.broker_fee"
                :ref="el => inputRefs.broker_fee.value = el"
                @keydown="handleKeyNavigation($event, 'broker_fee')"
                data-testid="broker-fee-input"
              />
            </div>

            <div class="col-md-4">
              <label class="form-label" data-testid="transaction-levy-label">交易征费</label>
              <input
                type="text"
                class="form-control"
                v-model="form.transaction_levy"
                :ref="el => inputRefs.transaction_levy.value = el"
                @keydown="handleKeyNavigation($event, 'transaction_levy')"
                data-testid="transaction-levy-input"
              />
            </div>

            <div class="col-md-4">
              <label class="form-label" data-testid="stamp-duty-label">印花税</label>
              <input
                type="text"
                class="form-control"
                v-model="form.stamp_duty"
                :ref="el => inputRefs.stamp_duty.value = el"
                @keydown="handleKeyNavigation($event, 'stamp_duty')"
                data-testid="stamp-duty-input"
              />
            </div>

            <div class="col-md-4">
              <label class="form-label" data-testid="trading-fee-label">交易费</label>
              <input
                type="text"
                class="form-control"
                v-model="form.trading_fee"
                :ref="el => inputRefs.trading_fee.value = el"
                @keydown="handleKeyNavigation($event, 'trading_fee')"
                data-testid="trading-fee-input"
              />
            </div>

            <div class="col-md-4">
              <label class="form-label" data-testid="deposit-fee-label">存入证券费</label>
              <input
                type="text"
                class="form-control"
                v-model="form.deposit_fee"
                :ref="el => inputRefs.deposit_fee.value = el"
                @keydown="handleKeyNavigation($event, 'deposit_fee')"
                data-testid="deposit-fee-input"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- 按钮组 -->
      <div class="d-flex justify-content-end gap-2">
        <button 
          type="button" 
          class="btn btn-secondary" 
          @click="$router.back()"
          :ref="el => inputRefs.cancelBtn.value = el"
          data-testid="cancel-button"
        >
          取消
        </button>
        <button 
          type="button"
          class="btn btn-primary" 
          :disabled="submitting"
          :ref="el => inputRefs.saveBtn.value = el"
          @click="submitForm"
          data-testid="save-button"
        >
          <span v-if="submitting" class="spinner-border spinner-border-sm me-1"></span>
          保存
        </button>
        <button 
          type="button" 
          class="btn btn-success" 
          :disabled="submitting" 
          @click="saveAndAdd"
          :ref="el => inputRefs.saveAndAddBtn.value = el"
          data-testid="save-and-add-button"
        >
          <span v-if="submitting" class="spinner-border spinner-border-sm me-1"></span>
          保存并添加下一条
        </button>
      </div>
    </div>

    <!-- 添加股票对话框 -->
    <div class="modal fade" id="addStockModal" tabindex="-1" ref="addStockModal" data-testid="add-stock-modal">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" data-testid="add-stock-modal-title">添加新股票</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" data-testid="add-stock-modal-close"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="submitNewStock">
              <div class="mb-3">
                <label class="form-label" data-testid="new-stock-code-label">股票代码</label>
                <input 
                  type="text" 
                  class="form-control" 
                  v-model="newStock.code"
                  :class="{ 'is-invalid': errors.code }"
                  placeholder="输入股票代码后将自动查询股票信息"
                  @keydown.enter.prevent="handleNewStockCodeEnter"
                  @keydown.tab.prevent="handleNewStockCodeEnter"
                  data-testid="new-stock-code-input"
                />
                <div class="invalid-feedback" data-testid="new-stock-code-error">{{ errors.code }}</div>
              </div>

              <div class="mb-3">
                <label class="form-label" data-testid="new-stock-market-label">市场</label>
                <input 
                  type="text" 
                  class="form-control" 
                  v-model="newStock.market"
                  :class="{ 'is-invalid': errors.market }"
                  readonly
                  data-testid="new-stock-market-input"
                />
                <div class="invalid-feedback" data-testid="new-stock-market-error">{{ errors.market }}</div>
              </div>

              <div class="mb-3">
                <label class="form-label" data-testid="new-stock-name-label">股票名称</label>
                <input 
                  type="text" 
                  class="form-control" 
                  v-model="newStock.name"
                  :class="{ 'is-invalid': errors.name }"
                  readonly
                  data-testid="new-stock-name-input"
                />
                <div class="invalid-feedback" data-testid="new-stock-name-error">{{ errors.name }}</div>
              </div>

              <div class="mb-3">
                <label class="form-label" data-testid="new-stock-google-code-label">谷歌查询代码</label>
                <input 
                  type="text" 
                  class="form-control" 
                  v-model="newStock.google_code"
                  readonly
                  data-testid="new-stock-google-code-input"
                />
              </div>

              <div class="mb-3">
                <label class="form-label" data-testid="new-stock-price-label">当前股价</label>
                <input 
                  type="text" 
                  class="form-control" 
                  :value="newStock.current_price"
                  readonly
                  data-testid="new-stock-price-input"
                />
                <div v-if="newStock.alertMessage" :class="{ 
                    'text-danger': newStock.alertMessage.includes('已存在'), 
                    'text-primary': newStock.alertMessage.includes('查询失败')
                  }" data-testid="new-stock-alert-message">
                  {{ newStock.alertMessage }}
                </div>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" data-testid="add-stock-modal-cancel">取消</button>
            <button type="button" class="btn btn-primary" @click="submitNewStock" :disabled="submittingStock" data-testid="add-stock-modal-submit">
              <span v-if="submittingStock" class="spinner-border spinner-border-sm me-1"></span>
              确认添加
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import StockSelector from '../components/StockSelector.vue'
import axios from 'axios'
import { useMessage } from '../composables/useMessage'
import { debounce } from 'lodash'
import { Modal } from 'bootstrap'

const router = useRouter()
const message = useMessage()
const submitting = ref(false)
const saveAndAddNext = ref(false)

// 表单数据
const form = ref({
  transaction_date: '',
  stock_code: '',
  stock_name: '',
  transaction_code: '',
  transaction_type: '',
  details: [{ quantity: null, price: null }],
  broker_fee: '',
  transaction_levy: '',
  stamp_duty: '',
  trading_fee: '',
  deposit_fee: '',
  market: 'HK'
})

// 添加标记来跟踪股票是否已被选择
const stockSelected = ref(false)

// 错误信息
const errors = ref({})

// 修改 refs 对象的定义方式
const inputRefs = {
  transaction_date: ref(null),
  stock_code: ref(null),
  transaction_code: ref(null),
  transaction_type: ref(null),
  broker_fee: ref(null),
  transaction_levy: ref(null),
  stamp_duty: ref(null),
  trading_fee: ref(null),
  deposit_fee: ref(null),
  cancelBtn: ref(null),
  saveBtn: ref(null),
  saveAndAddBtn: ref(null),
  addDetailBtn: ref(null),
  quantityRefs: [],
  priceRefs: []
}

// 股票搜索相关
const showStockList = ref(false)
const filteredStocks = ref([])
const currentStockIndex = ref(-1)

// 新增股票相关的状态
const addStockModal = ref(null)
const newStock = ref({
  market: 'HK',
  code: '',
  name: '',
  full_name: '',
  current_price: null,
  alertMessage: ''
})
const submittingStock = ref(false)

// 方法
const addDetail = () => {
  form.value.details.push({ quantity: null, price: null })
}

const removeDetail = (index) => {
  if (form.value.details.length > 1) {
    form.value.details.splice(index, 1)
  }
}

// 添加日期验证函数
const isValidDate = (dateString) => {
  const date = new Date(dateString)
  return date instanceof Date && !isNaN(date)
}

// 日期格式化函数
const formatDate = (date) => {
  const d = new Date(date)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// 修改日期处理相关代码
const handleDateInput = (event) => {
  const value = event.target.value
  form.value.transaction_date = value
}

const handleDateBlur = (event) => {
  const input = event.target.value.trim()
  if (!input) {
    form.value.transaction_date = ''
    return
  }

  let formattedDate = null

  // 处理简单数字输入
  if (/^\d{1,2}$/.test(input)) {
    // 如果输入1-31的数字，自动补充为当前年月
    const day = input.padStart(2, '0')
    const today = new Date()
    const year = today.getFullYear()
    const month = (today.getMonth() + 1).toString().padStart(2, '0')
    formattedDate = `${year}-${month}-${day}`
  } else if (/^\d{1,2}-\d{1,2}$/.test(input)) {
    // 如果输入月-日格式，自动补充年份
    const [month, day] = input.split('-').map(num => num.padStart(2, '0'))
    const year = new Date().getFullYear()
    formattedDate = `${year}-${month}-${day}`
  } else if (/^\d{1,2}-\d{1,2}-\d{2}$/.test(input)) {
    // 如果输入月-日-年格式（两位年份），自动补充为20xx
    const [month, day, shortYear] = input.split('-').map(num => num.padStart(2, '0'))
    formattedDate = `20${shortYear}-${month}-${day}`
  } else {
    // 尝试解析标准日期格式
    const date = new Date(input)
    if (isValidDate(date)) {
      formattedDate = formatDate(date)
    }
  }

  if (formattedDate && isValidDate(formattedDate)) {
    form.value.transaction_date = formattedDate
    delete errors.value.transaction_date
  } else {
    errors.value.transaction_date = '请输入有效的交易日期'
  }
}

// 表单验证
const validateForm = () => {
  errors.value = {}
  let isValid = true

  if (!form.value.transaction_date || !isValidDate(form.value.transaction_date)) {
    errors.value.transaction_date = '请输入有效的交易日期'
    isValid = false
  }

  if (!form.value.stock_code) {
    errors.value.stock_code = '请选择股票'
    isValid = false
  }

  if (!form.value.transaction_code) {
    errors.value.transaction_code = '请输入交易编号'
    isValid = false
  }

  if (!form.value.transaction_type) {
    errors.value.transaction_type = '请选择交易类型'
    isValid = false
  }

  form.value.details.forEach((detail, index) => {
    const price = parseFloat(detail.price)
    if (isNaN(price) || price <= 0) {
      errors.value[`price_${index}`] = '请输入有效的价格'
      isValid = false
    }
    
    const quantity = parseFloat(detail.quantity)
    if (isNaN(quantity) || quantity <= 0) {
      errors.value[`quantity_${index}`] = '请输入有效的数量'
      isValid = false
    }
  })

  return isValid
}

// 监听交易类型变化，但不自动计算印花税
watch(() => form.value.transaction_type, () => {
  if (form.value.transaction_type === 'buy') {
    form.value.stamp_duty = ''
  }
})

// 处理交易编号输入
const handleTransactionCodeInput = (event) => {
  const code = event.target.value.toUpperCase()
  form.value.transaction_code = code
  
  // 根据交易编号自动判断买卖类型
  if (code.startsWith('P')) {
    form.value.transaction_type = 'buy'
  } else if (code.startsWith('S')) {
    form.value.transaction_type = 'sell'
  }
}

// 添加交易编号失去焦点事件处理
const handleTransactionCodeBlur = async (event) => {
  const code = form.value.transaction_code.trim()
  if (!code) return

  try {
    const response = await axios.get(`/api/stock/transactions/check-code?code=${encodeURIComponent(code)}`)
    if (response.data.exists) {
      errors.value.transaction_code = '交易编号已存在，请重新输入'
      // 保持焦点在输入框
      event.target.focus()
    } else {
      delete errors.value.transaction_code
    }
  } catch (error) {
    console.error('检查交易编号失败:', error)
    message.error('检查交易编号失败，请重试')
  }
}

// 处理股票选择
const handleStockSelect = () => {
  if (showStockList.value && filteredStocks.value.length > 0) {
    const selectedStock = currentStockIndex.value >= 0 && currentStockIndex.value < filteredStocks.value.length
      ? filteredStocks.value[currentStockIndex.value]
      : filteredStocks.value[0]
    selectStock(selectedStock)
  }
}

// 选择股票
const selectStock = (stock) => {
  if (stock && stock.code) {
    // 再次验证股票是否存在
    axios.get(`/api/stock/stocks/search?query=${encodeURIComponent(stock.code)}`)
      .then(response => {
        if (response.data.success && response.data.data.length > 0) {
          const foundStock = response.data.data.find(s => s.code === stock.code)
          if (foundStock) {
            form.value.stock_code = foundStock.code
            form.value.stock_name = foundStock.name || ''
            form.value.market = foundStock.market || 'HK'
            stockSelected.value = true
          } else {
            message.warning('该股票可能已被删除，请重新选择')
            form.value.stock_code = ''
            form.value.stock_name = ''
            stockSelected.value = false
          }
        }
      })
      .catch(error => {
        console.error('验证股票失败:', error)
        message.error('验证股票失败，请重新选择')
      })
  }
  
  setTimeout(() => {
    showStockList.value = false
    filteredStocks.value = []
    currentStockIndex.value = -1
  }, 100)
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
    
    const submitData = {
      transaction_date: form.value.transaction_date,
      stock_code: form.value.stock_code,
      market: form.value.market,
      transaction_type: form.value.transaction_type.toLowerCase(),
      transaction_code: form.value.transaction_code,
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
    }
    
    console.log('提交的交易数据:', submitData)
    console.log('表单原始数据:', form.value)
    
    const response = await axios.post('/api/stock/transactions', submitData)

    if (response.data.success) {
      if (saveAndAddNext.value) {
        resetForm()
        saveAndAddNext.value = false
        message.success('交易记录添加成功')
        // 等待 DOM 更新后再设置焦点
        await nextTick()
        if (inputRefs.transaction_date.value) {
          inputRefs.transaction_date.value.focus()
        }
      } else {
        message.success('交易记录添加成功')
        router.push('/transactions')
      }
    } else {
      throw new Error(response.data.message || '操作失败')
    }
  } catch (error) {
    message.error(error.response?.data?.message || error.message || '操作失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

// 保存并继续添加
const saveAndAdd = () => {
  saveAndAddNext.value = true
  submitForm()
}

// 重置表单
const resetForm = () => {
  form.value = {
    transaction_date: '',
    stock_code: '',
    stock_name: '',
    transaction_code: '',
    transaction_type: '',
    details: [{ quantity: null, price: null }],
    broker_fee: '',
    transaction_levy: '',
    stamp_duty: '',
    trading_fee: '',
    deposit_fee: '',
    market: 'HK'
  }
  errors.value = {}
  stockSelected.value = false
}

// 在组件挂载后检查所有ref
onMounted(() => {
  nextTick(() => {
    console.log("检查所有输入框的 ref 是否绑定成功:", {
      transaction_date: inputRefs.transaction_date.value,
      stock_code: inputRefs.stock_code.value,
      transaction_code: inputRefs.transaction_code.value,
      transaction_type: inputRefs.transaction_type.value,
      broker_fee: inputRefs.broker_fee.value,
      transaction_levy: inputRefs.transaction_levy.value,
      stamp_duty: inputRefs.stamp_duty.value,
      trading_fee: inputRefs.trading_fee.value,
      deposit_fee: inputRefs.deposit_fee.value,
      cancelBtn: inputRefs.cancelBtn.value,
      saveBtn: inputRefs.saveBtn.value,
      saveAndAddBtn: inputRefs.saveAndAddBtn.value,
      addDetailBtn: inputRefs.addDetailBtn.value,
      quantityRefs: inputRefs.quantityRefs,
      priceRefs: inputRefs.priceRefs,
    });

    // 检查动态数组的长度是否匹配
    console.log("动态数组长度检查:", {
      details_length: form.value.details.length,
      quantityRefs_length: inputRefs.quantityRefs.length,
      priceRefs_length: inputRefs.priceRefs.length,
    });

    // 检查所有可聚焦元素的顺序
    const focusableElements = document.querySelectorAll(
      'input:not([disabled]), button:not([disabled])'
    );
    console.log("可聚焦元素数量:", focusableElements.length);
    
    // 检查每个动态行的ref
    form.value.details.forEach((_, index) => {
      console.log(`第 ${index + 1} 行明细的ref:`, {
        quantity: inputRefs.quantityRefs[index],
        price: inputRefs.priceRefs[index],
      });
    });
  });

  document.addEventListener('click', handleClickOutside)

  // 添加对话框关闭时的处理
  addStockModal.value?.addEventListener('hidden.bs.modal', () => {
    newStock.value = {
      market: 'HK',
      code: '',
      name: '',
      full_name: '',
      current_price: null,
      alertMessage: ''
    }
  })
});

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})

// 修改动态ref的处理
const setQuantityRef = (el, index) => {
  if (!inputRefs.quantityRefs) {
    inputRefs.quantityRefs = []
  }
  // 确保数组长度足够
  while (inputRefs.quantityRefs.length <= index) {
    inputRefs.quantityRefs.push(null)
  }
  inputRefs.quantityRefs[index] = el
}

const setPriceRef = (el, index) => {
  if (!inputRefs.priceRefs) {
    inputRefs.priceRefs = []
  }
  // 确保数组长度足够
  while (inputRefs.priceRefs.length <= index) {
    inputRefs.priceRefs.push(null)
  }
  inputRefs.priceRefs[index] = el
}

// 监听明细数量变化，更新refs数组
watch(() => form.value.details.length, (newLength) => {
  nextTick(() => {
    // 重置refs数组
    if (!inputRefs.quantityRefs) {
      inputRefs.quantityRefs = []
    }
    if (!inputRefs.priceRefs) {
      inputRefs.priceRefs = []
    }
    
    // 调整数组长度
    inputRefs.quantityRefs.length = newLength
    inputRefs.priceRefs.length = newLength
    
    // 初始化新的元素为 null
    for (let i = 0; i < newLength; i++) {
      if (!inputRefs.quantityRefs[i]) {
        inputRefs.quantityRefs[i] = null
      }
      if (!inputRefs.priceRefs[i]) {
        inputRefs.priceRefs[i] = null
      }
    }
  })
})

// 键盘导航处理
const handleKeyNavigation = (event, fieldName) => {
  // Enter键导航逻辑
  if (event.key === 'Enter') {
    event.preventDefault();
    
    // 处理动态字段的导航
    if (fieldName.startsWith('quantity_')) {
      const index = parseInt(fieldName.split('_')[1]);
      const priceInput = inputRefs.priceRefs[index];
      if (priceInput) {
        priceInput.focus();
      }
      return;
    }
    
    if (fieldName.startsWith('price_')) {
      // 如果是最后一行的价格，跳转到经纪佣金
      const index = parseInt(fieldName.split('_')[1]);
      if (index === form.value.details.length - 1) {
        const brokerFeeInput = inputRefs.broker_fee.value;
        if (brokerFeeInput) {
          brokerFeeInput.focus();
        }
      }
      return;
    }

    // Enter键特定导航映射
    const enterKeyMap = {
      'transaction_date': () => inputRefs.stock_code.value?.focus(),
      'stock_code': () => inputRefs.transaction_code.value?.focus(),
      'transaction_code': () => {
        const firstQuantityInput = inputRefs.quantityRefs[0];
        if (firstQuantityInput) {
          firstQuantityInput.focus();
        }
      },
      'broker_fee': () => inputRefs.transaction_levy.value?.focus(),
      'transaction_levy': () => inputRefs.stamp_duty.value?.focus(),
      'stamp_duty': () => inputRefs.trading_fee.value?.focus(),
      'trading_fee': () => inputRefs.deposit_fee.value?.focus(),
      'deposit_fee': () => {
        const saveAndAddBtn = inputRefs.saveAndAddBtn.value;
        if (saveAndAddBtn) {
          saveAndAddBtn.click();
        }
      }
    };

    // 执行Enter键导航
    const handler = enterKeyMap[fieldName];
    if (handler) {
      handler();
    }
  }

  // Tab键导航逻辑
  if (event.key === 'Tab') {
    event.preventDefault();
    
    // 处理动态字段的Tab导航
    if (fieldName.startsWith('quantity_')) {
      const index = parseInt(fieldName.split('_')[1]);
      const priceInput = inputRefs.priceRefs[index];
      if (priceInput) {
        priceInput.focus();
      }
      return;
    }
    
    if (fieldName.startsWith('price_')) {
      // 点击添加按钮并聚焦到新行
      addDetail();
      nextTick(() => {
        const newIndex = form.value.details.length - 1;
        const newQuantityInput = inputRefs.quantityRefs[newIndex];
        if (newQuantityInput) {
          newQuantityInput.focus();
        }
      });
      return;
    }

    // Tab键特定导航映射
    const tabKeyMap = {
      'transaction_date': () => inputRefs.stock_code.value?.focus(),
      'stock_code': () => inputRefs.transaction_code.value?.focus(),
      'transaction_code': () => {
        const firstQuantityInput = inputRefs.quantityRefs[0];
        if (firstQuantityInput) {
          firstQuantityInput.focus();
        }
      },
      'broker_fee': () => inputRefs.transaction_levy.value?.focus(),
      'transaction_levy': () => inputRefs.stamp_duty.value?.focus(),
      'stamp_duty': () => inputRefs.trading_fee.value?.focus(),
      'trading_fee': () => inputRefs.deposit_fee.value?.focus(),
      'deposit_fee': () => inputRefs.cancelBtn.value?.focus()
    };

    // 执行Tab键导航
    const handler = tabKeyMap[fieldName];
    if (handler) {
      handler();
    }
  }
};

// 处理股票代码输入
const handleStockCodeInput = debounce(async (event) => {
  const query = event.target.value.trim()
  if (!query) {
    showStockList.value = false
    filteredStocks.value = []
    return
  }

  try {
    // 每次搜索都从服务器获取最新数据
    const response = await axios.get(`/api/stock/stocks/search?query=${encodeURIComponent(query)}`, {
      params: {
        timestamp: new Date().getTime() // 添加时间戳防止缓存
      }
    })
    
    if (response.data.success && Array.isArray(response.data.data)) {
      filteredStocks.value = response.data.data
      showStockList.value = filteredStocks.value.length > 0
      currentStockIndex.value = -1
      
      // 如果没有找到股票，显示提示信息
      if (filteredStocks.value.length === 0) {
        message.info('未找到匹配的股票')
      }
    } else {
      filteredStocks.value = []
      showStockList.value = false
      message.warning('获取股票列表失败')
    }
  } catch (error) {
    console.error('搜索股票失败:', error)
    filteredStocks.value = []
    showStockList.value = false
    message.error('搜索股票失败，请重试')
  }
}, 300)

// 导航股票列表
const navigateStockList = (direction) => {
  if (!showStockList.value || filteredStocks.value.length === 0) return

  if (direction === 'up') {
    currentStockIndex.value = currentStockIndex.value <= 0 
      ? filteredStocks.value.length - 1 
      : currentStockIndex.value - 1
  } else {
    currentStockIndex.value = currentStockIndex.value >= filteredStocks.value.length - 1
      ? 0 
      : currentStockIndex.value + 1
  }
}

// 关闭股票列表
const closeStockList = () => {
  showStockList.value = false
  currentStockIndex.value = -1
}

// 点击外部关闭股票列表
const handleClickOutside = (event) => {
  if (!event.target.closest('.position-relative')) {
    closeStockList()
  }
}

// 修改股票代码失去焦点的处理函数
const handleStockCodeBlur = async (event) => {
  setTimeout(async () => {
    const code = form.value.stock_code
    if (!code) {
      stockSelected.value = false
      return
    }

    if (stockSelected.value && form.value.stock_name) {
      return
    }

    try {
      const response = await axios.get(`/api/stock/stocks/search?query=${encodeURIComponent(code)}`)
      if (response.data.success && Array.isArray(response.data.data)) {
        const exactMatch = response.data.data.find(stock => stock.code === code)
        if (exactMatch) {
          form.value.stock_code = exactMatch.code
          form.value.stock_name = exactMatch.name
          form.value.market = exactMatch.market
          stockSelected.value = true
          return
        }
      }

      const searchResponse = await axios.get(`/api/stock/search_stock?code=${encodeURIComponent(code)}`)
      if (searchResponse.data.success && searchResponse.data.data.length > 0) {
        const stockData = searchResponse.data.data[0]
        
        newStock.value = {
          market: stockData.market === 'HK' || stockData.exchange === 'HKG' ? 'HK' : 'USA',
          code: stockData.code,
          name: stockData.code_name || '',
          google_code: stockData.query,
          current_price: stockData.price,
          alertMessage: ''
        }
        
        const modal = new Modal(addStockModal.value)
        modal.show()
      } else {
        newStock.value = {
          market: 'HK',
          code: code,
          name: '',
          google_code: '',
          current_price: null,
          alertMessage: '未找到股票信息，请手动输入股票详情'
        }
        const modal = new Modal(addStockModal.value)
        modal.show()
      }
    } catch (error) {
      console.error('搜索股票失败:', error)
      newStock.value = {
        market: 'HK',
        code: code,
        name: '',
        google_code: '',
        current_price: null,
        alertMessage: '搜索股票失败，请手动输入股票详情'
      }
      const modal = new Modal(addStockModal.value)
      modal.show()
    }
  }, 200)
}

// 监听股票代码变化
watch(() => form.value.stock_code, (newCode) => {
  if (!newCode) {
    form.value.stock_name = ''
    form.value.market = 'HK'
    stockSelected.value = false
  }
})

// 处理股票代码回车和Tab事件
const handleNewStockCodeEnter = async (event) => {
  event.preventDefault()
  if (!newStock.value.code) {
    return
  }
  
  errors.value = {}
  newStock.value.alertMessage = ''
  
  try {
    // 直接使用原始输入查询股票信息，不做任何处理
    const response = await axios.get(`/api/stock/search_stock?code=${encodeURIComponent(newStock.value.code)}`)
    
    if (response.data.success && response.data.data.length > 0) {
      const stockData = response.data.data[0]
      
      // 检查是否已存在
      const checkResponse = await axios.get('/api/stock/stocks', {
        params: {
          search: stockData.code
        }
      })
      
      if (checkResponse.data.success && checkResponse.data.data.items.length > 0) {
        const existingStock = checkResponse.data.data.items.find(
          stock => stock.code === stockData.code
        )
        if (existingStock) {
          newStock.value = {
            ...existingStock,
            current_price: stockData.price
          }
          stockSelected.value = true
          return
        }
      }

      // 更新表单数据，保持原始代码
      newStock.value = {
        code: stockData.code,
        market: stockData.market,
        name: stockData.code_name || '',
        google_code: stockData.query,
        current_price: stockData.price
      }
      
      if (newStock.value.name) {
        stockSelected.value = true
      }
      
      if (!newStock.value.name) {
        errors.value.name = '未能获取公司名称'
      }
    } else {
      newStock.value.alertMessage = '未找到股票信息，请检查股票代码是否正确'
      resetNewStockExceptCode()
    }
  } catch (error) {
    console.error('查询股票信息失败:', error)
    newStock.value.alertMessage = '查询失败，请检查股票代码是否正确'
    resetNewStockExceptCode()
  }
}

// 重置表单（除了股票代码）
const resetNewStockExceptCode = () => {
  const currentCode = newStock.value.code
  newStock.value = {
    market: '',
    code: currentCode,
    name: '',
    google_code: '',
    current_price: null,
    alertMessage: ''
  }
  errors.value = {}
}

// 提交新股票
const submitNewStock = async () => {
  if (submittingStock.value) return

  errors.value = {}
  let isValid = true

  if (!newStock.value.code) {
    errors.value.code = '请输入股票代码'
    isValid = false
  }
  if (!newStock.value.market) {
    errors.value.market = '无法确定股票市场'
    isValid = false
  }
  if (!newStock.value.name) {
    errors.value.name = '未能获取股票名称'
    isValid = false
  }
  if (!newStock.value.current_price) {
    errors.value.code = '未能获取股票价格，请确认股票代码是否正确'
    isValid = false
  }

  if (!isValid) return
  
  try {
    submittingStock.value = true
    
    // 检查股票是否已存在，使用原始代码
    const checkResponse = await axios.get('/api/stock/stocks', {
      params: {
        search: newStock.value.code
      }
    })
    
    if (checkResponse.data.success && checkResponse.data.data.items.length > 0) {
      const existingStock = checkResponse.data.data.items.find(
        stock => stock.code === newStock.value.code
      )
      if (existingStock) {
        message.warning('该股票代码已存在')
        newStock.value.current_price = null
        submittingStock.value = false
        return
      }
    }

    // 修改提交的数据结构，确保字段名称与后端一致
    const stock = {
      code: newStock.value.code,
      market: newStock.value.market,
      code_name: newStock.value.name,  // 使用 code_name 而不是 name
      google_name: newStock.value.google_code,  // 使用 google_name 而不是 google_code
      currency: newStock.value.market === 'HK' ? 'HKD' : 'USD'
    }
    
    // 打印提交的数据，方便调试
    console.log('提交的股票数据:', stock)
    
    const response = await axios.post('/api/stock/stocks', stock)
    
    if (response.data.success) {
      message.success('股票添加成功')
      form.value.stock_code = newStock.value.code
      form.value.stock_name = newStock.value.name
      form.value.market = newStock.value.market
      
      try {
        if (addStockModal.value) {
          const modal = Modal.getInstance(addStockModal.value)
          if (modal) {
            modal.hide()
          } else {
            // 如果无法获取模态框实例，使用原生方法关闭
            addStockModal.value.classList.remove('show')
            addStockModal.value.style.display = 'none'
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
      
      newStock.value = {
        market: 'HK',
        code: '',
        name: '',
        full_name: '',
        current_price: null,
        alertMessage: ''
      }
    } else {
      message.error(response.data.message || '添加股票失败')
      newStock.value.current_price = null
    }
  } catch (error) {
    message.error(error.response?.data?.message || error.message || '添加股票失败，请重试')
    newStock.value.current_price = null
  } finally {
    submittingStock.value = false
  }
}

const handleStockCodeFocus = () => {
  form.value.stock_code = ''
}
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

.card-header h5 {
  font-size: 1rem;
}

.card-body {
  padding: 1rem;
}

.form-label {
  font-weight: 500;
  color: #333;
  margin-bottom: 0.25rem;
  font-size: 0.875rem;
}

.input-group-text {
  background-color: #f8f9fa;
  min-width: 80px;
  border-color: #dee2e6;
  color: #495057;
  font-size: 0.875rem;
  padding: 0.25rem 0.5rem;
}

.form-control,
.form-select {
  border-color: #dee2e6;
  padding: 0.25rem 0.5rem;
  height: calc(2rem + 2px);
  font-size: 0.875rem;
}

.form-control:focus,
.form-select:focus {
  border-color: #80bdff;
  box-shadow: 0 0 0 0.15rem rgba(0, 123, 255, 0.25);
}

.border {
  border-color: #dee2e6 !important;
}

.rounded {
  border-radius: 0.25rem !important;
}

.btn {
  padding: 0.25rem 0.75rem;
  font-weight: 500;
  font-size: 0.875rem;
}

.btn-sm {
  padding: 0.2rem 0.5rem;
  font-size: 0.8125rem;
}

.btn-outline-primary {
  border-color: #dee2e6;
  color: #0d6efd;
  &:hover {
    background-color: #0d6efd;
    border-color: #0d6efd;
    color: #fff;
  }
}

.btn-outline-danger {
  padding: 0.25rem 0.5rem;
  border-color: #dc3545;
}

.invalid-feedback {
  font-size: 0.75rem;
  margin-top: 0.125rem;
}

.mb-4 {
  margin-bottom: 1rem !important;
}

.mb-2 {
  margin-bottom: 0.5rem !important;
}

.g-2 {
  --bs-gutter-x: 0.5rem;
  --bs-gutter-y: 0.5rem;
}

.g-3 {
  --bs-gutter-x: 0.75rem;
  --bs-gutter-y: 0.75rem;
}

.p-3 {
  padding: 0.75rem !important;
}

.gap-2 {
  gap: 0.5rem !important;
}

.input-group > .form-control,
.input-group > .form-select {
  height: calc(2rem + 2px);
}

.btn-outline-danger {
  height: calc(2rem + 2px);
  line-height: 1;
}

.row > [class*="col-"] {
  padding-right: calc(var(--bs-gutter-x) * 0.5);
  padding-left: calc(var(--bs-gutter-x) * 0.5);
}

/* 添加股票搜索相关样式 */
.stock-input-wrapper {
  position: relative;
}

.stock-input-wrapper input {
  padding-right: 120px;
}

.selected-stock {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 0.875rem;
  color: #666;
  max-width: 70%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  pointer-events: none;
}

.market-tag {
  display: inline-block;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 500;
  margin-right: 0.5rem;
  min-width: 40px;
  text-align: center;
}

.market-tag.hk {
  background-color: #dc3545;
  color: #fff;
}

.market-tag.usa {
  background-color: #0d6efd;
  color: #fff;
}

.stock-list {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  max-height: 200px;
  overflow-y: auto;
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 0.25rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  z-index: 1000;
  flex: 1;
}

.stock-item {
  display: block;
  padding: 0.5rem 0.75rem;
  color: #212529;
  text-decoration: none;
  border-bottom: 1px solid #dee2e6;
  cursor: pointer;
}

.stock-item:last-child {
  border-bottom: none;
}

.stock-item:hover {
  background-color: #e9ecef;
}

.stock-item.active {
  background-color: #cfd4da;
  font-weight: 500;
}

.stock-item.active:hover {
  background-color: #c0c5cb;
}

/* 添加对话框相关样式 */
.modal-body {
  padding: 1rem;
}

.modal-footer {
  padding: 0.75rem;
  border-top: 1px solid #dee2e6;
}

.form-label {
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 0.25rem;
}
</style> 