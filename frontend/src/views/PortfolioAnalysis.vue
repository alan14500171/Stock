<template>
  <div class="container-fluid" v-permission="'portfolio:analysis:view'">
    <div class="row mb-4">
      <div class="col-12">
        <div class="card">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h5 class="mb-0">投资组合分析</h5>
            <div class="btn-group">
              <button 
                class="btn btn-sm" 
                :class="timeRange === '1m' ? 'btn-primary' : 'btn-outline-primary'"
                @click="changeTimeRange('1m')"
              >
                1个月
              </button>
              <button 
                class="btn btn-sm" 
                :class="timeRange === '3m' ? 'btn-primary' : 'btn-outline-primary'"
                @click="changeTimeRange('3m')"
              >
                3个月
              </button>
              <button 
                class="btn btn-sm" 
                :class="timeRange === '6m' ? 'btn-primary' : 'btn-outline-primary'"
                @click="changeTimeRange('6m')"
              >
                6个月
              </button>
              <button 
                class="btn btn-sm" 
                :class="timeRange === '1y' ? 'btn-primary' : 'btn-outline-primary'"
                @click="changeTimeRange('1y')"
              >
                1年
              </button>
              <button 
                class="btn btn-sm" 
                :class="timeRange === 'all' ? 'btn-primary' : 'btn-outline-primary'"
                @click="changeTimeRange('all')"
              >
                全部
              </button>
            </div>
          </div>
          <div class="card-body">
            <div class="chart-container" style="position: relative; height:400px;">
              <canvas id="portfolioPerformanceChart"></canvas>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="row mb-4">
      <div class="col-md-6">
        <div class="card h-100">
          <div class="card-header">
            <h5 class="mb-0">行业分布</h5>
          </div>
          <div class="card-body">
            <div class="chart-container" style="position: relative; height:300px;">
              <canvas id="sectorChart"></canvas>
            </div>
          </div>
        </div>
      </div>
      
      <div class="col-md-6">
        <div class="card h-100">
          <div class="card-header">
            <h5 class="mb-0">风险分析</h5>
          </div>
          <div class="card-body">
            <div class="row">
              <div class="col-md-6 mb-3">
                <div class="card bg-light">
                  <div class="card-body p-3">
                    <h6 class="card-title text-muted mb-2">波动率</h6>
                    <h3 class="mb-0">{{ formatPercent(volatility) }}</h3>
                    <small class="text-muted">年化标准差</small>
                  </div>
                </div>
              </div>
              <div class="col-md-6 mb-3">
                <div class="card bg-light">
                  <div class="card-body p-3">
                    <h6 class="card-title text-muted mb-2">夏普比率</h6>
                    <h3 class="mb-0">{{ formatNumber(sharpeRatio, 2) }}</h3>
                    <small class="text-muted">风险调整后收益</small>
                  </div>
                </div>
              </div>
              <div class="col-md-6 mb-3">
                <div class="card bg-light">
                  <div class="card-body p-3">
                    <h6 class="card-title text-muted mb-2">最大回撤</h6>
                    <h3 class="mb-0 text-danger">{{ formatPercent(maxDrawdown) }}</h3>
                    <small class="text-muted">历史最大跌幅</small>
                  </div>
                </div>
              </div>
              <div class="col-md-6 mb-3">
                <div class="card bg-light">
                  <div class="card-body p-3">
                    <h6 class="card-title text-muted mb-2">贝塔系数</h6>
                    <h3 class="mb-0">{{ formatNumber(beta, 2) }}</h3>
                    <small class="text-muted">相对市场波动</small>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="row">
      <div class="col-12">
        <div class="card">
          <div class="card-header">
            <h5 class="mb-0">投资组合表现</h5>
          </div>
          <div class="card-body p-0">
            <div class="table-responsive">
              <table class="table table-hover align-middle mb-0">
                <thead class="table-light">
                  <tr>
                    <th>时间段</th>
                    <th>投资组合收益</th>
                    <th>基准收益 (恒生指数)</th>
                    <th>超额收益</th>
                    <th>年化收益率</th>
                    <th>波动率</th>
                    <th>夏普比率</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="period in performancePeriods" :key="period.id">
                    <td>{{ period.name }}</td>
                    <td :class="getProfitLossClass(period.return)">
                      {{ formatPercent(period.return) }}
                    </td>
                    <td :class="getProfitLossClass(period.benchmarkReturn)">
                      {{ formatPercent(period.benchmarkReturn) }}
                    </td>
                    <td :class="getProfitLossClass(period.excessReturn)">
                      {{ formatPercent(period.excessReturn) }}
                    </td>
                    <td :class="getProfitLossClass(period.annualizedReturn)">
                      {{ formatPercent(period.annualizedReturn) }}
                    </td>
                    <td>{{ formatPercent(period.volatility) }}</td>
                    <td>{{ formatNumber(period.sharpeRatio, 2) }}</td>
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