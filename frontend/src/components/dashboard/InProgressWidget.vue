<script setup>
import { ref, onMounted } from 'vue'
import client from '@/api/client'
import { PhCheckCircle, PhClock } from '@phosphor-icons/vue'

const props = defineProps({
  shows: { type: Array, required: true }
})
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
      <RouterLink 
        v-for="show in shows" 
        :key="show.id"
        :to="{ name: 'show-detail', params: { id: show.id } }"
        class="flex gap-4 p-2 -mx-2 rounded-lg hover:bg-gray-800/50 transition-colors group"
      >
        <img :src="show.poster_path" class="w-12 h-16 object-cover rounded shadow-md group-hover:opacity-90" />
        <div class="flex-grow flex flex-col justify-center min-w-0">
          <h3 class="font-semibold text-white truncate text-sm" :title="show.name">{{ show.name }}</h3>
          <div class="flex items-center justify-between mt-1 mb-1.5 min-w-0">
            <span class="text-xs text-amber-500 whitespace-nowrap">{{ show.remaining_episodes }} eps · {{ show.remaining_hours }} hrs left</span>
          </div>
          <!-- Progress bare minimum wrapper instead of full component for size -->
          <div class="w-full bg-gray-800 rounded-full h-1 overflow-hidden">
            <div class="bg-amber-500 h-full rounded-full transition-all" :style="`width: ${show.progress_pct}%`"></div>
          </div>
        </div>
      </RouterLink>
    </div>
  </div>
</template>
