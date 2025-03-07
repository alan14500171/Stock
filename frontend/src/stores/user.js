import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: JSON.parse(localStorage.getItem('user') || '{}'),
    isLoggedIn: localStorage.getItem('isLoggedIn') === 'true'
  }),
  
  actions: {
    setToken(token) {
      this.token = token
      localStorage.setItem('token', token)
    },
    
    setUser(user) {
      this.user = user
      localStorage.setItem('user', JSON.stringify(user))
    },
    
    setLoggedIn(status) {
      this.isLoggedIn = status
      localStorage.setItem('isLoggedIn', status)
    },
    
    clearUserInfo() {
      this.token = ''
      this.user = {}
      this.isLoggedIn = false
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      localStorage.removeItem('isLoggedIn')
    }
  }
}) 