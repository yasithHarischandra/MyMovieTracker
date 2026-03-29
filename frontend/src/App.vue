<script setup>
import { RouterView } from 'vue-router'
import AppNav from '@/components/common/AppNav.vue'
import AppToast from '@/components/common/AppToast.vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <AppNav v-if="authStore.isAuthenticated" />
    <main class="flex-grow">
      <RouterView />
    </main>
    <AppToast />
  </div>
</template>


