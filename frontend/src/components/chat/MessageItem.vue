<template>
  <!-- User message (right-aligned) -->
  <div v-if="msg.role === 'user'" class="flex justify-end">
    <div
      class="max-w-[760px] bg-[#F4F4F5] rounded-2xl px-5 py-3 animate-fade-in"
    >
      <div class="text-sm text-text leading-relaxed whitespace-pre-wrap">{{ msg.text }}</div>
    </div>
  </div>

  <!-- Agent message (left-aligned) -->
  <div v-else class="flex justify-start">
    <div class="max-w-[760px] w-full animate-slide-up">
      <!-- Header -->
      <div class="flex items-center gap-2 mb-3">
        <div
          class="w-6 h-6 rounded-md bg-primary flex items-center justify-center text-white text-[10px] font-bold flex-shrink-0"
        >
          OF
        </div>
        <span class="text-xs font-medium text-secondary">OmniForge</span>
      </div>
      <!-- Content -->
      <MarkdownRenderer :content="msg.text" />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Msg } from '@/types'
import MarkdownRenderer from '@/components/markdown/MarkdownRenderer.vue'

defineProps<{
  msg: Msg
}>()
</script>
