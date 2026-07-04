<template>
  <a
    :href="url"
    target="_blank"
    rel="noopener noreferrer"
    class="source-card flex items-start gap-3 p-4 rounded-xl border border-border bg-white hover:bg-hover"
  >
    <!-- Favicon placeholder -->
    <div
      class="w-8 h-8 rounded-lg bg-code-bg flex items-center justify-center text-xs font-bold text-secondary flex-shrink-0 overflow-hidden"
    >
      <img v-if="favicon" :src="favicon" alt="" class="w-full h-full object-contain" />
      <span v-else>{{ domain.charAt(0).toUpperCase() }}</span>
    </div>

    <div class="min-w-0 flex-1">
      <div class="text-sm font-medium text-text truncate">{{ title }}</div>
      <div class="text-xs text-secondary truncate mt-0.5">{{ domain }}</div>
      <div v-if="snippet" class="text-xs text-secondary mt-1.5 line-clamp-2">
        {{ snippet }}
      </div>
    </div>

    <ExternalLink class="w-3.5 h-3.5 text-secondary flex-shrink-0 mt-1" />
  </a>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ExternalLink } from 'lucide-vue-next'

const props = defineProps<{
  title: string
  url: string
  favicon?: string
  snippet?: string
}>()

const domain = computed(() => {
  try {
    return new URL(props.url).hostname.replace('www.', '')
  } catch {
    return props.url
  }
})
</script>
