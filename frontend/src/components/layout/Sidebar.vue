<template>
  <aside
    class="w-[300px] flex-shrink-0 h-full flex flex-col bg-sidebar-bg border-r border-border select-none"
  >
    <!-- Logo -->
    <div class="px-5 pt-5 pb-4">
      <div class="flex items-center gap-3">
        <div
          class="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-white font-bold text-sm"
        >
          OF
        </div>
        <span class="text-base font-semibold text-text">OmniForge</span>
      </div>
    </div>

    <!-- Segmented Control -->
    <SegmentedControl />

    <!-- Nav items -->
    <nav class="px-3 mt-3 space-y-0.5">
      <NavItem
        v-for="item in navItems"
        :key="item.label"
        :icon="item.icon"
        :label="item.label"
        :active="item.active"
        @click="item.action?.()"
      />
    </nav>

    <!-- Recent Chats -->
    <ChatHistory />

    <!-- Spacer -->
    <div class="flex-1 min-h-0" />

    <!-- User Profile -->
    <UserProfile />
  </aside>
</template>

<script setup lang="ts">
import { inject } from 'vue'
import { Plus, Folder, BookOpen, Wrench, Settings } from 'lucide-vue-next'
import SegmentedControl from '@/components/sidebar/SegmentedControl.vue'
import NavItem from '@/components/sidebar/NavItem.vue'
import ChatHistory from '@/components/sidebar/ChatHistory.vue'
import UserProfile from '@/components/sidebar/UserProfile.vue'
import type { ChatState } from '@/composables/useChatState'

const chatState = inject<ChatState>('chatState')!

const navItems = [
  { icon: Plus, label: '新对话', active: false, action: () => chatState.newChat() },
  { icon: Folder, label: '项目', active: false, action: undefined },
  { icon: BookOpen, label: '知识库', active: false, action: () => { chatState.activeSection.value = 'knowledge' } },
  { icon: Wrench, label: '工具', active: false, action: undefined },
  { icon: Settings, label: '设置', active: false, action: undefined },
]
</script>
