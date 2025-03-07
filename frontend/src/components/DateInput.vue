<template>
  <div class="date-input">
    <input
      type="text"
      class="form-control"
      :value="displayValue"
      @input="handleInputChange"
      @blur="handleBlurChange"
      @keydown.enter="handleEnter"
      :placeholder="placeholder"
      :class="{ 'is-invalid': $attrs.class?.includes('is-invalid') }"
      ref="input"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'

const props = defineProps({
  modelValue: String,
  placeholder: {
    type: String,
    default: 'YYYY-MM-DD'
  }
})

const emit = defineEmits(['update:modelValue', 'enter', 'blur'])

const displayValue = ref(props.modelValue || '')

// 处理输入变化
const handleInputChange = (event) => {
  const value = event.target.value
  displayValue.value = value
  emit('update:modelValue', value)
}

// 处理失焦事件
const handleBlurChange = () => {
  if (!displayValue.value) {
    emit('blur', '')
    return
  }

  const value = displayValue.value.trim()
  let formattedDate = null

  // 处理快捷输入
  if (/^[a-zA-Z]+$/.test(value)) {
    const now = new Date()
    switch (value.toLowerCase()) {
      case 't':
      case 'today':
        formattedDate = formatDate(now)
        break
      case 'y':
      case 'yday':
        now.setDate(now.getDate() - 1)
        formattedDate = formatDate(now)
        break
      case 'tm':
      case 'tmr':
        now.setDate(now.getDate() + 1)
        formattedDate = formatDate(now)
        break
    }
  }

  // 处理相对日期（如：+7 表示7天后，-7 表示7天前）
  if (/^[+-]\d+$/.test(value)) {
    const days = parseInt(value)
    const date = new Date()
    date.setDate(date.getDate() + days)
    formattedDate = formatDate(date)
  }

  // 处理 MMDD 格式
  if (/^\d{3,4}$/.test(value)) {
    const now = new Date()
    const year = now.getFullYear()
    let month, day

    if (value.length === 3) {
      month = parseInt(value[0])
      day = parseInt(value.slice(1))
    } else {
      month = parseInt(value.slice(0, 2))
      day = parseInt(value.slice(2))
    }

    if (month >= 1 && month <= 12 && day >= 1 && day <= 31) {
      const date = new Date(year, month - 1, day)
      if (isValidDate(date)) {
        formattedDate = formatDate(date)
      }
    }
  }

  // 处理 M-D、M.D 或 M/D 格式
  const separators = ['-', '.', '/']
  for (const separator of separators) {
    if (value.includes(separator)) {
      const [month, day] = value.split(separator).map(Number)
      const now = new Date()
      const year = now.getFullYear()

      if (month >= 1 && month <= 12 && day >= 1 && day <= 31) {
        const date = new Date(year, month - 1, day)
        if (isValidDate(date)) {
          formattedDate = formatDate(date)
          break
        }
      }
    }
  }

  // 处理标准格式
  if (!formattedDate) {
    const date = new Date(value)
    if (isValidDate(date)) {
      formattedDate = formatDate(date)
    }
  }

  if (formattedDate) {
    displayValue.value = formattedDate
    emit('update:modelValue', formattedDate)
  }
  
  emit('blur', displayValue.value)
}

// 格式化日期
const formatDate = (date) => {
  if (!(date instanceof Date) || isNaN(date)) return ''
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// 验证日期是否有效
const isValidDate = (date) => {
  return date instanceof Date && !isNaN(date)
}

// 处理回车键
const handleEnter = (event) => {
  event.preventDefault()
  emit('enter', event)
}

// 监听 modelValue 变化
watch(() => props.modelValue, (newValue) => {
  if (newValue !== displayValue.value) {
    displayValue.value = newValue
  }
})

// 组件挂载时，如果没有值则设置为当天
onMounted(() => {
  if (!props.modelValue) {
    const today = formatDate(new Date())
    displayValue.value = today
    emit('update:modelValue', today)
  }
})
</script>

<style scoped>
.date-input {
  position: relative;
}

.date-input input {
  padding: 0.25rem 0.5rem;
  height: calc(2rem + 2px);
  font-size: 0.875rem;
}
</style> 