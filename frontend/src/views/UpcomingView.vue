<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import {
  format,
  addMonths,
  subMonths,
  addWeeks,
  subWeeks,
  startOfMonth,
  endOfMonth,
  startOfWeek,
  endOfWeek,
  eachDayOfInterval,
  isSameMonth,
  isToday,
  isPast,
  isSameDay
} from 'date-fns'
import client from '@/api/client'
import { useToastStore } from '@/stores/toast'
import { PhCaretLeft, PhCaretRight, PhCalendarBlank, PhCalendar, PhColumns } from '@phosphor-icons/vue'

const toast = useToastStore()
const loading = ref(true)
const currentDate = ref(new Date())
const episodes = ref([])
const viewMode = ref('month') // 'month' or 'week'
const showDropped = ref(false)

// Generate days for the calendar grid
const calendarDays = computed(() => {
  if (viewMode.value === 'month') {
    const start = startOfMonth(currentDate.value)
    const end = endOfMonth(currentDate.value)
    const days = eachDayOfInterval({ start, end })
    
    // Start grid on Sunday (0)
    const firstDay = start.getDay()
    const prefixDays = Array.from({ length: firstDay }).map(() => null)
    
    // Fill remaining days to keep grid complete (multiple of 7)
    const totalSlots = prefixDays.length + days.length
    const suffixCount = Math.ceil(totalSlots / 7) * 7 - totalSlots
    const suffixDays = Array.from({ length: suffixCount }).map(() => null)

    return [...prefixDays, ...days, ...suffixDays]
  } else {
    // Week view
    const start = startOfWeek(currentDate.value) // defaults to Sunday
    const end = endOfWeek(currentDate.value)
    return eachDayOfInterval({ start, end })
  }
})

const currentDisplayLabel = computed(() => {
  if (viewMode.value === 'month') {
    return format(currentDate.value, 'MMMM yyyy')
  } else {
    const start = startOfWeek(currentDate.value)
    const end = endOfWeek(currentDate.value)
    if (start.getMonth() === end.getMonth()) {
      return `${format(start, 'MMM d')} - ${format(end, 'd, yyyy')}`
    }
    return `${format(start, 'MMM d')} - ${format(end, 'MMM d, yyyy')}`
  }
})

const fetchUpcoming = async () => {
  loading.value = true
  try {
    let start_date, end_date;
    if (viewMode.value === 'month') {
      start_date = format(startOfMonth(currentDate.value), 'yyyy-MM-dd')
      end_date = format(endOfMonth(currentDate.value), 'yyyy-MM-dd')
    } else {
      start_date = format(startOfWeek(currentDate.value), 'yyyy-MM-dd')
      end_date = format(endOfWeek(currentDate.value), 'yyyy-MM-dd')
    }
    episodes.value = await client.get('/shows/upcoming', { 
      params: { 
        start_date, 
        end_date,
        include_dropped: showDropped.value
      } 
    })
  } catch (err) {
    toast.error('Failed to load upcoming episodes')
  } finally {
    loading.value = false
  }
}

onMounted(() => fetchUpcoming())

watch([viewMode, showDropped], () => {
  fetchUpcoming()
})

const goNext = () => {
  if (viewMode.value === 'month') {
    currentDate.value = addMonths(currentDate.value, 1)
  } else {
    currentDate.value = addWeeks(currentDate.value, 1)
  }
  fetchUpcoming()
}

const goPrev = () => {
  if (viewMode.value === 'month') {
    currentDate.value = subMonths(currentDate.value, 1)
  } else {
    currentDate.value = subWeeks(currentDate.value, 1)
  }
  fetchUpcoming()
}

const goToday = () => {
  currentDate.value = new Date()
  fetchUpcoming()
}

// Helper to get episodes for a specific day
const getEpisodesForDay = (day) => {
  if (!day) return []
  return episodes.value.filter(ep => {
    return ep.air_date === format(day, 'yyyy-MM-dd')
  })
}

const formatEpisodeNumber = (season, episode) => {
  const s = season?.toString().padStart(2, '0') || '00'
  const e = episode?.toString().padStart(2, '0') || '00'
  return `S${s}E${e}`
}

</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-8 pl-4 border-l-4 border-primary">
      <h1 class="text-3xl font-extrabold text-white tracking-tight">Upcoming Episodes</h1>
      
      <div class="flex flex-wrap items-center gap-4">
        <!-- View Toggle -->
        <div class="flex bg-surface border border-gray-800 rounded-lg p-1">
          <button 
            @click="viewMode = 'month'" 
            class="flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors"
            :class="viewMode === 'month' ? 'bg-primary/20 text-primary' : 'text-gray-400 hover:text-white'"
          >
            <PhCalendar weight="bold" class="w-4 h-4" />
            Month
          </button>
          <button 
            @click="viewMode = 'week'" 
            class="flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors"
            :class="viewMode === 'week' ? 'bg-primary/20 text-primary' : 'text-gray-400 hover:text-white'"
          >
            <PhColumns weight="bold" class="w-4 h-4" />
            Week
          </button>
        </div>

        <label class="inline-flex items-center cursor-pointer group">
          <input type="checkbox" v-model="showDropped" class="sr-only peer">
          <div class="w-11 h-6 bg-gray-800 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary/20 rounded-full peer peer-checked:after:translate-x-full rtl:peer-checked:after:-translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:start-[2px] after:bg-gray-400 after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary relative group-hover:after:bg-white transition-all"></div>
          <span class="ms-3 text-sm font-medium text-gray-400 group-hover:text-white transition-colors">Show Dropped</span>
        </label>

        <button @click="goToday" class="px-4 py-2 bg-surface hover:bg-gray-800 border border-gray-700 rounded-lg text-sm font-medium transition-colors text-gray-300 hover:text-white">
          Today
        </button>

        <div class="flex items-center bg-surface border border-gray-700 rounded-lg overflow-hidden">
          <button @click="goPrev" class="p-2 hover:bg-gray-800 transition-colors">
            <PhCaretLeft class="w-5 h-5 text-gray-400" />
          </button>
          <div class="px-4 py-2 min-w-[180px] text-center font-bold text-white">
            {{ currentDisplayLabel }}
          </div>
          <button @click="goNext" class="p-2 hover:bg-gray-800 transition-colors">
            <PhCaretRight class="w-5 h-5 text-gray-400" />
          </button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="flex justify-center py-20">
      <div class="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent"></div>
    </div>

    <div v-else class="bg-surface/50 border border-gray-800 rounded-2xl overflow-hidden backdrop-blur-sm">
      <!-- Weekday Headers -->
      <div class="grid grid-cols-7 border-b border-gray-800 bg-black/40">
        <div v-for="day in ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']" :key="day" class="px-2 py-3 text-center text-xs font-semibold text-gray-400 uppercase tracking-wider">
          {{ day }}
        </div>
      </div>

      <!-- Calendar Grid -->
      <div class="grid grid-cols-7 auto-rows-fr">
        <div 
          v-for="(day, index) in calendarDays" 
          :key="index"
          class="border-b border-r border-gray-800/50 p-1 sm:p-2 flex flex-col gap-1 transition-colors relative group"
          :class="{
            'min-h-[120px] md:min-h-[160px]': viewMode === 'month',
            'min-h-[300px]': viewMode === 'week',
            'bg-black/20': !day,
            'hover:bg-white/[0.02]': day,
            'bg-primary/5': day && isToday(day)
          }"
        >
          <template v-if="day">
            <div class="flex items-center justify-between px-1 mb-1">
              <span 
                class="text-sm font-medium w-7 h-7 flex items-center justify-center rounded-full transition-colors"
                :class="{
                  'bg-primary text-black font-bold': isToday(day),
                  'text-gray-300 group-hover:text-white': !isToday(day) && !isPast(day),
                  'text-gray-600': isPast(day) && !isToday(day)
                }"
              >
                {{ format(day, 'd') }}
              </span>
            </div>

            <div class="flex-grow overflow-y-auto space-y-2 custom-scrollbar pr-1">
              <RouterLink
                v-for="ep in getEpisodesForDay(day)" 
                :key="ep.episode_id"
                :to="{ name: 'show-detail', params: { id: ep.show_id } }"
                class="block bg-surface border hover:border-gray-600 rounded-xl p-2 transition-all cursor-pointer shadow-sm hover:shadow-md relative"
                :class="ep.is_dropped ? 'border-red-900/30 opacity-60 grayscale-[0.5] hover:bg-gray-800/50' : 'border-gray-800 hover:bg-gray-800'"
              >
                <div v-if="ep.is_dropped" class="absolute -top-2 -right-2 bg-red-600/80 text-white text-[10px] font-bold px-1.5 py-0.5 rounded shadow-lg z-10">
                  Dropped
                </div>
                <div class="flex gap-2">
                  <div class="w-10 h-14 sm:w-12 sm:h-16 flex-shrink-0 rounded-lg bg-gray-900 overflow-hidden shadow-inner hidden sm:block">
                    <img v-if="ep.show_poster_path" :src="`https://image.tmdb.org/t/p/w92${ep.show_poster_path}`" class="w-full h-full object-cover" />
                    <div v-else class="w-full h-full flex items-center justify-center text-gray-700">
                      <PhCalendarBlank class="w-5 h-5" />
                    </div>
                  </div>
                  
                  <div class="flex flex-col justify-center min-w-0 flex-grow py-0.5">
                    <span class="text-xs sm:text-sm font-bold text-white truncate transition-colors" :title="ep.show_name">{{ ep.show_name }}</span>
                    <div class="flex items-center text-[10px] sm:text-xs text-gray-400 mt-1">
                      <span class="font-mono bg-black/50 text-secondary px-1.5 py-0.5 rounded">{{ formatEpisodeNumber(ep.season_number, ep.episode_number) }}</span>
                    </div>
                    <span class="text-[10px] sm:text-xs text-gray-500 truncate mt-1 italic" :title="ep.episode_name">{{ ep.episode_name || 'TBA' }}</span>
                  </div>
                </div>
              </RouterLink>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}
.custom-scrollbar:hover::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
}
</style>
