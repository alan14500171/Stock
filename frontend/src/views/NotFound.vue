<template>
  <div class="not-found-container">
    <div class="not-found-content">
      <h1>404</h1>
      <h2>页面未找到</h2>
      <p>抱歉，您访问的页面不存在或已被移除。</p>
      <router-link to="/" class="btn btn-primary">返回首页</router-link>
    </div>
  </div>
</template>

<script setup>
// 404页面不需要特殊逻辑
</script>

<style scoped>
.not-found-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 80vh;
  text-align: center;
}

.not-found-content {
  max-width: 500px;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  background-color: #fff;
}

h1 {
  font-size: 6rem;
  margin: 0;
  color: #e74c3c;
}

h2 {
  font-size: 2rem;
  margin: 10px 0 20px;
  color: #333;
}

p {
  margin-bottom: 30px;
  color: #666;
}

.btn {
  padding: 10px 20px;
  font-size: 1rem;
}
</style> 