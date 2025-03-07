/**
 * 处理交易数据分组
 * @param {Object} transactions 交易数据
 * @returns {Object} 分组后的数据
 */
export const processTransactionGroups = (transactions) => {
  const grouped = {}
  
  // 初始化分组结构
  Object.entries(transactions).forEach(([key, transaction]) => {
    const [market, code] = key.split('-')
    if (!grouped[market]) {
      grouped[market] = {
        holding_stocks: [],
        closed_stocks: [],
        total: {
          buy_amount: 0,
          sell_amount: 0,
          fees: 0
        }
      }
    }
    
    // 更新市场总计
    grouped[market].total.buy_amount += transaction.total_buy || 0
    grouped[market].total.sell_amount += transaction.total_sell || 0
    grouped[market].total.fees += transaction.total_fees || 0
    
    // 根据持仓数量分类
    if (transaction.quantity > 0) {
      grouped[market].holding_stocks.push({
        market,
        code,
        ...transaction
      })
    } else {
      grouped[market].closed_stocks.push({
        market,
        code,
        ...transaction
      })
    }
  })
  
  // 对每个市场的股票进行排序
  Object.values(grouped).forEach(market => {
    // 持仓股票按市值降序排序
    market.holding_stocks.sort((a, b) => (b.market_value || 0) - (a.market_value || 0))
    // 已清仓股票按实现盈亏降序排序
    market.closed_stocks.sort((a, b) => (b.realized_profit || 0) - (a.realized_profit || 0))
  })
  
  return grouped
}

/**
 * 处理交易明细数据
 * @param {Array} details 交易明细数据
 * @returns {Array} 处理后的明细数据
 */
export const processTransactionDetails = (details) => {
  if (!details) return []
  
  // 按交易日期和ID降序排序
  return [...details].sort((a, b) => {
    const dateA = new Date(a.transaction_date)
    const dateB = new Date(b.transaction_date)
    if (dateA.getTime() !== dateB.getTime()) {
      return dateB.getTime() - dateA.getTime()
    }
    return b.id - a.id
  })
}

/**
 * 计算交易盈亏
 * @param {Object} detail 交易明细
 * @returns {number} 盈亏金额
 */
export const calculateTransactionProfit = (detail) => {
  if (detail.transaction_type !== 'sell') return 0
  const sellAmount = detail.total_amount
  const costAmount = detail.total_quantity * detail.sold_average_cost
  const fees = detail.total_fees_hkd
  return Number((sellAmount - costAmount - fees).toFixed(2))
} 