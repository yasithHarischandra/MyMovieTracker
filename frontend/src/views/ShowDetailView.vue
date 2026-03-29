<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import client from '@/api/client'
import { useToastStore } from '@/stores/toast'
import PosterCard from '@/components/common/PosterCard.vue'
import SeasonAccordion from '@/components/shows/SeasonAccordion.vue'
import ProgressBar from '@/components/common/ProgressBar.vue'

const route = useRoute()
const toast = useToastStore()
const show = ref(null)
const loading = ref(true)

const loadShow = async () => {
  loading.value = true
  try {
    show.value = await client.get(`/shows/${route.params.id}`)
  } catch (err) {
    toast.error('Failed to load TV show')
  } finally {
    loading.value = false
  }
}

const watchEpisode = async (episode, season) => {
  try {
    const res = await client.post(`/shows/${show.value.id}/episodes/${episode.id}/watch`, { rating: null, note: null })
    toast.success(`Marked "${episode.name}" as watched`)
    
    // Optimistic local update so we don't have to refetch full show structure right away
    episode.watched = true
    episode.watch_history_id = res.id
    season.watched_count++
    season.remaining_count--
    show.value.watched_episodes++
    show.value.remaining_episodes--
    // We could recalculate hours but a full reload is safer for complex state
    await loadShow()
  } catch (err) {
    toast.error('Failed to log watch')
  }
}

const unwatchEpisode = async (episode) => {
  if (!episode.watch_history_id) return
  if (!confirm('Unmark this episode?')) return
  try {
    await client.delete(`/shows/episodes/watch/${episode.watch_history_id}`)
    toast.success('Watch removed')
    await loadShow()
  } catch (err) {
    toast.error('Failed to unwatch')
  }
}

const watchSeason = async (season) => {
  if (!confirm(`Mark all ${season.remaining_count} remaining episodes in Season ${season.season_number} as watched?`)) return
  try {
    await client.post(`/shows/${show.value.id}/seasons/${season.season_number}/watch`)
    toast.success(`Season ${season.season_number} marked completed`)
    await loadShow()
  } catch (err) {
    toast.error('Failed to log season watch')
  }
}

onMounted(loadShow)
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8" v-if="!loading && show">
    <!-- Header Block -->
    <div class="flex flex-col md:flex-row gap-8 items-start mb-12">
      <!-- Poster -->
      <div class="w-full md:w-1/3 max-w-sm shrink-0 shadow-2xl rounded-2xl overflow-hidden border border-gray-800">
        <PosterCard :src="show.poster_path" :tmdbId="show.tmdb_id" :alt="show.name" />
      </div>

      <!-- Detail Info -->
      <div class="flex-grow w-full">
        <div class="flex flex-wrap items-center gap-4 mb-2">
          <h1 class="text-4xl font-extrabold text-white">{{ show.name }}</h1>
          <span class="px-2 py-0.5 mt-2 bg-surface text-gray-400 border border-gray-700 font-mono text-sm rounded">{{ show.status }}</span>
        </div>
        
        <div class="flex flex-wrap gap-2 text-sm font-mono text-gray-400 mb-6 items-center">
          <span>{{ show.first_air_date ? show.first_air_date.substring(0,4) : 'TBA' }}</span>
          <span class="text-gray-600 px-1">•</span>
          <span class="text-secondary font-bold px-2 py-0.5 bg-secondary/10 rounded">{{ show.genres }}</span>
        </div>

        <p class="text-gray-300 leading-relaxed max-w-3xl text-lg mb-8">{{ show.overview || 'No overview available.' }}</p>

        <!-- Dynamic Overall Progress Bar -->
        <div class="bg-surface p-6 rounded-xl border border-gray-800 lg:max-w-2xl">
          <div class="flex justify-between items-end mb-4">
            <div>
              <div class="text-sm font-bold text-gray-400 uppercase tracking-wider mb-1">Overall Progress</div>
              <div class="text-3xl font-mono text-white leading-none">
                {{ show.watched_episodes }} <span class="text-lg text-gray-500">/ {{ show.total_episodes }} eps</span>
              </div>
            </div>
            <div class="text-right">
              <div class="text-2xl font-mono text-amber-500 font-bold leading-none">{{ show.remaining_hours }}h</div>
              <div class="text-sm font-semibold text-gray-500 mt-1">remaining</div>
            </div>
          </div>
          <ProgressBar 
            :value="show.watched_episodes" 
            :max="show.total_episodes" 
            color="bg-secondary" 
            height="h-3"
            showPercentage
          />
        </div>
      </div>
    </div>

    <!-- Seasons List -->
    <div class="max-w-4xl mx-auto space-y-2 mt-8">
      <h2 class="text-2xl font-bold text-white mb-6">Seasons</h2>
      <!-- Default open the first incomplete season, or the latest season -->
      <SeasonAccordion 
        v-for="(season, index) in show.seasons" 
        :key="season.id" 
        :season="season"
        :defaultOpen="season.remaining_count > 0 || index === show.seasons.length - 1"
        @watch-episode="watchEpisode"
        @unwatch-episode="unwatchEpisode"
        @watch-season="watchSeason"
      />
    </div>

  </div>
</template>
