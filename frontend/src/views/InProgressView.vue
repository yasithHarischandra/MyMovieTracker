<script setup>
import { ref, onMounted, watch } from 'vue'
import client from '@/api/client'
import { useToastStore } from '@/stores/toast'
import PosterCard from '@/components/common/PosterCard.vue'
import { PhArchiveBox, PhArrowUUpLeft, PhEyeSlash } from '@phosphor-icons/vue'

const inProgress = ref([])
const loading = ref(true)
const showDropped = ref(false)
const toast = useToastStore()

const fetchInProgress = async (isInitial = false) => {
  if (isInitial) loading.value = true
  try {
    inProgress.value = await client.get('/shows/in-progress', { params: { include_dropped: showDropped.value } })
  } catch (err) {
    toast.error('Failed to load in-progress shows')
  } finally {
    loading.value = false
  }
}

onMounted(() => fetchInProgress(true))

watch(showDropped, () => fetchInProgress(false))

const handleDrop = async (show) => {
  try {
    await client.post(`/shows/${show.id}/drop`)
    toast.success(`"${show.name}" dropped`)
    await fetchInProgress(false)
  } catch (err) {
    toast.error('Failed to drop show')
  }
}

const handlePickup = async (show) => {
  try {
    await client.post(`/shows/${show.id}/pickup`)
    toast.success(`"${show.name}" picked up`)
    await fetchInProgress(false)
  } catch (err) {
    toast.error('Failed to pick up show')
  }
}
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8 pl-4 border-l-4 border-primary">
      <h1 class="text-3xl font-extrabold text-white tracking-tight">In Progress</h1>
      
      <div class="flex items-center gap-4">
        <label class="inline-flex items-center cursor-pointer group">
          <input type="checkbox" v-model="showDropped" class="sr-only peer">
          <div class="w-11 h-6 bg-gray-800 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-gray-400 after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary relative group-hover:after:bg-white transition-all"></div>
          <span class="ms-3 text-sm font-medium text-gray-400 group-hover:text-white transition-colors">Show Dropped</span>
        </label>

        <span class="bg-surface border border-gray-800 px-3 py-1 rounded-full text-secondary font-mono text-sm">
          {{ inProgress.length }} Shows
        </span>
      </div>
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
      <div 
        v-for="show in inProgress" 
        :key="show.id" 
        class="bg-surface border border-gray-800 rounded-xl overflow-hidden hover:-translate-y-1 hover:shadow-2xl transition-all duration-300 group flex flex-col relative"
        :class="{ 'opacity-60 grayscale-[0.5]': show.is_dropped }"
      >
        <RouterLink :to="{ name: 'show-detail', params: { id: show.id } }">
          <PosterCard :src="show.poster_path" :tmdbId="show.tmdb_id" :alt="show.name" ratio="aspect-[3/4]" />
        </RouterLink>
        
        <!-- Drop / Pick up badge button -->
        <button 
          v-if="!show.is_dropped"
          @click.stop="handleDrop(show)"
          class="absolute top-2 right-2 bg-black/60 hover:bg-red-600/80 text-white p-2 rounded-lg backdrop-blur-md opacity-0 group-hover:opacity-100 transition-all z-10"
          title="Drop Show"
        >
          <PhEyeSlash class="w-5 h-5" />
        </button>
        <button 
          v-else
          @click.stop="handlePickup(show)"
          class="absolute top-2 right-2 bg-primary/80 hover:bg-primary text-white p-2 rounded-lg backdrop-blur-md z-10"
          title="Pick Up Show"
        >
          <PhArrowUUpLeft class="w-5 h-5" />
        </button>

        <div v-if="show.is_dropped" class="absolute top-2 left-2 bg-red-600/80 text-white text-[10px] font-bold px-1.5 py-0.5 rounded flex items-center gap-1 uppercase tracking-wider shadow-lg">
          Dropped
        </div>

        <div class="p-4 flex-grow flex flex-col justify-between space-y-3">
          <RouterLink :to="{ name: 'show-detail', params: { id: show.id } }">
            <h3 class="font-bold text-white text-lg line-clamp-1 group-hover:text-primary transition-colors" :title="show.name">{{ show.name }}</h3>
          </RouterLink>
          
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
      </div>
    </div>
  </div>
</template>
