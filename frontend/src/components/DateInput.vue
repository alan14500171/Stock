<template>
  <div class="date-input">
    <input
      type="text"
      class="form-control form-control-sm"
      :value="modelValue"
      @input="handleInput"
      @blur="handleBlur"
      :placeholder="placeholder"
      :class="{ 'is-invalid': !!error }"
    />
    <div v-if="error" class="invalid-feedback">
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  modelValue: String,
  placeholder: {
    type: String,
    default: 'YYYY-MM-DD'
  }
})

const emit = defineEmits(['update:modelValue'])
const error = ref('')

const formatDateInput = (value) => {
  if (!value) return ''
  
  value = value.replace(/[^\d]/g, '')
  const currentYear = new Date().getFullYear()
  const currentMonth = (new Date().getMonth() + 1)
  
  try {
    let year, month, day
    
    switch (value.length) {
      case 8: // YYYYMMDD
        year = parseInt(value.substring(0, 4))
        month = parseInt(value.substring(4, 6))
        day = parseInt(value.substring(6, 8))
        break
        
      case 4: // MMDD
        year = currentYear
        month = parseInt(value.substring(0, 2))
        day = parseInt(value.substring(2, 4))
        break
        
      case 3: // MDD
        year = currentYear
        month = parseInt(value.substring(0, 1))
        day = parseInt(value.substring(1, 3))
        break
        
      case 2: // DD
        year = currentYear
        month = currentMonth
        day = parseInt(value)
        break
        
      default:
        return ''
    }
    
    // 验证日期是否有效
    if (!isValidDate(year, month, day)) {
      return ''
    }
    
    // 格式化为 YYYY-MM-DD
    return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
  } catch (e) {
    return ''
  }
}

const isValidDate = (year, month, day) => {
  // 检查月份范围
  if (month < 1 || month > 12) return false
  
  // 获取指定月份的最后一天
  const lastDay = new Date(year, month, 0).getDate()
  
  // 检查日期范围
  if (day < 1 || day > lastDay) return false
  
  // 检查年份范围（假设允许1900年至今）
  const currentYear = new Date().getFullYear()
  if (year < 1900 || year > currentYear) return false
  
  return true
}

const handleInput = (e) => {
  const value = e.target.value
  error.value = ''
  emit('update:modelValue', value)
}

const handleBlur = (e) => {
  let value = e.target.value.trim()
  error.value = ''

  if (!value) {
    emit('update:modelValue', '')
    return
  }

  const formattedDate = formatDateInput(value)
  if (formattedDate) {
    emit('update:modelValue', formattedDate)
  } else {
    error.value = '请输入有效的日期格式'
    emit('update:modelValue', '')
  }
}
</script>

<style scoped>
.date-input {
  position: relative;
}

.date-input input {
  padding-right: 30px;
}

.invalid-feedback {
  display: block;
  font-size: 0.75rem;
}
</style> 