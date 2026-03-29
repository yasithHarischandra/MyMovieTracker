<script setup>
import { ref } from 'vue'
import { format, parseISO } from 'date-fns'
import StarRating from '@/components/common/StarRating.vue'
import { PhTrash } from '@phosphor-icons/vue'

defineProps({ entry: Object })
const emit = defineEmits(['unwatch', 'update'])

const formatTime = (isoString) => {
  if (!isoString) return ''
  return format(parseISO(isoString), 'MMM do, yyyy h:mm a')
}
</script>

<template>
  <div class="bg-surface border border-gray-800 p-4 rounded-xl flex items-start gap-4 hover:border-gray-700 transition-colors group">
    <div class="flex-grow">
      <div class="flex justify-between items-center mb-2">
        <span class="text-sm font-medium text-gray-400 font-mono">{{ formatTime(entry.watched_at) }}</span>
        <button 
          @click="$emit('unwatch', entry.id)"
          class="text-gray-600 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all p-1"
          title="Remove log"
        >
          <PhTrash class="w-4 h-4" />
        </button>
      </div>
      
      <div class="flex items-center gap-4">
        <StarRating :rating="entry.rating || 0" :readOnly="true" size="sm" />
        <span v-if="entry.note" class="text-sm text-gray-300 italic">"{{ entry.note }}"</span>
        <span v-else class="text-sm text-gray-500 italic">No notes</span>
      </div>
    </div>
  </div>
</template>
