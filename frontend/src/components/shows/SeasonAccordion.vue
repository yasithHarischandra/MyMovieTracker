<script setup>
import { ref } from 'vue'
import EpisodeRow from './EpisodeRow.vue'
import ProgressBar from '@/components/common/ProgressBar.vue'
import { PhCaretDown, PhCaretUp, PhCheckCircle } from '@phosphor-icons/vue'

const props = defineProps({
  season: { type: Object, required: true },
  defaultOpen: { type: Boolean, default: false }
})

const emit = defineEmits(['watch-episode', 'unwatch-episode', 'watch-season'])

const isOpen = ref(props.defaultOpen)
</script>

<template>
  <div class="bg-surface border border-gray-800 rounded-xl overflow-hidden mb-4 shadow-sm">
    <!-- Header -->
    <div 
      class="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-800/30 transition-colors select-none"
      @click="isOpen = !isOpen"
    >
      <div class="flex-grow min-w-0 pr-4">
        <div class="flex items-center gap-3">
          <h3 class="text-lg font-bold text-white">{{ season.name || `Season ${season.season_number}` }}</h3>
          <span 
            v-if="season.is_complete" 
            class="bg-primary/20 text-primary text-xs px-2 py-0.5 rounded-full font-bold flex items-center gap-1"
          >
            <PhCheckCircle weight="fill" /> Completed
          </span>
        </div>
        
        <div class="mt-2 flex items-center gap-4 text-xs">
          <span class="text-gray-400 font-mono">{{ season.watched_count }} / {{ season.episode_count }} eps</span>
          <ProgressBar 
            :value="season.watched_count" 
            :max="season.episode_count" 
            class="w-32" 
            height="h-1.5"
          />
        </div>
      </div>
      
      <div class="shrink-0 flex items-center gap-4">
        <button 
          v-if="!season.is_complete && season.episodes.length > 0"
          @click.stop="$emit('watch-season', season)"
          class="text-xs font-semibold uppercase text-secondary border border-secondary/50 px-3 py-1.5 rounded hover:bg-secondary/10 hover:text-secondary-light transition-colors"
        >
          Mark Season
        </button>
        <span class="text-gray-500">
          <PhCaretUp v-if="isOpen" weight="bold" class="w-5 h-5" />
          <PhCaretDown v-else weight="bold" class="w-5 h-5" />
        </span>
      </div>
    </div>

    <!-- Episodes Dropdown -->
    <div v-show="isOpen" class="bg-black/20 border-t border-gray-800/50 p-4 pt-1">
      <div v-if="season.episodes.length === 0" class="text-gray-500 py-4 text-center text-sm font-mono italic">
        No episodes data.
      </div>
      <EpisodeRow 
        v-for="ep in season.episodes" 
        :key="ep.id" 
        :episode="ep" 
        :seasonNumber="season.season_number"
        @watch="$emit('watch-episode', $event, season)"
        @unwatch="$emit('unwatch-episode', $event)"
      />
    </div>
  </div>
</template>
