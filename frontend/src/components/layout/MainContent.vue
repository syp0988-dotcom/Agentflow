<template>
  <main class="flex-1 flex flex-col h-full min-w-0">
    <!-- Content area -->
    <div class="flex-1 overflow-y-auto">
      <ChatView v-if="chatState.activeSection.value === 'chat'" />
      <KnowledgeView v-else-if="chatState.activeSection.value === 'knowledge'" />
      <ProjectsView v-else-if="chatState.activeSection.value === 'projects'" />
      <ArtifactsView v-else-if="chatState.activeSection.value === 'artifacts'" />
      <ModelsSettings v-else-if="chatState.activeSection.value === 'settings'" />
      <ChatView v-else />
    </div>
    <!-- Folder reminder modal (global, shown from any section) -->
    <FolderReminderModal />
  </main>
</template>

<script setup lang="ts">
import { inject } from 'vue'
import ChatView from '@/components/chat/ChatView.vue'
import KnowledgeView from '@/components/knowledge/KnowledgeView.vue'
import ProjectsView from '@/components/projects/ProjectsView.vue'
import ArtifactsView from '@/components/ArtifactsView.vue'
import ModelsSettings from '@/components/settings/ModelsSettings.vue'
import FolderReminderModal from '@/components/projects/FolderReminderModal.vue'
import type { ChatState } from '@/composables/useChatState'

const chatState = inject<ChatState>('chatState')!
</script>
