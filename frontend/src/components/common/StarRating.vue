<script setup>
import { computed } from 'vue'
import { PhStar } from '@phosphor-icons/vue'

const props = defineProps({
  rating: { type: Number, default: 0 },
  max: { type: Number, default: 10 },
  readOnly: { type: Boolean, default: false },
  size: { type: String, default: 'md' }
})

const emit = defineEmits(['update:rating'])

const sizes = {
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-8 h-8'
}
const iconSize = computed(() => sizes[props.size] || sizes.md)

const setRating = (val) => {
  if (!props.readOnly) emit('update:rating', val)
}
</script>

<template>
  <div class="flex items-center gap-1" :class="{ 'cursor-pointer': !readOnly }">
    <button 
      v-for="i in max" 
      :key="i"
      type="button"
      @click.prevent="setRating(i)"
      :disabled="readOnly"
      class="focus:outline-none disabled:cursor-default"
      :class="[!readOnly ? 'hover:scale-110 transition-transform' : '']"
    >
      <PhStar 
        :weight="i <= rating ? 'fill' : 'regular'"
        :class="[iconSize, i <= rating ? 'text-warning' : 'text-gray-600 hover:text-warning/50']" 
      />
    </button>
  </div>
</template>
