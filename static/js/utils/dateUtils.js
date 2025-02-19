export function formatDateInput(value) {
    if (!value) return ''
    
    value = value.replace(/[^\d]/g, '')
    const currentYear = new Date().getFullYear()
    
    // 根据输入长度进行不同处理
    if (value.length === 4) { // 输入格式：MMDD
        const month = value.substring(0, 2)
        const day = value.substring(2, 4)
        if (month >= 1 && month <= 12 && day >= 1 && day <= 31) {
            return `${currentYear}-${month}-${day}`
        }
    } else if (value.length === 3) { // 输入格式：MDD
        const month = value.substring(0, 1)
        const day = value.substring(1, 3)
        if (month >= 1 && month <= 12 && day >= 1 && day <= 31) {
            return `${currentYear}-0${month}-${day}`
        }
    } else if (value.length === 2) { // 输入格式：DD
        const currentMonth = (new Date().getMonth() + 1).toString().padStart(2, '0')
        const day = value
        if (day >= 1 && day <= 31) {
            return `${currentYear}-${currentMonth}-${day}`
        }
    } else if (value.length === 8) { // 输入格式：YYYYMMDD
        const year = value.substring(0, 4)
        const month = value.substring(4, 6)
        const day = value.substring(6, 8)
        if (month >= 1 && month <= 12 && day >= 1 && day <= 31) {
            return `${year}-${month}-${day}`
        }
    }
    
    return value
} 