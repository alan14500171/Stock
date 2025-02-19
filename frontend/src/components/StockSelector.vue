<template>
  <div class="stock-selector">
    <div class="dropdown w-100">
      <button class="btn btn-outline-secondary dropdown-toggle w-100 text-start" 
              type="button" 
              :id="dropdownId" 
              data-bs-toggle="dropdown" 
              aria-expanded="false"
              :title="buttonTitle">
        {{ buttonLabel }}
      </button>
      <ul class="dropdown-menu w-100 p-2" :aria-labelledby="dropdownId">
        <li class="px-2">
          <input type="text" 
                 class="form-control form-control-sm" 
                 v-model="searchText"
                 placeholder="搜索股票..."
                 @click.stop>
        </li>
        <hr class="my-1">
        <li>
          <label class="dropdown-item">
            <input type="checkbox" 
                   class="form-check-input" 
                   v-model="selectAll"
                   @change="handleSelectAll"> 全选
          </label>
        </li>
        <hr class="my-1">
        <div class="stock-list">
          <li v-for="stock in filteredStocks" :key="stock.code">
            <label class="dropdown-item">
              <input type="checkbox" 
                     class="form-check-input stock-checkbox" 
                     :value="stock.code"
                     v-model="selectedCodes"
                     :data-market="stock.market"
                     @change="handleStockSelect">
              {{ stock.code }} {{ stock.name ? `(${stock.name})` : '' }}
            </label>
          </li>
          <li v-if="filteredStocks.length === 0" class="text-center text-muted py-2">
            未找到匹配的股票
          </li>
        </div>
      </ul>
      <input type="hidden" :name="hiddenInputName" :value="selectedCodes.join(',')">
    </div>
    <div class="selected-stocks mt-2 small">
      <span v-for="code in selectedCodes" 
            :key="code" 
            class="badge bg-light text-dark me-1 mb-1">
        {{ getStockLabel(code) }}
        <button type="button" 
                class="btn-close ms-1" 
                @click="removeStock(code)"
                aria-label="Remove"></button>
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  stocks: {
    type: Array,
    default: () => []
  },
  modelValue: {
    type: Array,
    default: () => []
  },
  maxDisplayCount: {
    type: Number,
    default: 2
  },
  hiddenInputName: {
    type: String,
    default: 'stock_codes'
  },
  dropdownId: {
    type: String,
    default: 'stockSearchDropdown'
  },
  market: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

// 状态
const searchText = ref('')
const selectedCodes = ref(props.modelValue)
const selectAll = ref(false)

// 计算属性
const filteredStocks = computed(() => {
  let stocks = props.stocks
  if (props.market) {
    stocks = stocks.filter(stock => stock.market === props.market)
  }
  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    return stocks.filter(stock => 
      stock.code.toLowerCase().includes(search) || 
      (stock.name && stock.name.toLowerCase().includes(search))
    )
  }
  return stocks
})

const buttonLabel = computed(() => {
  if (selectedCodes.value.length === 0) {
    return '请选择股票'
  }
  if (selectedCodes.value.length <= props.maxDisplayCount) {
    return selectedCodes.value.map(code => getStockLabel(code)).join(', ')
  }
  return `${selectedCodes.value.length} 只股票已选`
})

const buttonTitle = computed(() => {
  if (selectedCodes.value.length === 0) return ''
  return selectedCodes.value.map(code => getStockLabel(code)).join('\n')
})

// 方法
const getStockLabel = (code) => {
  const stock = props.stocks.find(s => s.code === code)
  return stock ? `${stock.code}${stock.name ? ` (${stock.name})` : ''}` : code
}

const handleSelectAll = () => {
  if (selectAll.value) {
    selectedCodes.value = filteredStocks.value.map(stock => stock.code)
  } else {
    selectedCodes.value = []
  }
  emitChange()
}

const handleStockSelect = () => {
  selectAll.value = filteredStocks.value.length > 0 && 
                    filteredStocks.value.every(stock => 
                      selectedCodes.value.includes(stock.code))
  emitChange()
}

const removeStock = (code) => {
  selectedCodes.value = selectedCodes.value.filter(c => c !== code)
  selectAll.value = false
  emitChange()
}

const emitChange = () => {
  emit('update:modelValue', selectedCodes.value)
  emit('change', selectedCodes.value)
}

// 监听 props 变化
watch(() => props.modelValue, (newValue) => {
  selectedCodes.value = newValue
}, { deep: true })

// 监听市场变化
watch(() => props.market, () => {
  // 当市场变化时，清除不属于该市场的选中股票
  if (props.market) {
    selectedCodes.value = selectedCodes.value.filter(code => {
      const stock = props.stocks.find(s => s.code === code)
      return stock && stock.market === props.market
    })
    emitChange()
  }
})
</script>

<style scoped>
.stock-selector {
  position: relative;
}

.dropdown-menu {
  max-height: 300px;
  overflow-y: auto;
}

.dropdown-toggle {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  position: relative;
  padding-right: 25px;
}

.dropdown-toggle::after {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
}

.dropdown-item {
  padding: 8px 12px;
  margin: 2px 0;
  border-radius: 4px;
  white-space: normal;
  word-break: break-all;
}

.dropdown-item:hover {
  background-color: #f8f9fa;
}

.dropdown-item input[type="checkbox"] {
  margin-right: 8px;
}

.stock-list {
  max-height: 200px;
  overflow-y: auto;
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: 0.35rem 0.65rem;
  font-weight: normal;
  background-color: #e9ecef !important;
  color: #212529 !important;
  border: 1px solid #ced4da;
}

.badge .btn-close {
  width: 0.5rem;
  height: 0.5rem;
  margin-left: 0.5rem;
  cursor: pointer;
  opacity: 0.5;
}

.badge .btn-close:hover {
  opacity: 1;
}

.text-muted {
  font-size: 0.875rem;
  color: #6c757d;
  padding: 8px;
  text-align: center;
}
</style> 