import { defineStore } from 'pinia'

export const useToastStore = defineStore('toast', {
  state: () => ({
    toasts: []
  }),
  actions: {
    add(message, type = 'info', duration = 3000) {
      const id = Date.now()
      this.toasts.push({ id, message, type })
      setTimeout(() => {
        this.remove(id)
      }, duration)
    },
    remove(id) {
      this.toasts = this.toasts.filter(t => t.id !== id)
    },
    success(message, duration) {
      this.add(message, 'success', duration)
    },
    error(message, duration = 5000) {
      this.add(message, 'error', duration)
    }
  }
})
