<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import client from '@/api/client'
import { useToastStore } from '@/stores/toast'
import PosterCard from '@/components/common/PosterCard.vue'
import StarRating from '@/components/common/StarRating.vue'
import WatchHistoryRow from '@/components/movies/WatchHistoryRow.vue'

const route = useRoute()
const toast = useToastStore()
const movie = ref(null)
const history = ref([])
const loading = ref(true)

const showWatchModal = ref(false)
const watchForm = ref({ rating: 0, note: '' })
const submitting = ref(false)

const loadMovie = async () => {
  loading.value = true
  try {
    const [mv, hist] = await Promise.all([
      client.get(`/movies/${route.params.id}`),
      client.get(`/movies/${route.params.id}/history`)
    ])
    movie.value = mv
    history.value = hist
  } catch (err) {
    toast.error('Failed to load movie')
  } finally {
    loading.value = false
  }
}

const submitWatch = async () => {
  submitting.value = true
  try {
    const payload = {}
    if (watchForm.value.rating > 0) payload.rating = watchForm.value.rating
    if (watchForm.value.note.trim()) payload.note = watchForm.value.note.trim()

    await client.post(`/movies/${movie.value.id}/watch`, payload)
    toast.success('Watch logged!')
    showWatchModal.value = false
    watchForm.value = { rating: 0, note: '' }
    await loadMovie()
  } catch (err) {
    toast.error('Failed to log watch')
  } finally {
    submitting.value = false
  }
}

const unwatch = async (historyId) => {
  if (!confirm('Remove this watch log?')) return
  try {
    await client.delete(`/movies/watch/${historyId}`)
    toast.success('Watch removed')
    await loadMovie()
  } catch (err) {
    toast.error('Failed to remove log')
  }
}

onMounted(loadMovie)
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8" v-if="!loading && movie">
    
    <!-- Header Block -->
    <div class="flex flex-col md:flex-row gap-8 items-start mb-12">
      <!-- Poster -->
      <div class="w-full md:w-1/3 max-w-sm mx-auto md:mx-0 shrink-0 shadow-2xl rounded-2xl overflow-hidden border border-gray-800">
        <PosterCard :src="movie.poster_path" :tmdbId="movie.tmdb_id" :alt="movie.title" />
      </div>

      <!-- Detail Info -->
      <div class="flex-grow w-full">
        <h1 class="text-4xl font-extrabold text-white mb-2">{{ movie.title }}</h1>
        <div class="flex flex-wrap gap-2 text-sm font-mono text-gray-400 mb-6 items-center">
          <span v-if="movie.release_date">{{ movie.release_date.substring(0,4) }}</span>
          <span class="text-gray-600 px-1">•</span>
          <span>{{ movie.runtime_mins }} min</span>
          <span class="text-gray-600 px-1">•</span>
          <span class="text-primary font-bold px-2 py-0.5 bg-primary/10 rounded">{{ movie.genres }}</span>
        </div>

        <p class="text-gray-300 leading-relaxed mb-8 max-w-3xl text-lg">{{ movie.overview }}</p>

        <!-- Stats / CTA -->
        <div class="flex items-center gap-6 bg-surface p-4 rounded-xl border border-gray-800 inline-flex shadow-inner">
          <div class="text-center pr-6 border-r border-gray-800">
            <div class="text-3xl font-mono text-white font-bold">{{ history.length }}</div>
            <div class="text-xs text-secondary uppercase font-bold tracking-wider">Times Watched</div>
          </div>
          
          <button @click="showWatchModal = true" class="btn-primary flex items-center gap-2">
            <span class="text-lg">👀</span> Log Watch
          </button>
        </div>
      </div>
    </div>

    <!-- History Block -->
    <div class="border-t border-gray-800 pt-8 max-w-3xl">
      <h2 class="text-2xl font-bold text-white mb-6">Watch History</h2>
      
      <div v-if="history.length === 0" class="text-center bg-surface rounded-xl p-8 border border-gray-800 text-gray-500">
        You haven't watched this movie yet.
      </div>

      <div v-else class="space-y-4">
        <WatchHistoryRow v-for="entry in history" :key="entry.id" :entry="entry" @unwatch="unwatch" />
      </div>
    </div>

    <!-- Modal for Logging via basic teleport or position fixed block -->
    <div v-if="showWatchModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div class="bg-surface border border-gray-800 rounded-2xl shadow-2xl max-w-md w-full p-6 animate-in zoom-in-95 duration-200">
        <h3 class="text-xl font-bold text-white mb-4 flex justify-between">
          Log Watch
          <button @click="showWatchModal = false" class="text-gray-500 hover:text-white">&times;</button>
        </h3>
        
        <form @submit.prevent="submitWatch" class="space-y-6">
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-2">Rating</label>
            <StarRating v-model:rating="watchForm.rating" />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-2">Notes</label>
            <textarea 
              v-model="watchForm.note"
              class="input-field w-full h-24 resize-none"
              placeholder="What did you think?"
            ></textarea>
          </div>
          
          <div class="flex justify-end gap-3 pt-2">
            <button type="button" @click="showWatchModal = false" class="btn-secondary">Cancel</button>
            <button type="submit" :disabled="submitting" class="btn-primary">
              {{ submitting ? 'Saving...' : 'Save Log' }}
            </button>
          </div>
        </form>
      </div>
    </div>

  </div>
</template>
