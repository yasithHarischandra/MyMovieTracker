<script setup>
import { ref, onMounted } from 'vue'
import client from '@/api/client'
import { useToastStore } from '@/stores/toast'
import MovieStatsPanel from '@/components/dashboard/MovieStatsPanel.vue'
import SeriesStatsPanel from '@/components/dashboard/SeriesStatsPanel.vue'
import InProgressWidget from '@/components/dashboard/InProgressWidget.vue'
import ActivityFeed from '@/components/dashboard/ActivityFeed.vue'

const toast = useToastStore()
const loading = ref(true)
const dashboardData = ref({ stats: {}, recent_activity: [], in_progress: [] })

const loadDashboard = async () => {
  loading.value = true
  try {
    const data = await client.get('/dashboard')
    dashboardData.value = data
  } catch (err) {
    toast.error('Failed to load dashboard data')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadDashboard()
})
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
    
    <div v-if="loading" class="flex justify-center items-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent"></div>
    </div>
    
    <template v-else>
      <!-- Stats Row 1: Movies (1 col) + Series (2 cols) -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <MovieStatsPanel :stats="dashboardData.stats?.movies" />
        <SeriesStatsPanel :stats="dashboardData.stats?.series" />
      </div>

      <!-- Content Row 2: Recent Activity (2 cols) + In Progress (1 col) -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
        <ActivityFeed :activities="dashboardData.recent_activity" class="lg:col-span-2" />
        <div class="lg:col-span-1 space-y-6 lg:sticky lg:top-24">
          <InProgressWidget :shows="dashboardData.in_progress" @refresh="loadDashboard" />
          
          <!-- Quick Actions / Sync -->
          <div class="bg-surface border border-gray-800 rounded-xl p-5 shadow-sm text-center">
             <RouterLink :to="{ name: 'search' }" class="btn-primary w-full flex items-center justify-center gap-2">
               <span class="text-xl">🔍</span> Find Media
             </RouterLink>
          </div>
        </div>
      </div>
    </template>

  </div>
</template>
