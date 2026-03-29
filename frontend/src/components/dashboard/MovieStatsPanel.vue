<script setup>
import { PhFilmStrip, PhClock } from '@phosphor-icons/vue'

defineProps({ stats: Object })
</script>

<template>
  <div class="bg-surface border border-gray-800 border-l-4 border-l-primary rounded-xl p-5 shadow-sm flex flex-col justify-center gap-6">
    <div class="text-xs font-bold uppercase tracking-wider text-primary mb-2">🎬 Movies</div>
    
    <div class="flex items-center gap-4">
      <div class="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center text-primary">
        <PhFilmStrip weight="fill" class="w-6 h-6" />
      </div>
      <div>
        <div class="text-3xl font-mono font-bold text-white leading-none">{{ stats?.movies_watched || 0 }}</div>
        <div class="text-sm font-medium text-gray-400 mt-1">Movies Watched</div>
      </div>
    </div>

    <div class="flex items-center gap-4">
      <div class="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center text-primary">
        <PhClock weight="fill" class="w-6 h-6" />
      </div>
      <div>
        <div class="text-3xl font-mono font-bold text-white leading-none">{{ (stats?.movie_hours_watched || 0).toLocaleString() }} <span class="text-lg">hrs</span></div>
        <div class="text-sm font-medium text-gray-400 mt-1">Movie Hours</div>
      </div>
    </div>
  </div>
</template>
