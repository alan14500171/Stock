<template>
  <div class="stock-selector" data-testid="stock-selector-container">
    <div class="selected-items form-control" data-testid="selected-items-container" @click="handleContainerClick">
      <div v-for="code in modelValue" :key="code" class="selected-tag" :data-testid="'selected-tag-' + code">
        {{ getStockLabel(code) }}
        <button type="button" class="btn-close" @click.stop="removeStock(code)" :data-testid="'remove-stock-btn-' + code"></button>
      </div>
      <div class="search-container" v-show="showDropdown || modelValue.length === 0">
        <input
          type="text"
          class="search-input"
          :value="searchText"
          @input="handleInput"
          @keydown.enter.prevent="handleEnter"
          @keydown.up.prevent="navigateList('up')"
          @keydown.down.prevent="navigateList('down')"
          :placeholder="placeholder"
          ref="input"
          @click.stop="handleInputClick"
          data-testid="stock-search-input"
        />
      </div>
    </div>
    <div class="dropdown-menu" :class="{ show: showDropdown }" data-testid="dropdown-menu">
      <!-- 全选/取消全选和清空选择 -->
      <div class="dropdown-header d-flex justify-content-between align-items-center" data-testid="dropdown-header">
        <div class="select-all">
          <input 
            type="checkbox" 
            class="form-check-input me-2" 
            :checked="isAllSelected"
            @change="toggleSelectAll"
            :indeterminate="isIndeterminate"
            data-testid="select-all-checkbox"
          >
          <span data-testid="select-all-text">全选</span>
        </div>
        <div class="d-flex align-items-center gap-3">
          <small class="text-muted" data-testid="selected-count">已选 {{ modelValue.length }} 项</small>
          <button 
            v-if="modelValue.length > 0"
            type="button" 
            class="btn btn-link btn-sm p-0 text-danger" 
            @click="clearSelected"
            data-testid="clear-selected-btn"
          >
            清空选择
          </button>
        </div>
      </div>

      <!-- 股票列表 -->
      <div class="stock-list" data-testid="stock-list">
        <template v-if="filteredStocks.length > 0">
          <a
            v-for="(stock, index) in filteredStocks"
            :key="stock.code"
            class="dropdown-item"
            :class="{ 'active': index === currentIndex }"
            href="#"
            @click.prevent="handleStockSelect(stock)"
            @mouseover="currentIndex = index"
            :data-testid="'stock-item-' + stock.code"
          >
            <input 
              type="checkbox" 
              class="form-check-input me-2" 
              :checked="isSelected(stock.code)"
              :data-testid="'stock-checkbox-' + stock.code"
            >
            <span class="stock-code" :data-testid="'stock-code-' + stock.code">{{ stock.code }}</span>
            <span class="stock-name" :data-testid="'stock-name-' + stock.code">{{ stock.code_name || stock.name || '' }}</span>
          </a>
        </template>
        <div v-else class="dropdown-item text-muted" data-testid="no-results">
          无匹配结果
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed, onBeforeUnmount } from 'vue'
import axios from 'axios'
import { debounce } from 'lodash'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  stocks: {
    type: Array,
    default: () => []
  },
  market: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: '输入代码或名称搜索'
  }
})

const emit = defineEmits(['update:modelValue', 'enter'])

// 搜索和过滤
const searchText = ref('')
const showDropdown = ref(false)
const input = ref(null)
const currentIndex = ref(-1)
const stockList = ref([])
const refreshTimer = ref(null)

// 获取股票列表
const fetchStocks = async () => {
  try {
    const response = await axios.get('/api/stock/stocks', {
      params: {
        market: props.market,
        per_page: 1000
      }
    })
    if (response.data.success) {
      stockList.value = response.data.data.items
    }
  } catch (error) {
    console.error('获取股票列表失败:', error)
  }
}

// 启动定时刷新
const startRefreshTimer = () => {
  stopRefreshTimer()
  refreshTimer.value = setInterval(fetchStocks, 60000) // 每分钟刷新一次
}

// 停止定时刷新
const stopRefreshTimer = () => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }
}

// 计算过滤后的股票列表
const filteredStocks = computed(() => {
  let result = stockList.value
  if (props.market) {
    result = result.filter(stock => stock.market === props.market)
  }
  if (searchText.value) {
    const searchValue = searchText.value.toLowerCase()
    result = result.filter(stock => 
      stock.code.toLowerCase().includes(searchValue) || 
      (stock.name && stock.name.toLowerCase().includes(searchValue))
    )
  }
  return result
})

// 全选状态
const isAllSelected = computed(() => {
  return filteredStocks.value.length > 0 && 
         filteredStocks.value.every(stock => isSelected(stock.code))
})

const isIndeterminate = computed(() => {
  const selectedCount = filteredStocks.value.filter(stock => isSelected(stock.code)).length
  return selectedCount > 0 && selectedCount < filteredStocks.value.length
})

// 获取股票显示标签
const getStockLabel = (code) => {
  const stock = props.stocks.find(s => s.code === code)
  if (!stock) return code
  const name = stock.code_name || stock.name || ''
  return `${stock.code} - ${name}`
}

// 检查股票是否已选中
const isSelected = (code) => {
  return props.modelValue.includes(code)
}

// 切换全选/取消全选
const toggleSelectAll = () => {
  const newValue = [...props.modelValue]
  if (isAllSelected.value) {
    // 取消全选
    filteredStocks.value.forEach(stock => {
      const index = newValue.indexOf(stock.code)
      if (index !== -1) {
        newValue.splice(index, 1)
      }
    })
  } else {
    // 全选
    filteredStocks.value.forEach(stock => {
      if (!newValue.includes(stock.code)) {
        newValue.push(stock.code)
      }
    })
  }
  emit('update:modelValue', newValue)
}

// 清空所有选择
const clearSelected = () => {
  emit('update:modelValue', [])
  searchText.value = ''
  showDropdown.value = false
}

// 删除已选择的股票
const removeStock = (code) => {
  const newValue = props.modelValue.filter(item => item !== code)
  emit('update:modelValue', newValue)
}

// 处理容器点击
const handleContainerClick = () => {
  showDropdown.value = true
  nextTick(() => {
    input.value?.focus()
  })
}

// 处理输入框点击
const handleInputClick = (event) => {
  event.stopPropagation()
  showDropdown.value = true
}

// 处理输入
const handleInput = (event) => {
  const value = event.target.value
  searchText.value = value
  showDropdown.value = true
  currentIndex.value = -1

  // 如果输入的是数字，尝试自动补全港股代码
  if (/^\d+$/.test(value)) {
    const paddedCode = value.padStart(4, '0')
    const matchingStock = props.stocks.find(s => 
      s.market === 'HK' && s.code === paddedCode
    )
    if (matchingStock) {
      currentIndex.value = filteredStocks.value.findIndex(s => s.code === matchingStock.code)
    }
  }
}

// 处理回车键
const handleEnter = (event) => {
  if (showDropdown.value && filteredStocks.value.length > 0) {
    event.preventDefault()
    if (currentIndex.value >= 0) {
      handleStockSelect(filteredStocks.value[currentIndex.value])
    } else if (filteredStocks.value.length === 1) {
      handleStockSelect(filteredStocks.value[0])
    }
  } else {
    emit('enter', event)
  }
}

// 处理股票选择
const handleStockSelect = (stock) => {
  const newValue = [...props.modelValue]
  const index = newValue.indexOf(stock.code)
  
  if (index === -1) {
    newValue.push(stock.code)
  } else {
    newValue.splice(index, 1)
  }
  
  emit('update:modelValue', newValue)
  searchText.value = ''
  
  // 保持下拉框打开状态
  showDropdown.value = true
  nextTick(() => {
    input.value?.focus()
  })
}

// 键盘导航
const navigateList = (direction) => {
  if (!showDropdown.value || filteredStocks.value.length === 0) {
    return
  }

  if (direction === 'up') {
    currentIndex.value = currentIndex.value <= 0 
      ? filteredStocks.value.length - 1 
      : currentIndex.value - 1
  } else {
    currentIndex.value = currentIndex.value >= filteredStocks.value.length - 1 
      ? 0 
      : currentIndex.value + 1
  }

  // 确保当前选中项在可视区域内
  nextTick(() => {
    const stockList = document.querySelector('.stock-list')
    const activeItem = stockList?.querySelector('.dropdown-item.active')
    if (activeItem) {
      activeItem.scrollIntoView({ block: 'nearest' })
    }
  })
}

// 点击外部关闭下拉框
const handleClickOutside = (event) => {
  if (!event.target.closest('.stock-selector')) {
    showDropdown.value = false
    searchText.value = ''
  }
}

// 监听下拉框显示状态
watch(showDropdown, (newValue) => {
  if (!newValue) {
    currentIndex.value = -1
    searchText.value = ''
  }
})

// 在组件挂载时获取股票列表并启动定时刷新
onMounted(() => {
  fetchStocks()
  startRefreshTimer()
  document.addEventListener('click', handleClickOutside)
})

// 在组件卸载时清理
onBeforeUnmount(() => {
  stopRefreshTimer()
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.stock-selector {
  position: relative;
  min-width: 300px;
  width: 100%;
}

.selected-items {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  min-height: calc(1.5em + 0.75rem + 2px);
  max-height: calc(4.5em + 0.75rem + 2px);
  padding: 0.25rem;
  cursor: text;
  background-color: #fff;
  align-items: flex-start;
  overflow-y: auto;
}

.search-container {
  flex: 1;
  min-width: 100px;
}

.search-input {
  width: 100%;
  border: none;
  outline: none;
  padding: 0.25rem;
  font-size: 0.875rem;
  background: transparent;
}

.selected-tag {
  display: inline-flex;
  align-items: center;
  background-color: #f8f9fa;
  border-radius: 0.25rem;
  padding: 0.125rem 0.375rem;
  font-size: 0.75rem;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin: 1px;
  border: 1px solid #dee2e6;
  flex-shrink: 0;
  color: #495057;
}

.selected-tag .btn-close {
  font-size: 0.675rem;
  margin-left: 0.375rem;
  padding: 0.125rem;
  opacity: 0.5;
  min-width: 12px;
  min-height: 12px;
}

.selected-tag .btn-close:hover {
  opacity: 1;
}

.dropdown-menu {
  width: 100%;
  margin-top: 1px;
  padding: 0;
  max-height: 350px;
  overflow-y: hidden;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
  display: none;
  flex-direction: column;
}

.dropdown-menu.show {
  display: flex;
}

.dropdown-header {
  font-size: 0.75rem;
  color: #6c757d;
  padding: 0.5rem 0.75rem;
  background-color: #f8f9fa;
  border-bottom: 1px solid #dee2e6;
}

.stock-list {
  overflow-y: auto;
  max-height: 300px;
}

.dropdown-item {
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  color: #212529;
  text-decoration: none;
  cursor: pointer;
}

.dropdown-item:hover {
  background-color: #f8f9fa;
}

.dropdown-item.active {
  background-color: #e9ecef;
}

.stock-code {
  font-weight: 500;
  margin-right: 0.5rem;
}

.stock-name {
  color: #6c757d;
}

.form-check-input {
  margin-right: 0.5rem;
}

.btn-link {
  text-decoration: none;
  font-size: 0.75rem;
  padding: 0;
}

.btn-link:hover {
  text-decoration: underline;
}
</style> 