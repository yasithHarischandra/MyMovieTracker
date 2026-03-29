<script setup>
import { PhTelevision, PhClock, PhHourglass, PhHourglassHigh } from '@phosphor-icons/vue'

const props = defineProps({ stats: Object })
</script>

<template>
  <div class="bg-surface border border-gray-800 border-l-4 border-l-secondary rounded-xl p-5 shadow-sm col-span-1 md:col-span-2 flex flex-col justify-between">
    <div class="text-xs font-bold uppercase tracking-wider text-secondary mb-4">📺 Series</div>
    
    <!-- Big Progress Bar Hero -->
    <div class="mb-6">
      <div class="flex justify-between items-end mb-2">
        <div class="text-sm font-semibold text-secondary">{{ (stats?.episodes_watched || 0).toLocaleString() }} watched</div>
        <div class="text-sm font-semibold text-amber-500">{{ (stats?.remaining_episodes || 0).toLocaleString() }} remaining</div>
      </div>
      
      <!-- Split bar -->
      <div class="w-full h-3 flex overflow-hidden rounded-full font-mono relative bg-gray-800">
        <div class="h-full bg-gradient-to-r from-primary to-secondary transition-all" :style="`width: ${stats?.completion_pct || 0}%`"></div>
        <div class="h-full bg-amber-900/40 transition-all" :style="`width: ${(100 - (stats?.completion_pct || 0))}%`"></div>
      </div>
      <div class="mt-2 text-xs text-gray-500 font-mono text-center">
        {{ stats?.completion_pct || 0 }}% complete · {{ (stats?.total_episodes_tracked || 0).toLocaleString() }} total episodes
      </div>
    </div>

    <!-- Mini 4-stat row -->
    <div class="grid grid-cols-4 gap-2 divide-x divide-gray-800 border-t border-gray-800 pt-4">
      <div class="flex flex-col items-center justify-center text-center px-1">
        <div class="flex items-center gap-1 text-white font-mono text-lg font-bold">
          <PhTelevision class="text-gray-400 w-4 h-4 hidden sm:block"/> {{ (stats?.episodes_watched || 0).toLocaleString() }}
        </div>
        <div class="text-[10px] sm:text-xs text-gray-500 leading-tight">eps watched</div>
      </div>

      <div class="flex flex-col items-center justify-center text-center px-1">
        <div class="flex items-center gap-1 text-white font-mono text-lg font-bold">
          <PhClock class="text-gray-400 w-4 h-4 hidden sm:block"/> {{ (stats?.series_hours_watched || 0).toLocaleString() }}
        </div>
        <div class="text-[10px] sm:text-xs text-gray-500 leading-tight">hrs watched</div>
      </div>

      <div class="flex flex-col items-center justify-center text-center px-1">
        <div class="flex items-center gap-1 text-white font-mono text-lg font-bold">
          <PhHourglass class="text-amber-500 w-4 h-4 hidden sm:block"/> {{ stats?.in_progress_count || 0 }}
        </div>
        <div class="text-[10px] sm:text-xs text-amber-500/70 leading-tight">in progress</div>
      </div>

      <div class="flex flex-col items-center justify-center text-center px-1">
        <div class="flex items-center gap-1 text-white font-mono text-lg font-bold">
          <PhHourglassHigh class="text-amber-500 w-4 h-4 hidden sm:block"/> {{ (stats?.remaining_hours || 0).toLocaleString() }}
        </div>
        <div class="text-[10px] sm:text-xs text-amber-500/70 leading-tight">hrs remaining</div>
      </div>
    </div>
  </div>
</template>
