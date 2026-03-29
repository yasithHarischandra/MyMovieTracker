<script setup>
import { ref, onMounted } from 'vue'
import client from '@/api/client'
import { useToastStore } from '@/stores/toast'
import PosterCard from '@/components/common/PosterCard.vue'

const inProgress = ref([])
const loading = ref(true)
const toast = useToastStore()

onMounted(async () => {
  try {
    inProgress.value = await client.get('/shows/in-progress')
  } catch (err) {
    toast.error('Failed to load in-progress shows')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="flex items-center justify-between pl-4 border-l-4 border-primary mb-8">
      <h1 class="text-3xl font-extrabold text-white tracking-tight">In Progress</h1>
      <span class="bg-surface border border-gray-800 px-3 py-1 rounded-full text-secondary font-mono text-sm">
        {{ inProgress.length }} Shows
      </span>
    </div>

    <div v-if="loading" class="flex justify-center py-20">
      <div class="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent"></div>
    </div>

    <div v-else-if="inProgress.length === 0" class="text-center py-24 bg-surface rounded-2xl border border-gray-800">
      <span class="text-6xl mb-4 block">📺</span>
      <h3 class="text-xl font-bold text-white">All caught up!</h3>
      <p class="text-gray-500 mt-2 max-w-sm mx-auto">You have no uncompleted series in your library. Search and add a new TV show to start tracking.</p>
      <RouterLink :to="{ name: 'search', query: { type: 'shows' } }" class="btn-primary inline-flex mt-6">
        Search TV Shows
      </RouterLink>
    </div>

    <div v-else class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
      <RouterLink 
        v-for="show in inProgress" 
        :key="show.id" 
        :to="{ name: 'show-detail', params: { id: show.id } }"
        class="bg-surface border border-gray-800 rounded-xl overflow-hidden hover:-translate-y-1 hover:shadow-2xl transition-all duration-300 group flex flex-col"
      >
        <PosterCard :src="show.poster_path" :tmdbId="show.tmdb_id" :alt="show.name" ratio="aspect-[3/4]" />
        
        <div class="p-4 flex-grow flex flex-col justify-between space-y-3">
          <h3 class="font-bold text-white text-lg line-clamp-1 group-hover:text-primary transition-colors" :title="show.name">{{ show.name }}</h3>
          
          <div class="space-y-2">
            <div class="flex justify-between text-sm text-gray-400">
              <span>{{ show.remaining_episodes }} eps left</span>
              <span class="font-mono text-amber-500">{{ show.remaining_hours }}h</span>
            </div>
            
            <div class="flex items-center gap-2">
              <div class="w-full bg-gray-900 rounded-full h-2 overflow-hidden border border-gray-800">
                <div class="bg-secondary h-full rounded-full transition-all" :style="`width: ${show.progress_pct}%`"></div>
              </div>
              <span class="text-xs font-mono font-bold text-gray-300 w-8 text-right">{{ Math.round(show.progress_pct) }}%</span>
            </div>
          </div>
        </div>
      </RouterLink>
    </div>
  </div>
</template>
