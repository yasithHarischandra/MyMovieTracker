<script setup>
import { useToastStore } from '@/stores/toast'
import { PhXCircle, PhCheckCircle, PhInfo, PhX } from '@phosphor-icons/vue'

const toastStore = useToastStore()

const getIcon = (type) => {
  switch (type) {
    case 'error': return PhXCircle
    case 'success': return PhCheckCircle
    default: return PhInfo
  }
}

const getColorClass = (type) => {
  switch (type) {
    case 'error': return 'bg-red-500/10 border-red-500/50 text-red-500'
    case 'success': return 'bg-accent/10 border-accent/50 text-accent'
    default: return 'bg-secondary/10 border-secondary/50 text-secondary'
  }
}
</script>

<template>
  <div class="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
    <TransitionGroup name="toast">
      <div 
        v-for="toast in toastStore.toasts" 
        :key="toast.id"
        :class="['flex items-center gap-3 px-4 py-3 rounded-lg border backdrop-blur-md shadow-lg min-w-[300px]', getColorClass(toast.type)]"
      >
        <component :is="getIcon(toast.type)" weight="fill" class="w-5 h-5 flex-shrink-0" />
        <span class="text-sm font-medium flex-grow">{{ toast.message }}</span>
        <button @click="toastStore.remove(toast.id)" class="text-gray-400 hover:text-white transition-colors">
          <PhX weight="bold" class="w-4 h-4" />
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}
.toast-leave-to {
  opacity: 0;
  transform: translateY(20px);
}
</style>
