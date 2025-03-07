<template>
        <div class="card">
          <div class="card-header d-flex justify-content-between align-items-center">
      <h4 class="mb-0">盈利统计</h4>
      <div class="btn-group">
        <button type="button" class="btn btn-sm btn-outline-secondary" @click="toggleSearch">
          <i :class="['bi', searchVisible ? 'bi-chevron-up' : 'bi-search']"></i>
          {{ searchVisible ? '收起' : '搜索' }}
              </button>
        <button type="button" class="btn btn-sm btn-outline-primary" @click="refreshMarketValue" :disabled="refreshLoading">
          <i :class="['bi', refreshLoading ? 'bi-arrow-clockwise bi-spin' : 'bi-arrow-clockwise']"></i>
          刷新市值
              </button>
        <button type="button" class="btn btn-sm btn-primary" @click="addTransaction">
          <i class="bi bi-plus-lg"></i>
          添加记录
              </button>
      </div>
    </div>
    
    <!-- 搜索表单 -->
    <div v-show="searchVisible" class="card-body border-bottom">
      <form @submit.prevent="search" class="row g-2 align-items-end">
        <div class="col-auto">
          <label class="form-label small">开始日期</label>
          <input
            type="text"
            class="form-control form-control-sm"
            style="width: 130px;"
            :value="startDateDisplayValue"
            @input="handleStartDateInput"
            @blur="handleStartDateBlur"
            @keydown.enter.prevent="focusNext($event, 'endDate')"
            @keydown.tab="focusNext($event, 'endDate')"
            placeholder="YYYY-MM-DD"
            ref="startDate"
          />
              </div>
        <div class="col-auto">
          <label class="form-label small">结束日期</label>
          <input
            type="text"
            class="form-control form-control-sm"
            style="width: 130px;"
            :value="endDateDisplayValue"
            @input="handleEndDateInput"
            @blur="handleEndDateBlur"
            @keydown.enter.prevent="focusNext($event, 'market')"
            @keydown.tab="focusNext($event, 'market')"
            placeholder="YYYY-MM-DD"
            ref="endDate"
          />
                </div>
        <div class="col-auto">
          <label class="form-label small">市场</label>
          <select 
            class="form-select form-select-sm"
            style="width: 100px;"
            v-model="searchForm.market"
            ref="market"
            @keydown.enter.prevent="focusNext($event, 'search')"
            @keydown.tab="focusNext($event, 'search')"
          >
            <option value="">全部</option>
            <option value="HK">HK</option>
            <option value="USA">USA</option>
          </select>
              </div>
        <div class="col-auto" style="min-width: 200px; max-width: 300px;">
          <label class="form-label small">股票代码</label>
          <stock-selector
            v-model="searchForm.stockCodes"
            :stocks="allStocks"
            :market="searchForm.market"
            class="stock-selector-sm"
          />
            </div>
        <div class="col-auto flex-grow-1" style="max-width: 50px;"></div>
        <div class="col-auto d-flex align-items-end" style="min-width: 80px;">
          <button type="submit" class="btn btn-sm btn-primary w-100 border border-primary text-white" style="background-color: #0D6EFD;" :disabled="loading" ref="searchBtn">
            <i class="bi bi-search me-1"></i>查询
          </button>
          </div>
        <div class="col-auto d-flex align-items-end" style="min-width: 80px;">
          <button type="button" class="btn btn-sm btn-outline-secondary w-100" @click="resetSearch">
            <i class="bi bi-arrow-clockwise me-1"></i>重置
          </button>
        </div>
      </form>
      </div>
      
          <div class="card-body p-0">
            <div class="table-responsive">
        <table class="table table-hover table-sm mb-0">
                <thead class="table-light">
                  <tr>
              <th></th>
              <th>市场</th>
              <th class="text-end">股票数量</th>
              <th class="text-end">笔数</th>
              <th class="text-end">买入总额</th>
              <th class="text-end" title="移动加权平均价">平均价格</th>
              <th class="text-end">卖出总额</th>
              <th class="text-end">费用</th>
              <th class="text-end">已实现盈亏</th>
              <th class="text-end">现价</th>
              <th class="text-end">持仓盈亏</th>
              <th class="text-end">总盈亏</th>
              <th class="text-end">盈亏率</th>
                  </tr>
                </thead>
                <tbody>
            <template v-for="market in getMarkets" :key="market">
              <!-- 市场汇总 -->
              <tr class="market-row">
                <td>
                  <button @click="toggleMarket(market)" class="btn btn-sm btn-outline-primary">
                    <i :class="['bi bi-chevron-right', { 'rotate-90': isMarketExpanded(market) }]"></i>
                  </button>
                </td>
                <td>{{ market }}</td>
                <td class="text-end">{{ formatNumber(marketStats[market].total_stocks, 0) }}</td>
                <td class="text-end">{{ marketStats[market].transaction_count }}</td>
                <td class="text-end text-danger">{{ formatNumber(marketStats[market].total_buy) }}</td>
                <td class="text-end">-</td>
                <td class="text-end text-success">{{ formatNumber(marketStats[market].total_sell) }}</td>
                <td class="text-end">{{ formatNumber(marketStats[market].total_fees) }}</td>
                <td class="text-end" :class="getProfitClass(marketStats[market].realized_profit)">
                  {{ formatNumber(marketStats[market].realized_profit) }}
                </td>
                <td class="text-end">-</td>
                <td class="text-end" :class="getProfitClass(marketStats[market].holding_profit)">
                  {{ formatNumber(marketStats[market].holding_profit) }}
                </td>
                <td class="text-end" :class="getProfitClass(marketStats[market].total_profit)">
                  {{ formatNumber(marketStats[market].total_profit) }}
                </td>
                <td class="text-end" :class="getProfitClass(marketStats[market].profit_rate)">
                  {{ formatRate(marketStats[market].profit_rate) }}
                </td>
              </tr>

              <!-- 持仓统计 -->
              <tr v-if="isMarketExpanded(market)" class="holding-stats-row">
                <td></td>
                <td><strong>持仓统计</strong></td>
                <td class="text-end">{{ marketStats[market].holding_stats.count }}</td>
                <td class="text-end">-</td>
                <td class="text-end text-danger">{{ formatNumber(marketStats[market].holding_stats.total_buy) }}</td>
                <td class="text-end">-</td>
                <td class="text-end text-success">{{ formatNumber(marketStats[market].holding_stats.total_sell) }}</td>
                <td class="text-end">{{ formatNumber(marketStats[market].holding_stats.total_fees) }}</td>
                <td class="text-end" :class="getProfitClass(marketStats[market].holding_stats.realized_profit)">
                  {{ formatNumber(marketStats[market].holding_stats.realized_profit) }}
                </td>
                <td class="text-end">-</td>
                <td class="text-end" :class="getProfitClass(marketStats[market].holding_stats.holding_profit)">
                  {{ formatNumber(marketStats[market].holding_stats.holding_profit) }}
                </td>
                <td class="text-end" :class="getProfitClass(marketStats[market].holding_stats.total_profit)">
                  {{ formatNumber(marketStats[market].holding_stats.total_profit) }}
                </td>
                <td class="text-end" :class="getProfitClass(marketStats[market].holding_stats.profit_rate)">
                  {{ formatRate(marketStats[market].holding_stats.profit_rate) }}
                </td>
              </tr>

              <!-- 已清仓统计 -->
              <tr v-if="isMarketExpanded(market)" class="closed-stats-row">
                <td></td>
                <td><strong>已清仓统计</strong></td>
                <td class="text-end">{{ marketStats[market].closed_stats.count }}</td>
                <td class="text-end">-</td>
                <td class="text-end text-danger">{{ formatNumber(marketStats[market].closed_stats.total_buy) }}</td>
                <td class="text-end">-</td>
                <td class="text-end text-success">{{ formatNumber(marketStats[market].closed_stats.total_sell) }}</td>
                <td class="text-end">{{ formatNumber(marketStats[market].closed_stats.total_fees) }}</td>
                <td class="text-end" :class="getProfitClass(marketStats[market].closed_stats.realized_profit)">
                  {{ formatNumber(marketStats[market].closed_stats.realized_profit) }}
                </td>
                <td class="text-end">-</td>
                <td class="text-end">-</td>
                <td class="text-end">-</td>
                <td class="text-end" :class="getProfitClass(marketStats[market].closed_stats.profit_rate)">
                  {{ formatRate(marketStats[market].closed_stats.profit_rate) }}
                </td>
              </tr>

              <!-- 持仓股票 -->
              <template v-if="isMarketExpanded(market)">
                <tr class="holding-group-row">
                  <td>
                    <button @click="toggleHoldingGroup(market)" class="btn btn-sm btn-outline-secondary">
                      <i :class="['bi bi-chevron-right', { 'rotate-90': isHoldingGroupExpanded(market) }]"></i>
                    </button>
                  </td>
                  <td colspan="12"><strong>持仓股票</strong></td>
                </tr>

                <template v-if="isHoldingGroupExpanded(market)">
                  <template v-for="stock in getHoldingStocks(market)" :key="stock.code">
                    <tr class="stock-row">
                      <td>
                        <button @click="toggleStock(market, stock.code)" class="btn btn-sm btn-outline-secondary">
                          <i :class="['bi bi-chevron-right', { 'rotate-90': isStockExpanded(market, stock.code) }]"></i>
                        </button>
                      </td>
                      <td>
                        {{ stock.code }}
                        <span class="company-name" style="display: inline-block; font-size: 14px; color: #6c757d; margin-left: 4px;">{{ stock.stock_name }}</span>
                      </td>
                      <td class="text-end">{{ formatNumber(stock.current_quantity, 0) }}</td>
                      <td class="text-end">{{ stock.transaction_count }}</td>
                      <td class="text-end text-danger">{{ formatNumber(stock.total_buy) }}</td>
                      <td class="text-end">{{ formatNumber(stock.average_cost, 3) }}</td>
                      <td class="text-end text-success">{{ formatNumber(stock.total_sell) }}</td>
                      <td class="text-end">{{ formatNumber(stock.total_fees) }}</td>
                      <td class="text-end" :class="getProfitClass(stock.realized_profit)">
                        {{ formatNumber(stock.realized_profit) }}
                      </td>
                      <td class="text-end">{{ stock.current_quantity > 0 ? formatNumber(stock.current_price, 3) : '-' }}</td>
                      <td class="text-end" :class="getProfitClass(stock.holding_profit)">
                        {{ stock.current_quantity > 0 ? formatNumber(stock.holding_profit) : '-' }}
                      </td>
                      <td class="text-end" :class="getProfitClass(stock.total_profit)">
                        {{ formatNumber(stock.total_profit) }}
                      </td>
                      <td class="text-end" :class="getProfitClass(stock.profit_rate)">
                        {{ formatRate(stock.profit_rate) }}
                      </td>
                    </tr>
                    <!-- 交易明细行 -->
                    <tr v-if="isStockExpanded(market, stock.code)">
                      <td colspan="13" class="p-0">
                        <div class="transaction-details">
                          <table class="table table-sm mb-0">
                            <thead class="table-light">
                              <tr>
                                <th class="transaction-info">交易日期</th>
                                <th class="quantity-price">数量@单价</th>
                                <th class="text-end amount">买入金额</th>
                                <th class="text-end cost" title="移动加权平均价">平均价格</th>
                                <th class="text-end amount">卖出金额</th>
                                <th class="text-end fees">费用</th>
                                <th class="text-end profit">盈亏</th>
                                <th class="text-end current-price">盈亏率</th>
                                <th class="text-end holding-value">持有人</th>
                                <th class="text-end total-profit"></th>
                                <th class="text-end profit-rate"></th>
                              </tr>
                            </thead>
                            <tbody>
                              <template v-if="transactionDetails[`${market}-${stock.code}`]">
                                <tr v-for="detail in sortTransactionDetails(transactionDetails[`${market}-${stock.code}`])" :key="detail.id">
                                  <td class="transaction-info">
                                    {{ formatDate(detail.transaction_date) }}
                                    <span :class="['transaction-type-badge', detail.transaction_type.toLowerCase() === 'buy' ? 'buy' : 'sell']">
                                      {{ detail.transaction_type.toLowerCase() === 'buy' ? '买入' : '卖出' }}
                                    </span>
                                    <span class="transaction-code">{{ detail.transaction_code.trim() }}</span>
                                  </td>
                                  <td class="quantity-price">
                                    {{ formatNumber(detail.total_quantity, 0) }} @ 
                                    {{ formatNumber(detail.total_amount / detail.total_quantity, 3) }}
                                  </td>
                                  <td class="text-end amount">
                                    {{ detail.transaction_type.toLowerCase() === 'buy' ? formatNumber(detail.total_amount) : '' }}
                                  </td>
                                  <td class="text-end cost">
                                    <template v-if="detail.transaction_type.toLowerCase() === 'buy'">
                                      {{ formatNumber(detail.current_avg_cost, 3) }}
                                    </template>
                                    <template v-else>
                                      {{ formatNumber(detail.prev_avg_cost, 3) }}
                                    </template>
                                  </td>
                                  <td class="text-end amount">
                                    {{ detail.transaction_type.toLowerCase() === 'sell' ? formatNumber(detail.total_amount) : '' }}
                                  </td>
                                  <td class="text-end fees">
                                    {{ formatNumber(detail.total_fees) }}
                                  </td>
                                  <td class="text-end" :class="getProfitClass(calculateProfit(detail))">
                                    {{ detail.transaction_type.toLowerCase() === 'sell' ? formatNumber(calculateProfit(detail)) : '-' }}
                                  </td>
                                  <td class="text-end" :class="getProfitClass(calculateProfitRate(detail))">
                                    {{ detail.transaction_type.toLowerCase() === 'sell' ? formatRate(calculateProfitRate(detail)) : '-' }}
                                  </td>
                                  <td class="text-end">{{ detail.holder_name || '-' }}</td>
                                  <td class="text-end">-</td>
                                  <td class="text-end">-</td>
                                </tr>
                              </template>
                              <tr v-else>
                                <td colspan="11" class="text-center py-2">
                                  <small class="text-muted">暂无交易明细数据</small>
                                </td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                      </td>
                    </tr>
                  </template>
                </template>

                <!-- 已清仓股票 -->
                <tr class="closed-group-row">
                  <td>
                    <button @click="toggleClosedGroup(market)" class="btn btn-sm btn-outline-secondary">
                      <i :class="['bi bi-chevron-right', { 'rotate-90': isClosedGroupExpanded(market) }]"></i>
                    </button>
                  </td>
                  <td colspan="12"><strong>已清仓股票</strong></td>
                </tr>

                <template v-if="isClosedGroupExpanded(market)">
                  <template v-for="stock in getClosedStocks(market)" :key="stock.code">
                    <tr class="stock-row">
                      <td>
                        <button @click="toggleStock(market, stock.code)" class="btn btn-sm btn-outline-secondary">
                          <i :class="['bi bi-chevron-right', { 'rotate-90': isStockExpanded(market, stock.code) }]"></i>
                        </button>
                      </td>
                      <td>
                        {{ stock.code }}
                        <span class="company-name" style="display: inline-block; font-size: 14px; color: #6c757d; margin-left: 4px;">{{ stock.stock_name }}</span>
                      </td>
                      <td class="text-end">{{ stock.quantity || '-' }}</td>
                      <td class="text-end">{{ stock.transaction_count }}</td>
                      <td class="text-end text-danger">{{ formatNumber(stock.total_buy) }}</td>
                      <td class="text-end">-</td>
                      <td class="text-end text-success">{{ formatNumber(stock.total_sell) }}</td>
                      <td class="text-end">{{ formatNumber(stock.total_fees) }}</td>
                      <td class="text-end" :class="getProfitClass(stock.realized_profit)">
                        {{ formatNumber(stock.realized_profit) }}
                      </td>
                      <td class="text-end">{{ stock.current_quantity > 0 ? formatNumber(stock.current_price, 3) : '-' }}</td>
                      <td class="text-end" :class="getProfitClass(stock.holding_profit)">
                        {{ stock.current_quantity > 0 ? formatNumber(stock.holding_profit) : '-' }}
                      </td>
                      <td class="text-end" :class="getProfitClass(stock.total_profit)">
                        {{ formatNumber(stock.total_profit) }}
                      </td>
                      <td class="text-end" :class="getProfitClass(stock.profit_rate)">
                        {{ formatRate(stock.profit_rate) }}
                      </td>
                    </tr>
                    <!-- 交易明细行 -->
                    <tr v-if="isStockExpanded(market, stock.code)">
                      <td colspan="13" class="p-0">
                        <div class="transaction-details">
                          <table class="table table-sm mb-0">
                            <thead class="table-light">
                              <tr>
                                <th class="transaction-info">交易日期</th>
                                <th class="quantity-price">数量@单价</th>
                                <th class="text-end amount">买入金额</th>
                                <th class="text-end cost" title="移动加权平均价">平均价格</th>
                                <th class="text-end amount">卖出金额</th>
                                <th class="text-end fees">费用</th>
                                <th class="text-end profit">盈亏</th>
                                <th class="text-end current-price">盈亏率</th>
                                <th class="text-end holding-value">持有人</th>
                                <th class="text-end total-profit"></th>
                                <th class="text-end profit-rate"></th>
                              </tr>
                            </thead>
                            <tbody>
                              <template v-if="transactionDetails[`${market}-${stock.code}`]">
                                <tr v-for="detail in sortTransactionDetails(transactionDetails[`${market}-${stock.code}`])" :key="detail.id">
                                  <td class="transaction-info">
                                    {{ formatDate(detail.transaction_date) }}
                                    <span :class="['transaction-type-badge', detail.transaction_type.toLowerCase() === 'buy' ? 'buy' : 'sell']">
                                      {{ detail.transaction_type.toLowerCase() === 'buy' ? '买入' : '卖出' }}
                                    </span>
                                    <span class="transaction-code">{{ detail.transaction_code.trim() }}</span>
                                  </td>
                                  <td class="quantity-price">
                                    {{ formatNumber(detail.total_quantity, 0) }} @ 
                                    {{ formatNumber(detail.total_amount / detail.total_quantity, 3) }}
                                  </td>
                                  <td class="text-end amount">
                                    {{ detail.transaction_type.toLowerCase() === 'buy' ? formatNumber(detail.total_amount) : '' }}
                                  </td>
                                  <td class="text-end cost">
                                    <template v-if="detail.transaction_type.toLowerCase() === 'buy'">
                                      {{ formatNumber(detail.current_avg_cost, 3) }}
                                    </template>
                                    <template v-else>
                                      {{ formatNumber(detail.prev_avg_cost, 3) }}
                                    </template>
                                  </td>
                                  <td class="text-end amount">
                                    {{ detail.transaction_type.toLowerCase() === 'sell' ? formatNumber(detail.total_amount) : '' }}
                                  </td>
                                  <td class="text-end fees">
                                    {{ formatNumber(detail.total_fees) }}
                                  </td>
                                  <td class="text-end" :class="getProfitClass(calculateProfit(detail))">
                                    {{ detail.transaction_type.toLowerCase() === 'sell' ? formatNumber(calculateProfit(detail)) : '-' }}
                                  </td>
                                  <td class="text-end" :class="getProfitClass(calculateProfitRate(detail))">
                                    {{ detail.transaction_type.toLowerCase() === 'sell' ? formatRate(calculateProfitRate(detail)) : '-' }}
                                  </td>
                                  <td class="text-end">{{ detail.holder_name || '-' }}</td>
                                  <td class="text-end">-</td>
                                  <td class="text-end">-</td>
                                </tr>
                              </template>
                              <tr v-else>
                                <td colspan="11" class="text-center py-2">
                                  <small class="text-muted">暂无交易明细数据</small>
                                </td>
                              </tr>
                            </tbody>
                          </table>
                        </div>
                      </td>
                    </tr>
                  </template>
                </template>
              </template>
            </template>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import DateInput from '../components/DateInput.vue'
import axios from 'axios'
import { useDateInput } from '../composables/useDateInput'
import StockSelector from '../components/StockSelector.vue'
import { Toast } from 'bootstrap'

const router = useRouter()

// 状态管理
const loading = ref(false)
const refreshLoading = ref(false)
const searchVisible = ref(true)
const expandedMarkets = ref(new Set())
const expandedHoldingGroups = ref(new Set())
const expandedClosedGroups = ref(new Set())
const expandedStocks = ref(new Set())
const rawMarketStats = ref({})
const stockStats = ref({})
const transactionDetails = ref({})
const allStocks = ref([])

// 搜索表单
const searchForm = reactive({
  startDate: '',
  endDate: '',
  market: '',
  stockCodes: []
})

const startDate = ref(null)
const endDate = ref(null)
const market = ref(null)

const focusNext = (event, target) => {
  event.preventDefault()
  switch(target) {
    case 'endDate':
      endDate.value?.focus()
      break
    case 'market':
      market.value?.focus()
      break
    case 'search':
      search()
      break
  }
}

// 统计计算模块
const useStatsCalculator = () => {
  // 计算市场统计数据
  const calculateMarketStats = (stockData, filterCodes = []) => {
    const stats = {}
    
    // 遍历所有股票统计数据
    Object.entries(stockData).forEach(([key, stock]) => {
      const [stockMarket] = key.split('-')
      const stockCode = key.split('-')[1]
      
      // 如果有筛选条件且当前股票不在筛选范围内,则跳过
      if (filterCodes.length > 0 && !filterCodes.includes(stockCode)) {
        return
      }
      
      // 初始化市场统计
      if (!stats[stockMarket]) {
        stats[stockMarket] = {
          total_stocks: 0,
          transaction_count: 0,
          total_buy: 0,
          total_sell: 0,
          total_fees: 0,
          realized_profit: 0,
          market_value: 0,
          holding_profit: 0,
          total_profit: 0,
          profit_rate: 0,
          holding_stats: {
            count: 0,
            total_buy: 0,
            total_sell: 0,
            total_fees: 0,
            realized_profit: 0,
            market_value: 0,
            holding_profit: 0,
            total_profit: 0,
            profit_rate: 0
          },
          closed_stats: {
            count: 0,
            total_buy: 0,
            total_sell: 0,
            total_fees: 0,
            realized_profit: 0,
            profit_rate: 0
          }
        }
      }

      // 更新市场统计
      stats[stockMarket].transaction_count += stock.transaction_count || 0
      stats[stockMarket].total_buy += stock.total_buy || 0
      stats[stockMarket].total_sell += stock.total_sell || 0
      stats[stockMarket].total_fees += stock.total_fees || 0
      stats[stockMarket].realized_profit += stock.realized_profit || 0
      stats[stockMarket].market_value += stock.market_value || 0
      stats[stockMarket].holding_profit += stock.holding_profit || 0
      
      if (stock.current_quantity > 0) {
        // 持仓股票统计
        stats[stockMarket].total_stocks += 1
        stats[stockMarket].holding_stats.count++
        stats[stockMarket].holding_stats.total_buy += stock.total_buy || 0
        stats[stockMarket].holding_stats.total_sell += stock.total_sell || 0
        stats[stockMarket].holding_stats.total_fees += stock.total_fees || 0
        stats[stockMarket].holding_stats.realized_profit += stock.realized_profit || 0
        stats[stockMarket].holding_stats.market_value += stock.market_value || 0
        stats[stockMarket].holding_stats.holding_profit += stock.holding_profit || 0
      } else {
        // 已清仓股票统计
        stats[stockMarket].total_stocks += 1
        stats[stockMarket].closed_stats.count++
        stats[stockMarket].closed_stats.total_buy += stock.total_buy || 0
        stats[stockMarket].closed_stats.total_sell += stock.total_sell || 0
        stats[stockMarket].closed_stats.total_fees += stock.total_fees || 0
        stats[stockMarket].closed_stats.realized_profit += stock.realized_profit || 0
      }
    })

    // 计算各项汇总数据
    Object.values(stats).forEach(market => {
      // 持仓统计盈亏
      market.holding_stats.total_profit = 
        (market.holding_stats.realized_profit || 0) + 
        (market.holding_stats.holding_profit || 0)

      // 持仓统计盈亏率
      market.holding_stats.profit_rate = 
        market.holding_stats.total_buy > 0 
          ? ((market.holding_stats.total_profit || 0) / market.holding_stats.total_buy * 100)
          : 0

      // 已清仓统计盈亏率
      market.closed_stats.profit_rate = 
        market.closed_stats.total_buy > 0
          ? ((market.closed_stats.realized_profit || 0) / market.closed_stats.total_buy * 100)
          : 0

      // 市场总计
      market.total_profit = 
        (market.realized_profit || 0) + 
        (market.holding_profit || 0)

      // 市场总盈亏率
      market.profit_rate = 
        market.total_buy > 0 
          ? (market.total_profit / market.total_buy * 100) 
          : 0
    })

    return stats
  }

  // 获取持仓股票列表
  const getHoldingStocks = (stockData, market, filterCodes = []) => {
    return Object.entries(stockData)
      .filter(([key, stock]) => {
        const [stockMarket] = key.split('-')
        const stockCode = key.split('-')[1]
        
        if (filterCodes.length > 0) {
          return stockMarket === market && 
                 stock.current_quantity > 0 && 
                 filterCodes.includes(stockCode)
        }
        return stockMarket === market && stock.current_quantity > 0
      })
      .map(([key, stock]) => ({
        code: key.split('-')[1],
        ...stock
      }))
      .sort((a, b) => {
        // 使用最后交易日期进行排序
        const dateA = new Date(a.last_transaction_date || 0)
        const dateB = new Date(b.last_transaction_date || 0)
        return dateB - dateA
      })
  }

  // 获取已清仓股票列表
  const getClosedStocks = (stockData, market, filterCodes = []) => {
    return Object.entries(stockData)
      .filter(([key, stock]) => {
        const [stockMarket] = key.split('-')
        const stockCode = key.split('-')[1]
        
        if (filterCodes.length > 0) {
          return stockMarket === market && 
                 stock.current_quantity <= 0 && 
                 filterCodes.includes(stockCode)
        }
        return stockMarket === market && stock.current_quantity <= 0
      })
      .map(([key, stock]) => ({
        code: key.split('-')[1],
        ...stock
      }))
      .sort((a, b) => {
        // 使用最后交易日期进行排序
        const dateA = new Date(a.last_transaction_date || 0)
        const dateB = new Date(b.last_transaction_date || 0)
        return dateB - dateA
      })
  }

  return {
    calculateMarketStats,
    getHoldingStocks,
    getClosedStocks
  }
}

// 创建统计计算器实例
const statsCalculator = useStatsCalculator()

// 修改 marketStats 计算属性
const marketStats = computed(() => {
  return statsCalculator.calculateMarketStats(stockStats.value, searchForm.stockCodes || [])
})

// 修改获取持仓股票函数
const getHoldingStocks = (market) => {
  return statsCalculator.getHoldingStocks(stockStats.value, market, searchForm.stockCodes || [])
}

// 修改获取已清仓股票函数
const getClosedStocks = (market) => {
  return statsCalculator.getClosedStocks(stockStats.value, market, searchForm.stockCodes || [])
}

// 获取市场列表（按名称排序）
const getMarkets = computed(() => {
  return Object.keys(marketStats.value).sort();
});

// 格式化函数
const formatNumber = (value, decimals = 2) => {
  if (value === null || value === undefined) return '-'
  return Number(value).toLocaleString('zh-HK', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })
}

const formatRate = (value) => {
  if (value === null || value === undefined) return '-'
  return value.toFixed(2) + '%'
}

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).replace(/\//g, '-')
}

const getProfitClass = (value) => {
  if (!value) return ''
  return value > 0 ? 'text-success' : value < 0 ? 'text-danger' : ''
}

// 展开/收起控制
const isMarketExpanded = (market) => expandedMarkets.value.has(market)
const isHoldingGroupExpanded = (market) => expandedHoldingGroups.value.has(market)
const isClosedGroupExpanded = (market) => expandedClosedGroups.value.has(market)
const isStockExpanded = (market, code) => {
  const stockKey = `${market}-${code}`
  return expandedStocks.value.has(stockKey)
}

const toggleMarket = (market) => {
  if (expandedMarkets.value.has(market)) {
    // 收起所有相关的展开状态
    expandedMarkets.value.delete(market)
    expandedHoldingGroups.value.delete(market)
    expandedClosedGroups.value.delete(market)
    
    // 清除该市场下所有股票的展开状态
    const stocksInMarket = Object.keys(stockStats.value)
      .filter(key => key.startsWith(market))
    stocksInMarket.forEach(stockKey => {
      expandedStocks.value.delete(stockKey)
    })
  } else {
    // 展开市场和持仓股票组，但不展开已清仓股票组
    expandedMarkets.value.add(market)
    expandedHoldingGroups.value.add(market)
  }
}

const toggleHoldingGroup = (market) => {
  if (expandedHoldingGroups.value.has(market)) {
    expandedHoldingGroups.value.delete(market)
  } else {
    expandedHoldingGroups.value.add(market)
  }
}

const toggleClosedGroup = (market) => {
  if (expandedClosedGroups.value.has(market)) {
    expandedClosedGroups.value.delete(market)
  } else {
    expandedClosedGroups.value.add(market)
  }
}

const toggleStock = (market, code) => {
  const stockKey = `${market}-${code}`
  if (expandedStocks.value.has(stockKey)) {
    expandedStocks.value.delete(stockKey)
  } else {
    expandedStocks.value.add(stockKey)
  }
}

const expandAll = () => {
  Object.keys(marketStats.value).forEach(market => {
    expandedMarkets.value.add(market)
    expandedHoldingGroups.value.add(market)
  })
}

const collapseAll = () => {
  expandedMarkets.value.clear()
  expandedHoldingGroups.value.clear()
  expandedClosedGroups.value.clear()
}

// 搜索相关
const toggleSearch = () => {
  searchVisible.value = !searchVisible.value
}

const showToast = (message) => {
  const toast = new Toast(
    Object.assign(document.createElement('div'), {
      className: 'toast position-fixed top-0 end-0 m-3',
      innerHTML: `
        <div class="toast-header">
          <strong class="me-auto">提示</strong>
          <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
        </div>
        <div class="toast-body">${message}</div>
      `
    })
  )
  document.body.appendChild(toast._element)
  toast.show()
  setTimeout(() => {
    toast._element.remove()
  }, 3000)
}

const search = async () => {
  loading.value = true
  try {
    const params = {}
    if (searchForm.startDate) params.start_date = searchForm.startDate
    if (searchForm.endDate) params.end_date = searchForm.endDate
    if (searchForm.market) params.market = searchForm.market
    if (searchForm.stockCodes?.length > 0) params.stock_codes = searchForm.stockCodes
    
    const response = await axios.get('/api/profit/', { params })
    
    if (response.data.success) {
      stockStats.value = response.data.data.stock_stats || {}
      transactionDetails.value = response.data.data.transaction_details || {}
      
      // 清除所有展开状态
      expandedMarkets.value.clear()
      expandedHoldingGroups.value.clear()
      expandedClosedGroups.value.clear()
      expandedStocks.value.clear()
      
      // 默认展开所有市场和持仓股票组
      Object.keys(marketStats.value).forEach(market => {
        expandedMarkets.value.add(market)
        expandedHoldingGroups.value.add(market)
      })
    }
  } catch (error) {
    console.error('查询失败:', error)
    showToast('查询失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const resetSearch = () => {
  searchForm.startDate = ''
  searchForm.endDate = ''
  searchForm.market = ''
  searchForm.stockCodes = []
  search()
}

const refreshMarketValue = async () => {
  if (refreshLoading.value) return
  
  refreshLoading.value = true
  try {
    console.log('开始刷新市值...')
    const response = await axios.post('/api/profit/refresh_prices')
    console.log('收到后端响应:', response.data)
    
    if (response.data.success) {
      const { items, success_count, failed_count } = response.data.data
      
      // 更新持仓股票的现价和相关数据
      items.forEach(item => {
        const stockKey = `${item.market}-${item.code}`
        if (stockStats.value[stockKey]) {
          console.log(`更新股票 ${stockKey} 数据:`, item)
          stockStats.value[stockKey].current_price = item.current_price
          stockStats.value[stockKey].market_value = item.market_value
          stockStats.value[stockKey].holding_profit = item.holding_profit
          stockStats.value[stockKey].total_profit = item.total_profit
          stockStats.value[stockKey].profit_rate = item.profit_rate
        }
      })
      
      // 重新计算市场统计
      rawMarketStats.value = statsCalculator.calculateMarketStats(stockStats.value, searchForm.stockCodes || [])
      
      // 显示更新结果
      showToast(`市值更新完成：${success_count} 个成功，${failed_count} 个失败`)
    }
  } catch (error) {
    console.error('刷新市值失败:', error)
    showToast('刷新市值失败，请稍后重试')
  } finally {
    refreshLoading.value = false
  }
}

const addTransaction = () => {
  router.push('/transactions/add')
}

// 修改日期变更处理部分
const { handleBlur: dateInputBlur } = useDateInput()

// 日期处理
const startDateDisplayValue = ref('')
const endDateDisplayValue = ref('')

const handleStartDateInput = (event) => {
  const value = event.target.value
  startDateDisplayValue.value = value
  searchForm.startDate = value
}

const handleStartDateBlur = () => {
  if (!startDateDisplayValue.value) {
    searchForm.startDate = ''
    return
  }

  const value = startDateDisplayValue.value.trim()
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
    startDateDisplayValue.value = formattedDate
    searchForm.startDate = formattedDate
    // 如果开始日期大于结束日期，更新结束日期
    if (searchForm.endDate && formattedDate > searchForm.endDate) {
      searchForm.endDate = formattedDate
      endDateDisplayValue.value = formattedDate
    }
  }
}

const handleEndDateInput = (event) => {
  const value = event.target.value
  endDateDisplayValue.value = value
  searchForm.endDate = value
}

const handleEndDateBlur = () => {
  if (!endDateDisplayValue.value) {
    searchForm.endDate = ''
    return
  }

  const value = endDateDisplayValue.value.trim()
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
    endDateDisplayValue.value = formattedDate
    searchForm.endDate = formattedDate
    // 如果结束日期小于开始日期，更新开始日期
    if (searchForm.startDate && formattedDate < searchForm.startDate) {
      searchForm.startDate = formattedDate
      startDateDisplayValue.value = formattedDate
    }
  }
}

// 验证日期是否有效
const isValidDate = (date) => {
  return date instanceof Date && !isNaN(date)
}

// 处理后端返回的数据
const processTransactionDetails = (details) => {
  if (!details) return [];
  // 对交易明细按日期和创建时间降序排序
  return [...details].sort((a, b) => {
    // 先按交易日期排序
    const dateA = new Date(a.transaction_date);
    const dateB = new Date(b.transaction_date);
    if (dateA.getTime() !== dateB.getTime()) {
      return dateB.getTime() - dateA.getTime();
    }
    // 如果交易日期相同，按创建时间排序
    const createA = new Date(a.created_at || 0);
    const createB = new Date(b.created_at || 0);
    return createB.getTime() - createA.getTime();
  });
}

// 在 script setup 部分添加计算函数
const calculateHKDAmount = (detail) => {
  return detail.total_amount * detail.exchange_rate;
}

const calculateProfit = (detail) => {
  if (detail.transaction_type.toLowerCase() !== 'sell') return 0
  
  const sellAmount = Number(detail.total_amount)
  const costAmount = Number(detail.total_quantity) * Number(detail.prev_avg_cost)
  const fees = Number(detail.total_fees)
  
  return Number((sellAmount - costAmount - fees).toFixed(2))
}

// 在 script setup 部分添加计算盈亏率函数
const calculateProfitRate = (detail) => {
  if (detail.transaction_type.toLowerCase() !== 'sell') return 0
  
  const profit = calculateProfit(detail)
  const costAmount = Number(detail.total_quantity) * Number(detail.prev_avg_cost)
  
  return costAmount > 0 ? Number((profit / costAmount * 100).toFixed(2)) : 0
}

// 获取所有股票
const fetchStocks = async () => {
  try {
    const response = await axios.get('/api/stock/stocks')
    if (response.data.success) {
      allStocks.value = response.data.data.items
    }
  } catch (error) {
    console.error('获取股票列表失败:', error)
  }
}

// 添加交易明细排序函数
const sortTransactionDetails = (details) => {
  if (!details) return [];
  return [...details].sort((a, b) => {
    // 先按交易日期降序排序
    const dateA = new Date(a.transaction_date).getTime();
    const dateB = new Date(b.transaction_date).getTime();
    if (dateA !== dateB) {
      return dateB - dateA;
    }
    // 如果交易日期相同，按ID降序排序
    return b.id - a.id;
  });
}

// 初始化
onMounted(() => {
  fetchStocks()
  search()
})
</script>

<style scoped>
.card {
  margin: 1.5rem auto;
  max-width: 1400px;
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
  border-radius: 0.5rem;
  background-color: #fff;
}

.card-body {
  padding: 0.75rem !important;
}

.table-responsive {
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
  background-color: #ffffff;
}

.table {
  margin-bottom: 0;
  background-color: #ffffff;
}

.table > :first-child > tr:first-child > * {
  border-top: none;
}

.table > :last-child > tr:last-child > * {
  border-bottom: none;
}

.market-row {
  background-color: #f8f9fa;
}

.holding-group-row,
.closed-group-row {
  background-color: #f8f9fa;
}

.stock-row {
  background-color: #ffffff;
}

.stock-row:hover {
  background-color: #f8f9fa;
}

/* 层级缩进样式 */
/* 第一层级 - 市场行 */
.market-row td:first-child {
  padding-left: 0.1rem !important;
  position: relative;
  width: 40px;
}

/* 第二层级 - 持仓/已清仓分组 */
.holding-group-row td:first-child,
.closed-group-row td:first-child {
  padding-left: 0.5rem !important;
  position: relative;
  width: 40px;
}

.holding-group-row td:nth-child(2),
.closed-group-row td:nth-child(2) {
  padding-left: 2rem !important;/* 第二层级 - 修改缩进*/
}

/* 第三层级 - 股票行 */
.stock-row td:first-child {
  padding-left: 0.5rem !important;
  position: relative;
  width: 40px;
}

.stock-row td:nth-child(2) {
  padding-left: 1rem !important;/* 第三层级 - 修改缩进*/
}

/* 第四层级 - 交易明细 */
.transaction-details {
  padding-left: 5rem !important; /* 第四层级 - 修改缩进*/
  background-color: #ffffff;
  padding: 0.5rem;
  font-size: 0.75rem;  /* 12px */
}

.transaction-details .table {
  background-color: white;
  margin-bottom: 0;
}

.transaction-details th,
.transaction-details td {
  padding: 0.4rem 0.5rem;
  font-size: 0.75rem;  /* 12px */
  white-space: nowrap;
}

.transaction-details th {
  background-color: #f1f3f5;
  font-weight: 500;
  color: #495057;
}

.transaction-details td {
  vertical-align: middle;
}

.transaction-details tr:hover {
  background-color: #f8f9fa;
}

/* 交易明细列宽 持仓股票*/
.transaction-details .transaction-info {
  min-width: 50px;
  font-size: 0.75rem;  /* 12px */
}

.transaction-details .quantity-price {
  min-width: 60px;
  font-size: 0.75rem;  /* 12px */
}

.transaction-details .amount {
  min-width: 100px;
  font-size: 12px;
}

.transaction-details .cost {
  min-width: 80px;
  font-size: 12px;
}

.transaction-details .fees {
  min-width: 80px;
  font-size: 12px;
}

.transaction-details .profit {
  min-width: 80px;
  font-size: 12px;
}

.transaction-details .current-price {
  min-width: 100px;
  font-size: 12px;
}

.transaction-details .holding-value {
  min-width: 100px;
  font-size: 12px;
}

.transaction-details .total-profit {
  min-width: 100px;
  font-size: 12px;
}

.transaction-details .profit-rate {
  min-width: 100px;
  font-size: 12px;
}

/* 交易类型标签样式 */
.transaction-type-badge {
  display: inline-block;
  width: 30px;
  height: 16px;
  line-height: 15px;
  text-align: center;
  border-radius: 4px;
  font-size: 0.75rem;  /* 12px */
  font-weight: 450;
  margin: 0 6px;
}

.transaction-type-badge.buy {
  background-color: #e6071d;
  color: #ffffff;
}

.transaction-type-badge.sell {
  background-color: #549359;
  color: #ffffff;
}

.transaction-code {
  font-size: 0.675rem;  /* 14px */
  color: #6c757d;
  margin-left: 4px;
}

/* 按钮样式 */
.btn-sm {
  padding: 0.25rem 0.5rem;
  min-width: 28px;
  height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  color: #495057;
  transition: all 0.2s;
  margin: 2px;
  position: relative;
}

.btn-sm:hover {
  background: transparent;
}

.btn-sm:focus {
  box-shadow: none;
  outline: none;
}

.btn-sm .bi {
  font-size: 18px;
  width: 18px;
  height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease-in-out;
  position: relative;
  z-index: 2;
  font-weight: bold;
  stroke-width: 1px;
}

.rotate-90 {
  transform: rotate(90deg);
  color: #0d6efd !important;
}

/* 市场行按钮样式 */
.market-row .btn-sm {
  background: transparent;
  border: none;
}

.market-row .btn-sm .bi {
  font-size: 20px;
  width: 20px;
  height: 20px;
  font-weight: bold;
  transition: all 0.2s ease-in-out;
}

.market-row .btn-sm .bi-chevron-right {
  color: #495057;
}

/* 分组行按钮样式 */
.holding-group-row .btn-sm,
.closed-group-row .btn-sm {
  background: transparent;
  border: none;
  transform: translateX(0.8rem);
}

.holding-group-row .btn-sm .bi,
.closed-group-row .btn-sm .bi {
  font-size: 18px;
  width: 18px;
  height: 18px;
  font-weight: bold;
  transition: all 0.2s ease-in-out;
}

.holding-group-row .btn-sm .bi-chevron-right,
.closed-group-row .btn-sm .bi-chevron-right {
  color: #495057;
}

/* 股票行按钮样式 */
.stock-row .btn-sm {
  background: transparent;
  border: none;
  transform: translateX(1.2rem);
}

.stock-row .btn-sm .bi {
  font-size: 16px;
  width: 16px;
  height: 16px;
  font-weight: bold;
  transition: all 0.2s ease-in-out;
}

.stock-row .btn-sm .bi-chevron-right {
  color: #495057;
}

/* 按钮悬停效果 */
.btn-sm:hover .bi-chevron-right {
  color: #0d6efd;
}

.btn-sm:hover .rotate-90 {
  color: #0a58ca !important;
}

/* 交易明细表格样式 */
.transaction-details {
  background-color: #ffffff;
  padding: 0.5rem;
}

.transaction-details .table {
  margin-bottom: 0;
}

.transaction-details td {
  background-color: #ffffff;
  padding: 0.25rem 0.5rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  border-bottom: 1px solid #dee2e6;
  line-height: 1.2;
  vertical-align: middle;
  font-size: 12px;
}

.transaction-details tr:last-child td {
  border-bottom: none;
}

/* 交易明细行悬停效果 */
.transaction-details tr {
  transition: background-color 0.2s;
  height: 8px;
}

.transaction-details tr:hover td {
  background-color: #f8f9fa;
}

.transaction-details tr.selected td {
  background-color: #e9ecef;
}

/* 旋转动画 */
@keyframes bi-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.bi-spin {
  display: inline-block;
  animation: bi-spin 1s linear infinite;
}

.text-success {
  color: #198754 !important;
}

.text-danger {
  color: #dc3545 !important;
}

.table th {
  white-space: nowrap;
  font-size: 0.875rem;
}

.table td {
  font-size: 0.875rem;
  vertical-align: middle;
}

.small {
  font-size: 0.875rem;
}

/* 交易类型徽章样式 */
.transaction-type-badge {
  display: inline-block;
  width: 30px;
  height: 16px;
  line-height: 15px;
  text-align: center;
  border-radius: 4px;
  font-size: 0.75rem;  /* 12px */
  font-weight: 450;
  margin: 0 6px;
}

.transaction-type-badge.buy {
  background-color: #e6071d;
  color: #ffffff;
}

.transaction-type-badge.sell {
  background-color: #549359;
  color: #ffffff;
}

/* 交易编号样式 */
.transaction-code {
  font-size: 0.675rem;  /* 14px */
  color: #6c757d;
  margin-left: 4px;
}

/* 交易信息列样式 */
.transaction-info {
  min-width: 180px;
  font-size: 0.75rem;  /* 12px */
}

/* 数量@单价列样式 */
.quantity-price {
  min-width: 60px;
  padding-left: 1rem !important;
  text-align: left !important;
  font-size: 12px;
}

/* 金额列样式 */
.amount {
  min-width: 100px;
  font-size: 12px;
}

/* 单笔成本列样式 */
.cost {
  min-width: 80px;
  font-size: 12px;
}

/* 费用列样式 */
.fees {
  min-width: 80px;
  font-size: 12px;
}

.profit {
  min-width: 80px;
  font-size: 12px;
} 

.current-price {
  min-width: 100px;
  font-size: 12px;
} 

.holding-value {
  min-width: 100px;
  font-size: 12px;
} 

.total-profit {
  min-width: 100px;
  font-size: 12px;
}  

.profit-rate {
  min-width: 100px;
  font-size: 12px;
}

/* 统计行样式 */
.holding-stats-row,
.closed-stats-row {
  background-color: #f8f9fa;
  font-size: 0.875rem;
}

.holding-stats-row td,
.closed-stats-row td {
  padding-left: 2rem !important;
  color: #495057;
}

.holding-stats-row strong,
.closed-stats-row strong {
  color: #495057;
  font-weight: 500;
}

.stock-selector-sm :deep(.selected-items) {
  min-height: calc(1.5em + 0.5rem + 2px);
  max-height: calc(2.5em + 0.5rem + 2px);
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
}

.stock-selector-sm :deep(.selected-tag) {
  font-size: 0.75rem;
  padding: 0.125rem 0.375rem;
  max-width: 150px;
}

.stock-selector-sm :deep(.search-input) {
  height: 1.25rem;
  min-width: 40px;
  font-size: 0.875rem;
}

.stock-selector-sm :deep(.dropdown-menu) {
  min-width: 200px;
}

.company-name {
  display: block;
  font-size: 14px;
  color: #64a7e3;
  margin-top: 2px;
}
</style> 
