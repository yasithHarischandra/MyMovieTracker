<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import client from '@/api/client'
import { useToastStore } from '@/stores/toast'
import { PhCloudArrowUp, PhUploadSimple, PhShieldCheck } from '@phosphor-icons/vue'

const authStore = useAuthStore()
const toast = useToastStore()

const isSyncing = ref(false)
const selectedFile = ref(null)
const isImporting = ref(false)

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
  try {
    const res = await client.post('/admin/import/trakt', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 600000
    })
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
      </section>

    </div>
  </div>
</template>
