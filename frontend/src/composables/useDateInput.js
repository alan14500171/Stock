// 日期输入处理工具
import { ref, computed } from 'vue'

export function useDateInput(initialValue = '') {
  const inputValue = ref(initialValue)
  const displayValue = ref(initialValue)

  // 获取当前日期
  const getCurrentDate = () => {
    const now = new Date()
    return now.toISOString().split('T')[0]
  }

  // 格式化日期
  const formatDate = (date) => {
    if (!(date instanceof Date) || isNaN(date)) return ''
    return date.toISOString().split('T')[0]
  }

  // 验证日期是否有效
  const isValidDate = (date) => {
    return date instanceof Date && !isNaN(date)
  }

  // 处理输入事件
  const handleInput = (event) => {
    console.log('handleInput event:', event)
    const value = event.target.value
    inputValue.value = value
    displayValue.value = value
    return value
  }

  // 处理失焦事件，在这里进行日期格式化
  const handleBlur = () => {
    console.log('handleBlur current value:', inputValue.value)
    if (!inputValue.value) return { isValid: true, value: '' }

    const value = inputValue.value.trim()
    
    // 处理快捷输入
    if (/^[a-zA-Z]+$/.test(value)) {
      const now = new Date()
      switch (value.toLowerCase()) {
        case 't':
        case 'today':
          displayValue.value = formatDate(now)
          return { isValid: true, value: displayValue.value }
        case 'y':
        case 'yday':
          now.setDate(now.getDate() - 1)
          displayValue.value = formatDate(now)
          return { isValid: true, value: displayValue.value }
        case 'tm':
        case 'tmr':
          now.setDate(now.getDate() + 1)
          displayValue.value = formatDate(now)
          return { isValid: true, value: displayValue.value }
      }
    }

    // 处理相对日期（如：+7 表示7天后，-7 表示7天前）
    if (/^[+-]\d+$/.test(value)) {
      const days = parseInt(value)
      const date = new Date()
      date.setDate(date.getDate() + days)
      displayValue.value = formatDate(date)
      return { isValid: true, value: displayValue.value }
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
          displayValue.value = formatDate(date)
          return { isValid: true, value: displayValue.value }
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
            displayValue.value = formatDate(date)
            return { isValid: true, value: displayValue.value }
          }
        }
      }
    }

    // 处理标准格式
    const date = new Date(value)
    if (isValidDate(date)) {
      displayValue.value = formatDate(date)
      return { isValid: true, value: displayValue.value }
    }

    // 如果无法解析，保持原值
    return { isValid: false, value: inputValue.value }
  }

  // 设置为今天
  const setToday = () => {
    const today = getCurrentDate()
    inputValue.value = today
    displayValue.value = today
    return today
  }

  return {
    displayValue,
    handleInput,
    handleBlur,
    setToday
  }
} 