<script setup>
import { ref, watch, onMounted } from 'vue'
import { format, subDays, startOfMonth, startOfYear, parseISO } from 'date-fns'
import client from '@/api/client'
import { useToastStore } from '@/stores/toast'
import ActivityFeed from '@/components/dashboard/ActivityFeed.vue'
import { PhCalendarBlank } from '@phosphor-icons/vue'

const toast = useToastStore()
const loading = ref(false)
const activities = ref([])
const stats = ref(null)

const period = ref('30days')
const customFrom = ref('')
const customTo = ref('')

const dateRanges = {
  '7days': () => ({ from: format(subDays(new Date(), 7), 'yyyy-MM-dd'), to: format(new Date(), 'yyyy-MM-dd') }),
  '30days': () => ({ from: format(subDays(new Date(), 30), 'yyyy-MM-dd'), to: format(new Date(), 'yyyy-MM-dd') }),
  'this_month': () => ({ from: format(startOfMonth(new Date()), 'yyyy-MM-dd'), to: format(new Date(), 'yyyy-MM-dd') }),
  'this_year': () => ({ from: format(startOfYear(new Date()), 'yyyy-MM-dd'), to: format(new Date(), 'yyyy-MM-dd') }),
  'all': () => ({ from: null, to: null })
}

const loadData = async () => {
  loading.value = true
  try {
    let from_dt, to_dt
    
    if (period.value === 'custom') {
      from_dt = customFrom.value || null
      to_dt = customTo.value || null
    } else {
      const dates = dateRanges[period.value]()
      from_dt = dates.from ? dates.from + 'T00:00:00Z' : null
      to_dt = dates.to ? dates.to + 'T23:59:59Z' : null
    }

    const params = {}
    if (from_dt) params.from_date = from_dt
    if (to_dt) params.to_date = to_dt

    const [actRes, statRes] = await Promise.all([
      client.get('/history', { params: { ...params, limit: 100 } }),
      client.get('/history/stats', { params })
    ])
    
    activities.value = actRes
    stats.value = statRes

  } catch (err) {
    toast.error('Failed to load history')
  } finally {
    loading.value = false
  }
}

watch([period, customFrom, customTo], () => {
  if (period.value === 'custom' && (!customFrom.value || !customTo.value)) return
  loadData()
})

onMounted(loadData)
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    
    <!-- Controls Layout -->
    <div class="flex flex-col md:flex-row justify-between items-start md:items-end mb-8 gap-4 bg-surface p-4 rounded-xl border border-gray-800">
      
      <div class="flex flex-col">
        <label class="text-sm font-semibold text-gray-400 mb-2 flex items-center gap-2">
          <PhCalendarBlank class="w-4 h-4" /> Filter Period
        </label>
        <div class="flex flex-wrap gap-2">
          <button 
            v-for="(val, key) in {'30days': 'Last 30 Days', 'this_month': 'This Month', 'this_year': 'This Year', 'all': 'All Time', 'custom': 'Custom'}"
            :key="key"
            @click="period = key"
            :class="['px-4 py-1.5 rounded-full text-sm font-medium border transition-colors', period === key ? 'bg-primary text-white border-primary' : 'bg-transparent text-gray-400 border-gray-700 hover:text-white hover:border-gray-500']"
          >
            {{ val }}
          </button>
        </div>
      </div>

      <div v-if="period === 'custom'" class="flex items-center gap-3 bg-background p-2 rounded-lg border border-gray-800 w-full md:w-auto">
        <input type="date" v-model="customFrom" class="bg-transparent text-sm text-gray-300 outline-none" />
        <span class="text-gray-600">to</span>
        <input type="date" v-model="customTo" class="bg-transparent text-sm text-gray-300 outline-none" />
      </div>

    </div>

    <div v-if="loading" class="flex justify-center p-12">
      <div class="animate-spin rounded-full h-8 w-8 border-2 border-primary border-t-transparent"></div>
    </div>

    <template v-else>
      <!-- Stats row -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-10" v-if="stats">
        <div class="bg-surface border-l-4 border-l-primary p-4 rounded-r-xl shadow-sm border border-gray-800">
          <div class="text-xs text-gray-500 uppercase font-bold tracking-wider">Movies Watched</div>
          <div class="text-3xl font-mono text-white mt-1">{{ stats.movies_watched }}</div>
        </div>
        <div class="bg-surface border-l-4 border-l-primary p-4 rounded-r-xl shadow-sm border border-gray-800">
          <div class="text-xs text-gray-500 uppercase font-bold tracking-wider">Movie Hours</div>
          <div class="text-3xl font-mono text-white mt-1">{{ stats.movie_hours }}</div>
        </div>
        <div class="bg-surface border-l-4 border-l-secondary p-4 rounded-r-xl shadow-sm border border-gray-800">
          <div class="text-xs text-gray-500 uppercase font-bold tracking-wider">Episodes Watched</div>
          <div class="text-3xl font-mono text-white mt-1">{{ stats.episodes_watched }}</div>
        </div>
        <div class="bg-surface border-l-4 border-l-secondary p-4 rounded-r-xl shadow-sm border border-gray-800">
          <div class="text-xs text-gray-500 uppercase font-bold tracking-wider">Series Hours</div>
          <div class="text-3xl font-mono text-white mt-1">{{ stats.series_hours }}</div>
        </div>
      </div>

      <!-- Feed -->
      <ActivityFeed :activities="activities" />
    </template>
    
  </div>
</template>
