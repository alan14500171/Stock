<template>
  <div class="home-container" data-testid="home-container">
    <div class="content-wrapper">
      <div class="row">
        <div class="col-12 mb-4">
          <h2 class="section-title" data-testid="home-section-title">快速操作</h2>
          <div class="row g-4">
            <!-- 盈利统计卡片 -->
            <div class="col-md-6">
              <div class="card h-100" data-testid="profit-stats-card">
                <div class="card-body">
                  <h5 class="card-title" data-testid="profit-stats-title">
                    <i class="bi bi-graph-up text-primary"></i>
                    盈利统计
                  </h5>
                  <p class="card-text">查看您的交易盈亏情况，分析投资表现。</p>
                  <router-link to="/profit/stats" class="btn btn-primary" data-testid="view-profit-stats-btn">
                    查看统计
                  </router-link>
                </div>
              </div>
            </div>

            <!-- 交易记录卡片 -->
            <div class="col-md-6">
              <div class="card h-100" data-testid="transactions-card">
                <div class="card-body">
                  <h5 class="card-title" data-testid="transactions-title">
                    <i class="bi bi-journal-text text-success"></i>
                    交易记录
                  </h5>
                  <p class="card-text">管理您的所有交易记录，添加新的交易。</p>
                  <div class="btn-group">
                    <router-link to="/transaction/list" class="btn btn-success" data-testid="view-transactions-btn">
                      查看记录
                    </router-link>
                    <router-link to="/transaction/add" class="btn btn-outline-success" data-testid="add-transaction-btn">
                      添加交易
                    </router-link>
                  </div>
                </div>
              </div>
            </div>

            <!-- 股票管理卡片 -->
            <div class="col-md-6">
              <div class="card h-100" data-testid="stocks-card">
                <div class="card-body">
                  <h5 class="card-title" data-testid="stocks-title">
                    <i class="bi bi-briefcase text-info"></i>
                    股票管理
                  </h5>
                  <p class="card-text">管理您的股票列表，添加新的股票。</p>
                  <router-link to="/stock" class="btn btn-info text-white" data-testid="manage-stocks-btn">
                    管理股票
                  </router-link>
                </div>
              </div>
            </div>

            <!-- 汇率管理卡片 -->
            <div class="col-md-6">
              <div class="card h-100" data-testid="exchange-rates-card">
                <div class="card-body">
                  <h5 class="card-title" data-testid="exchange-rates-title">
                    <i class="bi bi-currency-exchange text-warning"></i>
                    汇率管理
                  </h5>
                  <p class="card-text">更新和管理港币、美元等货币汇率。</p>
                  <router-link to="/exchange/rate" class="btn btn-warning text-white" data-testid="manage-exchange-rates-btn">
                    管理汇率
                  </router-link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// 无需额外的逻辑
</script>

<style scoped>
.home-container {
  padding: 20px;
  min-height: calc(100vh - 56px);
  background-color: #f8f9fa;
}

.content-wrapper {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 500;
  margin-bottom: 1.5rem;
  color: #333;
}

.card {
  border: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: transform 0.2s, box-shadow 0.2s;
}

.card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.card-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.25rem;
  margin-bottom: 1rem;
}

.card-title i {
  font-size: 1.5rem;
}

.card-text {
  color: #6c757d;
  margin-bottom: 1.5rem;
}

.btn-group {
  display: flex;
  gap: 0.5rem;
}

.btn {
  padding: 0.5rem 1rem;
  font-weight: 500;
}

@media (max-width: 768px) {
  .content-wrapper {
    padding: 0 15px;
  }

  .section-title {
    font-size: 1.25rem;
    margin-bottom: 1rem;
  }

  .card-title {
    font-size: 1.1rem;
  }

  .card-text {
    font-size: 0.9rem;
  }
}
</style> 