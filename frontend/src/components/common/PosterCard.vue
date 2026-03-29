<script setup>
import { usePoster } from '@/composables/usePoster'
import { computed } from 'vue'

const props = defineProps({
  src: { type: String, default: null },
  alt: { type: String, default: 'Poster' },
  tmdbId: { type: Number, default: 0 },
  ratio: { type: String, default: 'aspect-[2/3]' }
})

const { getPosterUrl, getPlaceholderGradient } = usePoster()

const posterUrl = computed(() => getPosterUrl(props.src))
const gradient = computed(() => getPlaceholderGradient(props.tmdbId))
const hasImage = computed(() => props.src && props.src !== '' && !props.src.includes('placeholder'))

</script>

<template>
  <div :class="['relative overflow-hidden bg-gray-900 group rounded-md', ratio]">
    <!-- Image -->
    <img 
      v-if="hasImage"
      :src="posterUrl" 
      :alt="alt" 
      class="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
      loading="lazy"
    />
    <!-- Fallback Gradient -->
    <div 
      v-else 
      :class="['absolute inset-0 w-full h-full bg-gradient-to-br', gradient, 'flex items-center justify-center p-4 text-center']"
    >
      <span class="text-sm font-semibold text-white/50 break-words line-clamp-3">{{ alt }}</span>
    </div>

    <!-- Optional Hover Overlay slot -->
    <slot name="overlay"></slot>
  </div>
</template>
