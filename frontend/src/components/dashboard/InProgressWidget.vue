<script setup>
import { ref } from 'vue'
import client from '@/api/client'
import { PhCheckCircle, PhClock, PhFastForward } from '@phosphor-icons/vue'
import { useToastStore } from '@/stores/toast'

const props = defineProps({
  shows: { type: Array, required: true }
})

const emit = defineEmits(['refresh'])
const toast = useToastStore()
const loadingId = ref(null)

const markNext = async (show) => {
  if (loadingId.value) return
  loadingId.value = show.id
  try {
    await client.post(`/shows/${show.id}/watch-next`)
    toast.success(`Marked next episode of ${show.name} as watched`)
    emit('refresh')
  } catch (err) {
    toast.error(err.response?.data?.detail || 'Failed to mark next episode')
  } finally {
    loadingId.value = null
  }
}
</script>

<template>
  <div class="bg-surface border border-gray-800 rounded-xl p-5 shadow-sm">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-bold text-white flex items-center gap-2">
        <PhClock class="text-amber-500" weight="fill" />
        In Progress
      </h2>
      <RouterLink :to="{name: 'in-progress'}" class="text-sm text-primary hover:underline">View All</RouterLink>
    </div>

    <div v-if="shows.length === 0" class="text-center py-6 text-gray-500 text-sm">
      <PhCheckCircle class="w-8 h-8 mx-auto mb-2 opacity-50" />
      <p>All caught up!</p>
    </div>

    <div v-else class="space-y-4">
      <div 
        v-for="show in shows" 
        :key="show.id"
        class="flex items-center gap-4 p-2 -mx-2 rounded-lg hover:bg-gray-800/50 transition-colors group relative"
      >
        <RouterLink :to="{ name: 'show-detail', params: { id: show.id } }" class="flex gap-4 flex-grow min-w-0">
          <img :src="show.poster_path" class="w-12 h-16 object-cover rounded shadow-md group-hover:opacity-90" />
          <div class="flex-grow flex flex-col justify-center min-w-0">
            <h3 class="font-semibold text-white truncate text-sm" :title="show.name">{{ show.name }}</h3>
            <div class="flex items-center justify-between mt-0.5 min-w-0">
              <span class="text-[10px] text-amber-500 whitespace-nowrap">{{ show.remaining_episodes }} left</span>
            </div>
            
            <div class="text-[10px] text-gray-500 mt-0.5 truncate italic" v-if="show.next_episode">
              Next: S{{show.next_episode.season_number}}E{{show.next_episode.episode_number}} · {{show.next_episode.name}}
            </div>

            <div class="w-full bg-gray-800 rounded-full h-1 mt-1.5 overflow-hidden">
              <div class="bg-amber-500 h-full rounded-full transition-all" :style="`width: ${show.progress_pct}%`"></div>
            </div>
          </div>
        </RouterLink>

        <button 
          v-if="show.next_episode"
          @click.prevent="markNext(show)" 
          class="p-2 rounded-full bg-gray-700/50 hover:bg-primary/20 text-gray-300 hover:text-primary transition-all disabled:opacity-50"
          title="mark next episode watched"
          :disabled="loadingId === show.id"
        >
          <PhFastForward weight="bold" class="w-5 h-5" v-if="loadingId !== show.id" />
          <div v-else class="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
        </button>
      </div>
    </div>
  </div>
</template>
