<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import client from '@/api/client'
import { useToastStore } from '@/stores/toast'
import PosterCard from '@/components/common/PosterCard.vue'
import StarRating from '@/components/common/StarRating.vue'
import { PhMagnifyingGlass, PhCheckCircle, PhPlus, PhFilmSlate, PhArrowSquareOut, PhEye, PhArrowUUpLeft } from '@phosphor-icons/vue'

const route = useRoute()
const router = useRouter()
const toast = useToastStore()

const query = ref(route.query.q || '')
const activeTab = ref(route.query.type || 'movies')
const results = ref([])
const loading = ref(false)
const searchTimer = ref(null)

// Quick-watch modal state (movies only)
const showWatchModal = ref(false)
const watchTarget = ref(null) // the item being quick-watched
const watchForm = ref({ rating: 0, note: '' })
const submitting = ref(false)

const doSearch = async () => {
  if (!query.value.trim()) {
    results.value = []
    return
  }
  loading.value = true
  try {
    const endpoint = activeTab.value === 'movies' ? '/search/movies' : '/search/shows'
    const res = await client.get(endpoint, { params: { q: query.value } })
    results.value = res
  } catch (err) {
    toast.error('Search failed')
  } finally {
    loading.value = false
  }
}

watch(query, (newVal) => {
  router.replace({ query: { ...route.query, q: newVal } })
  clearTimeout(searchTimer.value)
  searchTimer.value = setTimeout(doSearch, 500)
})

watch(activeTab, (newVal) => {
  router.replace({ query: { ...route.query, type: newVal } })
  doSearch()
})

onMounted(() => {
  if (query.value) doSearch()
})

/**
 * Add an item to the user's library and return the new library record.
 * Updates `item.in_library` and `item.library_id` in-place.
 */
const addToLibrary = async (item) => {
  const endpoint = activeTab.value === 'movies' ? '/movies' : '/shows'
  const resp = await client.post(endpoint, { tmdb_id: item.tmdb_id })
  item.in_library = true
  item.library_id = resp.id
  return resp
}

/**
 * Navigate to the detail view. If not yet in library, adds it first.
 */
const openDetail = async (item) => {
  try {
    if (!item.in_library) {
      await addToLibrary(item)
      toast.success(`${item.title || item.name} added to library`)
    }
    const routeName = activeTab.value === 'movies' ? 'movie-detail' : 'show-detail'
    router.push({ name: routeName, params: { id: item.library_id } })
  } catch (err) {
    toast.error(err.response?.data?.detail || 'Failed to open detail')
  }
}

/**
 * Add to library without navigating (for the + button).
 */
const handleAddToLibrary = async (item) => {
  try {
    await addToLibrary(item)
    toast.success(`${item.title || item.name} added to library`)
  } catch (err) {
    toast.error(err.response?.data?.detail || 'Failed to add')
  }
}

const handlePickup = async (item) => {
  try {
    await client.post(`/shows/${item.library_id}/pickup`)
    item.is_dropped = false
    toast.success(`"${item.name}" picked up`)
  } catch (err) {
    toast.error('Failed to pick up show')
  }
}

/**
 * Open the quick-watch modal for a movie.
 * Adds to library first if needed.
 */
const openWatchModal = async (item) => {
  try {
    if (!item.in_library) {
      await addToLibrary(item)
    }
    watchTarget.value = item
    watchForm.value = { rating: 0, note: '' }
    showWatchModal.value = true
  } catch (err) {
    toast.error(err.response?.data?.detail || 'Failed to prepare watch log')
  }
}

const closeWatchModal = () => {
  showWatchModal.value = false
  watchTarget.value = null
}

const submitWatch = async () => {
  if (!watchTarget.value) return
  submitting.value = true
  try {
    await client.post(`/movies/${watchTarget.value.library_id}/watch`, watchForm.value)
    toast.success(`"${watchTarget.value.title}" logged as watched!`)
    closeWatchModal()
  } catch (err) {
    toast.error('Failed to log watch')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

    <!-- Search Bar -->
    <div class="max-w-3xl mx-auto space-y-6 mb-12">
      <!-- Tabs -->
      <div class="flex justify-center">
        <div class="bg-surface p-1 rounded-lg inline-flex border border-gray-800">
          <button
            @click="activeTab = 'movies'"
            :class="['px-6 py-2 rounded-md font-medium text-sm transition-colors', activeTab === 'movies' ? 'bg-primary text-white' : 'text-gray-400 hover:text-white']"
          >Movies</button>
          <button
            @click="activeTab = 'shows'"
            :class="['px-6 py-2 rounded-md font-medium text-sm transition-colors', activeTab === 'shows' ? 'bg-primary text-white' : 'text-gray-400 hover:text-white']"
          >TV Shows</button>
        </div>
      </div>

      <!-- Input -->
      <div class="relative">
        <PhMagnifyingGlass class="absolute left-4 top-1/2 -translate-y-1/2 w-6 h-6 text-gray-500" />
        <input
          v-model="query"
          type="text"
          placeholder="Search for movies or TV shows..."
          class="w-full bg-surface border-2 border-gray-800 rounded-xl py-4 pl-12 pr-4 text-lg text-white placeholder-gray-500 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary shadow-lg"
          autofocus
        />
        <div v-if="loading" class="absolute right-4 top-1/2 -translate-y-1/2">
          <div class="animate-spin rounded-full h-5 w-5 border-2 border-primary border-t-transparent"></div>
        </div>
      </div>
    </div>

    <!-- Results Grid -->
    <div v-if="results.length > 0" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
      <div v-for="item in results" :key="item.tmdb_id" class="group relative flex flex-col gap-2">
        <PosterCard
          :src="item.poster_path"
          :alt="item.title || item.name"
          :tmdbId="item.tmdb_id"
          class="shadow-xl cursor-pointer"
          @click="openDetail(item)"
        >
          <template #overlay>
            <!-- Hover actions overlay -->
            <div class="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex flex-col justify-end p-3 gap-2">

              <!-- View Details button (always shown on hover) -->
              <button
                @click.stop="openDetail(item)"
                class="w-full bg-white/10 hover:bg-white/20 backdrop-blur-sm text-white font-medium py-2 rounded transition-colors flex items-center justify-center gap-2 transform translate-y-4 group-hover:translate-y-0 duration-300"
                style="transition-delay: 0ms"
              >
                <PhArrowSquareOut weight="bold" class="w-4 h-4" /> View Details
              </button>

              <!-- Mark as Watched (movies only, always shown) -->
              <button
                v-if="activeTab === 'movies'"
                @click.stop="openWatchModal(item)"
                class="w-full bg-primary/80 hover:bg-primary text-white font-medium py-2 rounded transition-colors flex items-center justify-center gap-2 transform translate-y-4 group-hover:translate-y-0 duration-300"
                style="transition-delay: 50ms"
              >
                <PhEye weight="bold" class="w-4 h-4" /> Mark Watched
              </button>

              <!-- Add to Library (when not in library) -->
              <button
                v-if="!item.in_library"
                @click.stop="handleAddToLibrary(item)"
                class="w-full bg-accent/80 hover:bg-accent text-white font-medium py-2 rounded transition-colors flex items-center justify-center gap-2 transform translate-y-4 group-hover:translate-y-0 duration-300"
                style="transition-delay: 100ms"
              >
                <PhPlus weight="bold" class="w-4 h-4" /> Add to Library
              </button>

              <!-- Pick Up (if dropped) -->
              <button
                v-else-if="activeTab === 'shows' && item.is_dropped"
                @click.stop="handlePickup(item)"
                class="w-full bg-primary/80 hover:bg-primary text-white font-medium py-2 rounded transition-colors flex items-center justify-center gap-2 transform translate-y-4 group-hover:translate-y-0 duration-300"
                style="transition-delay: 100ms"
              >
                <PhArrowUUpLeft weight="bold" class="w-4 h-4" /> Pick Up Show
              </button>
            </div>

            <!-- In Library Badge (persistently visible) -->
            <div v-if="item.in_library" class="absolute top-2 right-2 flex flex-col items-end gap-1">
              <div class="bg-primary text-white text-xs font-bold px-2 py-1 rounded-md shadow-lg flex items-center gap-1 pointer-events-none">
                <PhCheckCircle weight="fill" /> In Library
              </div>
              <div v-if="item.is_dropped" class="bg-red-600 text-white text-[10px] font-bold px-2 py-0.5 rounded shadow-lg uppercase tracking-wider pointer-events-none">
                Dropped
              </div>
            </div>
          </template>
        </PosterCard>

        <!-- Title / Year — also clickable -->
        <div class="px-1 mt-1 cursor-pointer" @click="openDetail(item)">
          <h3 class="font-semibold text-white truncate hover:text-primary transition-colors" :title="item.title || item.name">{{ item.title || item.name }}</h3>
          <p class="text-xs text-gray-400">
            {{ (item.release_date || item.first_air_date || '').substring(0,4) }}
            <span v-if="item.status" class="ml-1 px-1.5 py-0.5 rounded-sm bg-gray-800 text-gray-300">{{ item.status }}</span>
          </p>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="query && !loading" class="text-center py-20 text-gray-500">
      <PhMagnifyingGlass class="w-16 h-16 mx-auto mb-4 opacity-50" />
      <p class="text-xl">No results found for "{{ query }}"</p>
    </div>

  </div>

  <!-- Quick Watch Modal (Movies) -->
  <div v-if="showWatchModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm" @click.self="closeWatchModal">
    <div class="bg-surface border border-gray-800 rounded-2xl shadow-2xl max-w-md w-full p-6 animate-in zoom-in-95 duration-200">
      <h3 class="text-xl font-bold text-white mb-1 flex justify-between items-start">
        <span class="flex items-center gap-2">
          <PhFilmSlate class="w-5 h-5 text-primary" /> Log Watch
        </span>
        <button @click="closeWatchModal" class="text-gray-500 hover:text-white text-2xl leading-none">&times;</button>
      </h3>
      <p v-if="watchTarget" class="text-gray-400 text-sm mb-6 truncate">{{ watchTarget.title }}</p>

      <form @submit.prevent="submitWatch" class="space-y-6">
        <div>
          <label class="block text-sm font-medium text-gray-300 mb-2">Rating <span class="text-gray-500">(optional)</span></label>
          <StarRating v-model:rating="watchForm.rating" />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-300 mb-2">Notes <span class="text-gray-500">(optional)</span></label>
          <textarea
            v-model="watchForm.note"
            class="input-field w-full h-24 resize-none"
            placeholder="What did you think?"
          ></textarea>
        </div>

        <div class="flex justify-end gap-3 pt-2">
          <button type="button" @click="closeWatchModal" class="btn-secondary">Cancel</button>
          <button type="submit" :disabled="submitting" class="btn-primary">
            {{ submitting ? 'Saving...' : 'Save Log' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
