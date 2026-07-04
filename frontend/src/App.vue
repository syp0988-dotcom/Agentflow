<template>
  <div class="flex h-screen bg-bg">
    <Sidebar />
    <MainContent />
  </div>
</template>

<script setup lang="ts">
import { provide } from 'vue'
import { useChatState } from '@/composables/useChatState'
import Sidebar from '@/components/layout/Sidebar.vue'
import MainContent from '@/components/layout/MainContent.vue'

const chatState = useChatState()
provide('chatState', chatState)
</script>
