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
          <ul class="navbar-nav ms-auto">
            <li class="nav-item">
              <a href="#" class="nav-link" @click.prevent="handleLogout">
                <i class="fas fa-sign-out-alt"></i> 退出登录
              </a>
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
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()

const handleLogout = async () => {
  try {
    const response = await axios.get('/auth/logout')
    if (response.data.success) {
      // 使用后端返回的重定向 URL 进行跳转
      window.location.href = response.data.redirect
    }
  } catch (error) {
    console.error('退出登录失败:', error)
  }
}
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