<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import client from '@/api/client'
import { useToastStore } from '@/stores/toast'
import { PhCloudArrowUp, PhUploadSimple, PhShieldCheck, PhTrash } from '@phosphor-icons/vue'

const authStore = useAuthStore()
const toast = useToastStore()

const isSyncing = ref(false)
const selectedFile = ref(null)
const isImporting = ref(false)
const skippedItems = ref([])
const skippedItemsVisible = ref(false)
const isClearing = ref(false)
const isClearingLibrary = ref(false)

const triggerSync = async () => {
  isSyncing.value = true
  try {
    const res = await client.post('/admin/sync')
    toast.success(`Sync finished: Added ${res.added} items, updated ${res.updated}`)
  } catch (err) {
    toast.error('Sync failed')
  } finally {
    isSyncing.value = false
  }
}

const handleFileSelect = (evt) => {
  selectedFile.value = evt.target.files[0]
}

const uploadTrakt = async () => {
  if (!selectedFile.value) {
    toast.error('No file selected')
    return
  }

  const formData = new FormData()
  formData.append('file', selectedFile.value)

  isImporting.value = true
  skippedItems.value = []
  try {
    const res = await client.post('/admin/import/trakt', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 600000
    })
    skippedItems.value = res.skipped || []
    const skippedMsg = res.skipped?.length > 0 ? ` (+${res.skipped.length} Skipped)` : ''
    toast.success(`Trakt Import Complete! Movies: ${res.imported_movies || 0}, Episodes: ${res.imported_episodes || 0}${skippedMsg}`)
    selectedFile.value = null
  } catch (err) {
    toast.error(err.response?.data?.error || 'Import failed')
  } finally {
    isImporting.value = false
    // reset input
    document.getElementById('trakt-file').value = ''
  }
}

const clearHistory = async () => {
  if (!confirm('Are you absolutely sure? This will permanently delete your entire watch history. This action cannot be undone.')) {
    return
  }

  isClearing.value = true
  try {
    await client.delete('/history')
    toast.success('Watch history cleared successfully')
  } catch (err) {
    toast.error('Failed to clear watch history')
  } finally {
    isClearing.value = false
  }
}

const clearLibrary = async () => {
  if (!confirm('Are you absolutely sure? This will permanently delete ALL movies and TV shows from your library. This will also delete all associated watch history. This action cannot be undone.')) {
    return
  }

  isClearingLibrary.value = true
  try {
    await client.delete('/admin/library')
    toast.success('Library cleared successfully')
  } catch (err) {
    toast.error('Failed to clear library')
  } finally {
    isClearingLibrary.value = false
  }
}
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    
    <div class="mb-8 border-b border-gray-800 pb-4">
      <h1 class="text-3xl font-extrabold text-white tracking-tight">Settings</h1>
      <p class="text-gray-400 mt-1">Manage sync, imports, and account details</p>
    </div>

    <div class="space-y-8">
      
      <!-- Account Info -->
      <section class="bg-surface border border-gray-800 rounded-xl p-6 shadow-sm flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 bg-gray-800 rounded-full flex justify-center items-center text-gray-500">
            <PhShieldCheck class="w-6 h-6" weight="fill" />
          </div>
          <div>
            <h3 class="text-lg font-bold text-white">Logged in as: {{ authStore.user?.username }}</h3>
            <p class="text-sm font-mono text-gray-500 mt-1">Role: Administrator (Account ID: {{ authStore.user?.id }})</p>
          </div>
        </div>
      </section>

      <!-- Sync Details -->
      <section class="bg-surface border border-gray-800 rounded-xl p-6 shadow-sm">
        <h2 class="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <PhCloudArrowUp class="text-primary w-6 h-6" /> Backstage Sync
        </h2>
        <p class="text-gray-400 mb-6 text-sm">
          The system automatically checks for new episodes of your <strong>"Returning Series"</strong> every Tuesday and Friday night. 
          You can manually trigger a full synchronization with TMDB immediately using the button below.
        </p>

        <button 
          @click="triggerSync" 
          :disabled="isSyncing"
          class="btn-primary flex items-center gap-2"
        >
          <span v-if="isSyncing" class="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></span>
          {{ isSyncing ? 'Syncing with TMDB...' : 'Trigger Full Sync Now' }}
        </button>
      </section>

      <!-- Trakt Import -->
      <section class="bg-surface border border-gray-800 rounded-xl p-6 shadow-sm">
        <h2 class="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <PhUploadSimple class="text-secondary w-6 h-6" /> Trakt.tv JSON Import
        </h2>
        <p class="text-gray-400 mb-4 text-sm max-w-2xl">
          Upload a JSON export from Trakt.tv to automatically import your watched movies and TV series history.
          This process runs entirely on the backend and adds missing metadata from TMDB in the background. Note: this might take several minutes depending on the file size.
        </p>

        <form @submit.prevent="uploadTrakt" class="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
          <div class="flex-grow w-full">
            <input 
              id="trakt-file"
              type="file" 
              accept=".json" 
              @change="handleFileSelect"
              class="block w-full text-sm text-gray-400 file:mr-4 file:py-2.5 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-secondary/10 file:text-secondary hover:file:bg-secondary/20 cursor-pointer"
            />
          </div>
          <button 
            type="submit" 
            :disabled="isImporting || !selectedFile"
            class="btn-secondary whitespace-nowrap"
            :class="{'opacity-50 cursor-not-allowed': isImporting || !selectedFile}"
          >
             {{ isImporting ? 'Importing... (Please wait)' : 'Upload & Import' }}
          </button>
        </form>

        <!-- Skipped Items List -->
        <div v-if="skippedItems.length > 0" class="mt-6 border border-amber-900/30 bg-amber-900/5 rounded-lg overflow-hidden">
          <button 
            @click="skippedItemsVisible = !skippedItemsVisible"
            class="w-full flex items-center justify-between p-3 text-amber-500 font-bold text-sm hover:bg-amber-900/10 transition-colors"
          >
            <span>⚠️ {{ skippedItems.length }} Items were skipped during last import</span>
            <span class="text-xs">{{ skippedItemsVisible ? 'Hide Details ▲' : 'Show Details ▼' }}</span>
          </button>
          
          <div v-if="skippedItemsVisible" class="max-h-60 overflow-y-auto border-t border-amber-900/30">
            <table class="w-full text-left text-xs text-gray-400">
              <thead class="bg-gray-900 text-gray-500 uppercase">
                <tr>
                  <th class="px-4 py-2">Title</th>
                  <th class="px-4 py-2">Reason</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-800">
                <tr v-for="(item, idx) in skippedItems" :key="idx" class="hover:bg-gray-800/30">
                  <td class="px-4 py-2 font-medium text-gray-300">{{ item.title }}</td>
                  <td class="px-4 py-2 text-amber-600/80">{{ item.reason }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- Danger Zone -->
      <section class="bg-red-900/10 border border-red-900/50 rounded-xl p-6 shadow-sm">
        <h2 class="text-xl font-bold text-red-500 mb-4 flex items-center gap-2">
          <PhTrash class="w-6 h-6" /> Danger Zone
        </h2>
        <p class="text-gray-400 mb-6 text-sm">
          Permanently remove your entire watch history. This includes all logged movies and TV show episodes. 
          Your library items (added shows and movies) will remain, but their watch status will be reset.
        </p>

        <div class="flex flex-col sm:flex-row gap-4">
          <button 
            @click="clearHistory" 
            :disabled="isClearing || isClearingLibrary"
            class="bg-red-600 hover:bg-red-700 text-white px-6 py-2.5 rounded-lg font-bold transition-all disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <span v-if="isClearing" class="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></span>
            {{ isClearing ? 'Clearing History...' : 'Clear Entire Watch History' }}
          </button>

          <button 
            @click="clearLibrary" 
            :disabled="isClearing || isClearingLibrary"
            class="bg-transparent hover:bg-red-600/10 text-red-500 border border-red-500/50 hover:border-red-500 px-6 py-2.5 rounded-lg font-bold transition-all disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <span v-if="isClearingLibrary" class="animate-spin rounded-full h-4 w-4 border-2 border-red-500 border-t-transparent"></span>
            {{ isClearingLibrary ? 'Clearing Library...' : 'Clear Entire Library' }}
          </button>
        </div>
      </section>

    </div>
  </div>
</template>
