<template>
  <div class="flex items-center gap-2">
    <button
      v-for="action in actions"
      :key="action.label"
      class="flex items-center gap-2 px-4 py-2 rounded-full border border-border text-sm text-secondary hover:text-text hover:bg-hover transition-all duration-150 ease-out"
    >
      <component :is="action.icon" class="w-4 h-4" />
      <span>{{ action.label }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import {
  Code,
  BookOpen,
  PenSquare,
  Search,
  Lightbulb,
} from 'lucide-vue-next'
import type { Component } from 'vue'

const actions: { icon: Component; label: string }[] = [
  { icon: Code, label: 'Code' },
  { icon: BookOpen, label: 'Learn' },
  { icon: PenSquare, label: 'Write' },
  { icon: Search, label: 'Research' },
  { icon: Lightbulb, label: 'Knowledge' },
]
</script>
