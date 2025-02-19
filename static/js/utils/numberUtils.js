export function formatNumber(value, decimals = 2) {
    if (value === null || value === undefined) return '-'
    return Number(value).toLocaleString('zh-HK', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    })
}

export function formatRate(value) {
    if (value === null || value === undefined) return '-'
    return value.toFixed(1) + '%'
} 