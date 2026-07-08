<template>
  <div class="flex items-center gap-2">
    <button
      v-for="action in actions"
      :key="action.label"
      class="flex items-center gap-2 px-4 py-2 rounded-full border border-border text-sm text-secondary hover:text-text hover:bg-hover transition-all duration-150 ease-out"
      @click="action.handler()"
    >
      <component :is="action.icon" class="w-4 h-4" />
      <span>{{ action.label }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { inject } from 'vue'
import {
  Code,
  BookOpen,
  PenSquare,
  Search,
  Lightbulb,
} from 'lucide-vue-next'
import type { Component } from 'vue'
import type { ChatState } from '@/composables/useChatState'

const chatState = inject<ChatState>('chatState')!

interface QuickAction {
  icon: Component
  label: string
  handler: () => void
}

const actions: QuickAction[] = [
  { icon: Code, label: 'Code', handler: () => chatState.handleSend('帮我写一段 Python 代码') },
  { icon: BookOpen, label: 'Learn', handler: () => chatState.handleSend('解释一下什么是机器学习') },
  { icon: PenSquare, label: 'Write', handler: () => chatState.handleSend('帮我写一篇文章') },
  { icon: Search, label: 'Research', handler: () => chatState.handleSend('搜索最新的 AI 技术趋势') },
  { icon: Lightbulb, label: 'Knowledge', handler: () => chatState.handleSend('从知识库查找相关信息') },
]
</script>
