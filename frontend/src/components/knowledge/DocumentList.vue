<template>
  <div class="space-y-2">
    <div class="text-xs font-medium text-secondary">
      已索引文档 ({{ chatState.documents.value.length }})
    </div>

    <div
      v-if="chatState.documents.value.length === 0"
      class="text-sm text-secondary p-4 rounded-xl bg-hover"
    >
      暂无文档
    </div>

    <div
      v-for="doc in chatState.documents.value"
      :key="doc.id"
      class="flex items-center justify-between p-4 rounded-xl border border-border bg-white transition-colors duration-150 hover:bg-hover"
    >
      <div class="min-w-0 flex-1">
        <div class="text-sm font-medium text-text truncate">{{ doc.filename }}</div>
        <div class="text-xs text-secondary mt-0.5">
          {{ doc.file_type.toUpperCase() }} · {{ chatState.formatSize(doc.file_size) }} ·
          {{ chatState.formatDate(doc.created_at) }}
        </div>
      </div>
      <button
        class="ml-4 px-3 py-1.5 rounded-lg text-xs text-secondary border border-border hover:text-danger hover:border-danger/30 hover:bg-danger/5 transition-all duration-150 flex-shrink-0"
        @click="chatState.handleDelete(doc.id, doc.filename)"
      >
        删除
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { inject } from 'vue'
import type { ChatState } from '@/composables/useChatState'

const chatState = inject<ChatState>('chatState')!
</script>
