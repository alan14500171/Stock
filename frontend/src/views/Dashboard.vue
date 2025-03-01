<template>
  <div class="container-fluid" v-permission="'dashboard:view'" data-testid="dashboard-container">
    <div class="row mb-4">
      <div class="col-md-6 col-lg-3 mb-3">
        <div class="card h-100" data-testid="portfolio-overview-card">
          <div class="card-body">
            <h5 class="card-title" data-testid="portfolio-overview-title">持仓总览</h5>
            <div class="d-flex justify-content-between align-items-center mt-3">
              <div>
                <h3 class="mb-0" data-testid="total-value">{{ formatCurrency(totalValue) }}</h3>
                <small class="text-muted">当前总市值</small>
              </div>
              <div class="text-end">
                <div :class="['fs-5', getProfitLossClass(totalProfitLoss)]" data-testid="total-profit-loss">
                  {{ formatProfitLoss(totalProfitLoss) }}
                </div>
                <small class="text-muted">总盈亏</small>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="col-md-6 col-lg-3 mb-3">
        <div class="card h-100" data-testid="today-change-card">
          <div class="card-body">
            <h5 class="card-title" data-testid="today-change-title">今日变动</h5>
            <div class="d-flex justify-content-between align-items-center mt-3">
              <div>
                <h3 class="mb-0" data-testid="today-change-amount">{{ formatCurrency(todayChange) }}</h3>
                <small class="text-muted">金额变动</small>
              </div>
              <div class="text-end">
                <div :class="['fs-5', getProfitLossClass(todayChangePercent)]" data-testid="today-change-percent">
                  {{ formatPercent(todayChangePercent) }}
                </div>
                <small class="text-muted">百分比</small>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="col-md-6 col-lg-3 mb-3">
        <div class="card h-100" data-testid="holdings-count-card">
          <div class="card-body">
            <h5 class="card-title" data-testid="holdings-count-title">持仓数量</h5>
            <div class="d-flex justify-content-between align-items-center mt-3">
              <div>
                <h3 class="mb-0" data-testid="total-stocks">{{ totalStocks }}</h3>
                <small class="text-muted">股票数量</small>
              </div>
              <div class="text-end">
                <div class="fs-5" data-testid="total-transactions">{{ totalTransactions }}</div>
                <small class="text-muted">交易记录</small>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="col-md-6 col-lg-3 mb-3">
        <div class="card h-100" data-testid="market-distribution-card">
          <div class="card-body">
            <h5 class="card-title" data-testid="market-distribution-title">市场分布</h5>
            <div class="d-flex justify-content-between align-items-center mt-3">
              <div>
                <h3 class="mb-0" data-testid="hk-value">{{ formatCurrency(hkValue) }}</h3>
                <small class="text-muted">港股市值</small>
              </div>
              <div class="text-end">
                <h3 class="mb-0" data-testid="us-value">{{ formatCurrency(usValue) }}</h3>
                <small class="text-muted">美股市值</small>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="row mb-4">
      <div class="col-lg-8 mb-3">
        <div class="card h-100" data-testid="holdings-distribution-card">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h5 class="mb-0" data-testid="holdings-distribution-title">持仓分布</h5>
            <div class="btn-group" data-testid="chart-view-toggle">
              <button 
                class="btn btn-sm" 
                :class="chartView === 'value' ? 'btn-primary' : 'btn-outline-primary'"
                @click="chartView = 'value'"
                data-testid="value-view-btn"
              >
                市值
              </button>
              <button 
                class="btn btn-sm" 
                :class="chartView === 'profit' ? 'btn-primary' : 'btn-outline-primary'"
                @click="chartView = 'profit'"
                data-testid="profit-view-btn"
              >
                盈亏
              </button>
            </div>
          </div>
          <div class="card-body">
            <div class="chart-container" style="position: relative; height:300px;" data-testid="portfolio-chart-container">
              <canvas id="portfolioChart"></canvas>
            </div>
          </div>
        </div>
      </div>
      
      <div class="col-lg-4 mb-3">
        <div class="card h-100" data-testid="market-ratio-card">
          <div class="card-header">
            <h5 class="mb-0" data-testid="market-ratio-title">市场占比</h5>
          </div>
          <div class="card-body">
            <div class="chart-container" style="position: relative; height:300px;" data-testid="market-chart-container">
              <canvas id="marketChart"></canvas>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="row">
      <div class="col-12">
        <div class="card" data-testid="holdings-detail-card">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h5 class="mb-0" data-testid="holdings-detail-title">持仓明细</h5>
            <button class="btn btn-sm btn-outline-primary" @click="refreshData" data-testid="refresh-data-btn">
              <i class="bi bi-arrow-clockwise me-1"></i>刷新数据
            </button>
          </div>
          <div class="card-body p-0">
            <div class="table-responsive" data-testid="holdings-table-container">
              <table class="table table-hover align-middle mb-0">
                <thead class="table-light">
                  <tr>
                    <th data-testid="stock-header">股票</th>
                    <th data-testid="quantity-header">持仓数量</th>
                    <th data-testid="avg-cost-header">平均成本</th>
                    <th data-testid="current-price-header">当前价格</th>
                    <th data-testid="market-value-header">市值</th>
                    <th data-testid="profit-loss-header">盈亏</th>
                    <th data-testid="profit-loss-percent-header">盈亏比例</th>
                    <th data-testid="today-change-header">今日变动</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="position in positions" :key="position.stock_id" :data-testid="'position-row-' + position.stock_id">
                    <td>
                      <div class="d-flex align-items-center">
                        <span class="badge me-2" :class="position.market === 'HK' ? 'bg-danger' : 'bg-primary'" :data-testid="'market-badge-' + position.stock_id">
                          {{ position.market }}
                        </span>
                        <div>
                          <div class="fw-bold" :data-testid="'stock-code-' + position.stock_id">{{ position.stock_code }}</div>
                          <small class="text-muted" :data-testid="'stock-name-' + position.stock_id">{{ position.stock_name }}</small>
                        </div>
                      </div>
                    </td>
                    <td :data-testid="'quantity-' + position.stock_id">{{ formatNumber(position.quantity) }}</td>
                    <td :data-testid="'avg-cost-' + position.stock_id">{{ formatPrice(position.avg_cost, position.market) }}</td>
                    <td :data-testid="'current-price-' + position.stock_id">{{ formatPrice(position.current_price, position.market) }}</td>
                    <td :data-testid="'market-value-' + position.stock_id">{{ formatCurrency(position.market_value) }}</td>
                    <td :class="getProfitLossClass(position.profit_loss)" :data-testid="'profit-loss-' + position.stock_id">
                      {{ formatCurrency(position.profit_loss) }}
                    </td>
                    <td :class="getProfitLossClass(position.profit_loss_percent)" :data-testid="'profit-loss-percent-' + position.stock_id">
                      {{ formatPercent(position.profit_loss_percent) }}
                    </td>
                    <td :class="getProfitLossClass(position.today_change_percent)" :data-testid="'today-change-percent-' + position.stock_id">
                      {{ formatPercent(position.today_change_percent) }}
                    </td>
                  </tr>
                  <tr v-if="positions.length === 0">
                    <td colspan="8" class="text-center py-3">
                      <div class="text-muted" data-testid="no-positions-message">暂无持仓数据</div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template> 