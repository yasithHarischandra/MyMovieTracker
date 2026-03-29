<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: { type: Number, required: true },
  max: { type: Number, required: true },
  color: { type: String, default: 'bg-primary' },
  height: { type: String, default: 'h-1.5' },
  showPercentage: { type: Boolean, default: false }
})

const percentage = computed(() => {
  if (props.max === 0) return 0
  return Math.min(100, Math.max(0, (props.value / props.max) * 100))
})
</script>

<template>
  <div class="w-full">
    <div class="flex justify-between text-xs mb-1" v-if="showPercentage || $slots.label">
      <span class="text-gray-400 font-medium"><slot name="label"></slot></span>
      <span v-if="showPercentage" class="text-gray-400 font-mono">{{ Math.round(percentage) }}%</span>
    </div>
    <div :class="['w-full bg-gray-800 rounded-full overflow-hidden', height]">
      <div 
        :class="[color, 'h-full rounded-full transition-all duration-500 ease-out']"
        :style="{ width: `${percentage}%` }"
      ></div>
    </div>
  </div>
</template>
