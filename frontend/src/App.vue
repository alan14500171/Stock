<template>
  <div class="app-container">
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
      <div class="container">
        <router-link class="navbar-brand" to="/">股票交易系统</router-link>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav">
            <li class="nav-item">
              <router-link class="nav-link" :to="{name: 'ProfitStats'}">盈利统计</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" :to="{name: 'TransactionList'}">交易记录</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" :to="{name: 'ExchangeRateManager'}">汇率管理</router-link>
            </li>
            <li class="nav-item">
              <router-link class="nav-link" :to="{name: 'StockManager'}">股票管理</router-link>
            </li>
          </ul>
        </div>
      </div>
    </nav>

    <div class="container mt-4">
      <router-view></router-view>
    </div>
  </div>
</template>

<script setup>
// 组件逻辑
</script>

<style>
.app-container {
  min-height: 100vh;
  background-color: #f8f9fa;
}

.navbar {
  margin-bottom: 20px;
}
</style> 