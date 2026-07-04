<template>
  <div
    class="group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors duration-150 ease-out hover:bg-hover"
  >
    <div class="flex-1 min-w-0">
      <div class="text-sm text-text truncate">{{ title }}</div>
      <div class="text-xs text-secondary">{{ time }}</div>
    </div>
    <button
      class="opacity-0 group-hover:opacity-100 w-6 h-6 flex items-center justify-center rounded-md text-secondary hover:text-text hover:bg-border transition-all duration-150"
    >
      <MoreHorizontal class="w-3.5 h-3.5" />
    </button>
  </div>
</template>

<script setup lang="ts">
import { MoreHorizontal } from 'lucide-vue-next'

defineProps<{
  title: string
  time: string
}>()
</script>
