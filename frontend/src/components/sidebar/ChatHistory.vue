<template>
  <div class="flex-1 min-h-0 flex flex-col px-3 mt-4">
    <div class="text-xs font-medium text-secondary px-3 mb-2">最近对话</div>
    <div class="flex-1 overflow-y-auto space-y-0.5">
      <ChatHistoryItem
        v-for="(msg, i) in recentMessages"
        :key="i"
        :title="msg.text"
        :time="formatRelativeTime(msg.id)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { inject, computed } from 'vue'
import ChatHistoryItem from './ChatHistoryItem.vue'
import type { ChatState } from '@/composables/useChatState'

const chatState = inject<ChatState>('chatState')!

const recentMessages = computed(() => {
  const msgs = chatState.messages.value.filter((m) => m.role === 'user')
  return msgs.slice(-10).reverse()
})

function formatRelativeTime(id: string): string {
  const ts = parseInt(id, 10)
  if (isNaN(ts)) return ''
  const diff = Date.now() - ts
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  const d = new Date(ts)
  return `${d.getMonth() + 1}/${d.getDate()}`
}
</script>
