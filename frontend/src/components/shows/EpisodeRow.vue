<script setup>
import { ref } from 'vue'
import { PhCheckCircle, PhHash } from '@phosphor-icons/vue'

const props = defineProps({
  episode: { type: Object, required: true },
  seasonNumber: { type: Number, required: true }
})

const emit = defineEmits(['watch', 'unwatch'])
</script>

<template>
  <div class="flex items-center gap-4 py-3 border-b border-gray-800/50 hover:bg-white/[0.02] transition-colors -mx-4 px-4 group">
    
    <!-- Episode Meta -->
    <div class="w-12 text-center shrink-0 border-r border-gray-800 pr-2">
      <span class="text-lg font-mono font-bold text-gray-500 group-hover:text-white transition-colors">{{ episode.episode_number }}</span>
    </div>

    <!-- Episode Details -->
    <div class="flex-grow min-w-0">
      <div class="flex items-center gap-2">
        <h4 class="font-medium text-white truncate text-sm" :class="{'text-gray-400': episode.watched}">
          {{ episode.name }}
        </h4>
        <span v-if="episode.watched" class="shrink-0 bg-primary/20 text-primary px-1.5 py-0.5 rounded text-[10px] font-bold uppercase">Watched</span>
      </div>
      <div class="text-xs text-gray-500 font-mono flex items-center gap-2 mt-1">
        <span>{{ episode.air_date || 'TBA' }}</span>
        <span>•</span>
        <span>{{ episode.runtime_mins || 45 }}m</span>
      </div>
    </div>

    <!-- Actions -->
    <div class="shrink-0 flex items-center justify-end w-24">
      <button 
        v-if="episode.watched"
        @click="$emit('unwatch', episode)"
        class="text-primary hover:text-red-400 transition-colors p-2 rounded-full hover:bg-red-400/10"
        title="Unwatch episode"
      >
        <PhCheckCircle weight="fill" class="w-6 h-6" />
      </button>
      <button 
        v-else
        @click="$emit('watch', episode)"
        class="text-gray-600 hover:text-primary transition-colors p-2 rounded-full hover:bg-primary/10 opacity-50 hover:opacity-100"
        title="Mark watched"
      >
        <PhCheckCircle class="w-6 h-6" />
      </button>
    </div>

  </div>
</template>
