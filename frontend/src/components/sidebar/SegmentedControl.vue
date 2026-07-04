<template>
  <div class="px-3 py-2">
    <div class="flex bg-hover rounded-[10px] p-0.5 gap-0.5">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        @click="chatState.activeSection.value = tab.key"
        class="flex-1 px-3 py-1.5 text-xs font-medium rounded-[8px] transition-all duration-150 ease-out"
        :class="
          chatState.activeSection.value === tab.key
            ? 'bg-white text-text shadow-sm'
            : 'text-secondary hover:text-text'
        "
      >
        {{ tab.label }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { inject } from 'vue'
import type { ChatState } from '@/composables/useChatState'
import type { Section } from '@/types'

const chatState = inject<ChatState>('chatState')!

const tabs: { key: Section; label: string }[] = [
  { key: 'chat', label: 'Chat' },
  { key: 'agents', label: 'Agents' },
  { key: 'knowledge', label: 'Knowledge' },
  { key: 'artifacts', label: 'Artifacts' },
]
</script>
