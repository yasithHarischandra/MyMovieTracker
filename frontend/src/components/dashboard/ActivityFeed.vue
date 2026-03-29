<script setup>
import { computed } from 'vue'
import { formatDistanceToNow } from 'date-fns'
import StarRating from '@/components/common/StarRating.vue'

const props = defineProps({
  activities: { type: Array, required: true }
})

const getRelativeTime = (isoString) => {
  if (!isoString) return ''
  return formatDistanceToNow(new Date(isoString), { addSuffix: true })
}
</script>

<template>
  <div class="col-span-1 lg:col-span-2">
    <h2 class="text-xl font-bold text-white mb-6">Recent Activity</h2>
    
    <div v-if="activities.length === 0" class="text-center py-10 text-gray-500 bg-surface rounded-xl border border-gray-800">
      <span class="text-4xl mb-4 block">🍿</span>
      <p>No watches yet! Time to start tracking.</p>
    </div>

    <div v-else class="space-y-3">
      <div 
        v-for="item in activities" 
        :key="item.id"
        class="bg-surface hover:bg-gray-800/80 transition-colors rounded-xl p-3 border border-gray-800 shadow-sm flex items-center gap-4 group"
      >
        <!-- Thumbnail -->
        <RouterLink :to="item.movie_id ? {name: 'movie-detail', params: {id: item.movie_id}} : {name: 'show-detail', params: {id: item.show_id}}" class="flex-shrink-0">
          <img 
            :src="item.movie_poster_path || item.show_poster_path || '/placeholder-poster.png'" 
            class="w-10 h-14 object-cover rounded outline outline-1 outline-gray-700 shadow-md group-hover:opacity-90 transition-opacity"
            loading="lazy"
          />
        </RouterLink>

        <!-- Details -->
        <div class="flex-grow min-w-0 flex flex-col justify-center py-1">
          <div class="flex items-center gap-2">
            <RouterLink 
              :to="item.movie_id ? {name: 'movie-detail', params: {id: item.movie_id}} : {name: 'show-detail', params: {id: item.show_id}}"
              class="font-bold text-white hover:text-primary transition-colors truncate"
            >
              {{ item.movie_title || item.show_name }}
            </RouterLink>
          </div>
          
          <div class="text-sm text-gray-400 mt-1 flex items-center gap-2 flex-wrap">
            <span v-if="item.movie_id">Movie</span>
            <span v-else class="font-medium text-gray-300">S{{ item.season_number }}:E{{ item.episode_number }} "{{ item.episode_name }}"</span>
            
            <span class="text-gray-600 px-1">•</span>
            <span class="font-mono text-xs">({{ item.movie_runtime_mins || item.episode_runtime_mins || 45 }} min)</span>
          </div>
        </div>

        <!-- Right side info -->
        <div class="flex flex-col items-end gap-1 flex-shrink-0 min-w-24 pl-4 text-right border-l border-gray-800/50">
          <span class="text-xs text-gray-500">{{ getRelativeTime(item.watched_at) }}</span>
          <StarRating v-if="item.rating" :rating="item.rating" :read-only="true" size="sm" class="mt-1" />
        </div>
      </div>
    </div>
  </div>
</template>
