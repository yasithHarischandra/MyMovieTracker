<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { PhFilmStrip, PhMagnifyingGlass, PhHourglass, PhClockCounterClockwise, PhSignOut, PhUserCircle, PhGear, PhCalendar } from '@phosphor-icons/vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const navLinks = [
  { name: 'Dashboard', to: { name: 'dashboard' }, icon: PhFilmStrip },
  { name: 'Search', to: { name: 'search' }, icon: PhMagnifyingGlass },
  { name: 'In Progress', to: { name: 'in-progress' }, icon: PhHourglass },
  { name: 'Upcoming', to: { name: 'upcoming' }, icon: PhCalendar },
  { name: 'History', to: { name: 'history' }, icon: PhClockCounterClockwise },
  { name: 'Settings', to: { name: 'settings' }, icon: PhGear },
]

const isActive = (pathName) => route.name === pathName

const logout = () => {
  authStore.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <nav v-if="authStore.isAuthenticated" class="sticky top-0 z-40 bg-background/80 backdrop-blur-md border-b border-gray-800">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16">
        
        <!-- Logo & Navigation Links -->
        <div class="flex items-center gap-8">
          <RouterLink :to="{ name: 'dashboard' }" class="flex items-center gap-2 group">
            <span class="text-2xl transition-transform group-hover:scale-110">🎬</span>
            <span class="font-bold text-lg tracking-tight text-white">CineTrack</span>
          </RouterLink>
          
          <div class="hidden md:flex items-center space-x-1">
            <RouterLink 
              v-for="link in navLinks" 
              :key="link.name" 
              :to="link.to"
              :class="[
                'flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                isActive(link.to.name) ? 'text-primary bg-primary/10' : 'text-gray-400 hover:text-white hover:bg-white/5'
              ]"
            >
              <component :is="link.icon" :weight="isActive(link.to.name) ? 'fill' : 'regular'" class="w-4 h-4" />
              {{ link.name }}
            </RouterLink>
          </div>
        </div>

        <!-- Right Side: User Menu -->
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2 text-sm text-gray-400">
            <PhUserCircle weight="fill" class="w-6 h-6 text-gray-500" />
            <span class="hidden sm:block font-medium">{{ authStore.user?.username || 'Admin' }}</span>
          </div>
          <button @click="logout" class="p-2 text-gray-500 hover:text-red-400 transition-colors" title="Sign Out">
            <PhSignOut weight="bold" class="w-5 h-5" />
          </button>
        </div>

      </div>
    </div>
  </nav>
</template>
