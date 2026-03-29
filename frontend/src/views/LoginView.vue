<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { PhSignIn } from '@phosphor-icons/vue'

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const router = useRouter()
const authStore = useAuthStore()

const handleLogin = async () => {
  if (!username.value || !password.value) {
    error.value = 'Please enter both username and password'
    return
  }

  error.value = ''
  loading.value = true

  const success = await authStore.login(username.value, password.value)
  
  if (success) {
    router.push({ name: 'dashboard' })
  } else {
    error.value = authStore.error || 'Invalid credentials'
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex flex-col justify-center items-center py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
    <!-- Cinematic background glow -->
    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[600px] bg-primary/20 blur-[120px] rounded-full pointer-events-none"></div>

    <div class="max-w-md w-full space-y-8 bg-surface/80 backdrop-blur-xl p-8 rounded-2xl border border-gray-800 shadow-2xl z-10">
      <div>
        <div class="flex justify-center flex-col items-center">
          <span class="text-6xl mb-4">🎬</span>
          <h2 class="text-center text-3xl font-extrabold text-white tracking-tight">CineTrack </h2>
        </div>
        <p class="mt-2 text-center text-sm text-gray-400">Sign in to your personal media library</p>
      </div>
      
      <form class="mt-8 space-y-6" @submit.prevent="handleLogin">
        <div class="rounded-md space-y-4">
          <div>
            <label for="username" class="sr-only">Username</label>
            <input 
              id="username" 
              name="username" 
              type="text" 
              required 
              v-model="username"
              class="appearance-none relative block w-full input-field" 
              placeholder="Username" 
            />
          </div>
          <div>
            <label for="password" class="sr-only">Password</label>
            <input 
              id="password" 
              name="password" 
              type="password" 
              required 
              v-model="password"
              class="appearance-none relative block w-full input-field" 
              placeholder="Password" 
            />
          </div>
        </div>

        <div v-if="error" class="text-red-400 text-sm bg-red-400/10 p-3 rounded-lg border border-red-400/20 text-center">
          {{ error }}
        </div>

        <div>
          <button 
            type="submit" 
            :disabled="loading"
            class="group relative w-full flex justify-center btn-primary"
            :class="{ 'opacity-75 cursor-wait': loading }"
          >
            <span class="absolute left-0 inset-y-0 flex items-center pl-3">
              <PhSignIn class="h-5 w-5 text-indigo-300 group-hover:text-indigo-200" aria-hidden="true" />
            </span>
            {{ loading ? 'Signing in...' : 'Sign In' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
