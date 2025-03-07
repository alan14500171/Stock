<template>
  <div class="message-container">
    <transition-group name="message-fade">
      <div 
        v-for="message in messages" 
        :key="message.id" 
        class="message-toast" 
        :class="[
          `bg-${message.type}`, 
          { 'show': message.show }
        ]"
        @click="removeMessage(message.id)"
      >
        <div class="message-content">
          <i 
            class="bi me-2" 
            :class="{
              'bi-check-circle-fill': message.type === 'success',
              'bi-exclamation-triangle-fill': message.type === 'warning',
              'bi-info-circle-fill': message.type === 'info',
              'bi-x-circle-fill': message.type === 'danger'
            }"
          ></i>
          <span>{{ message.text }}</span>
        </div>
      </div>
    </transition-group>
  </div>
</template>

<script setup>
import { useMessage } from '@/composables/useMessage'

const { messages, removeMessage } = useMessage()
</script>

<style scoped>
.message-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  pointer-events: none;
}

.message-toast {
  margin-bottom: 10px;
  padding: 12px 20px;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  color: white;
  max-width: 350px;
  pointer-events: auto;
  cursor: pointer;
  opacity: 0;
  transform: translateY(-20px);
  transition: all 0.3s ease;
}

.message-toast.show {
  opacity: 1;
  transform: translateY(0);
}

.message-content {
  display: flex;
  align-items: center;
}

.message-fade-enter-active,
.message-fade-leave-active {
  transition: all 0.3s ease;
}

.message-fade-enter-from,
.message-fade-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}
</style> 