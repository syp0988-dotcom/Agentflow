<template>
  <div class="relative">
    <input
      ref="inputRef"
      type="file"
      multiple
      accept=".pdf,.docx,.doc,.txt,.md,.markdown"
      class="hidden"
      @change="onFileSelect"
    />
    <button
      class="w-8 h-8 rounded-full flex items-center justify-center text-secondary hover:text-text hover:bg-hover transition-all duration-150"
      title="上传文件"
      @click="inputRef?.click()"
    >
      <Paperclip class="w-4 h-4" />
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Paperclip } from 'lucide-vue-next'

const emit = defineEmits<{ upload: [files: File[]] }>()
const inputRef = ref<HTMLInputElement | null>(null)

function onFileSelect(e: Event) {
  const target = e.target as HTMLInputElement
  if (!target.files?.length) return
  emit('upload', Array.from(target.files))
  target.value = ''
}
</script>
