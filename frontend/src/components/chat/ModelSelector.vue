<template>
  <div class="relative">
    <button
      class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-full border border-border text-secondary hover:text-text hover:bg-hover transition-all duration-150"
      @click="open = !open"
    >
      <Zap class="w-3.5 h-3.5" />
      <span>{{ currentModel }}</span>
      <ChevronDown
        class="w-3 h-3 transition-transform duration-150"
        :class="{ 'rotate-180': open }"
      />
    </button>

    <Transition name="dropdown">
      <div
        v-if="open"
        v-click-outside="() => (open = false)"
        class="absolute right-0 top-full mt-1 w-44 bg-white border border-border rounded-xl shadow-lg py-1 z-50"
      >
        <button
          v-for="model in models"
          :key="model"
          class="w-full flex items-center gap-2 px-3 py-2 text-sm text-text hover:bg-hover transition-colors duration-150"
          :class="{ 'bg-hover font-medium': model === currentModel }"
          @click="currentModel = model; open = false"
        >
          <Zap class="w-3.5 h-3.5 text-secondary" />
          {{ model }}
        </button>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Zap, ChevronDown } from 'lucide-vue-next'

const open = ref(false)
const currentModel = ref('DeepSeek V3')
const models = ['DeepSeek V3', 'DeepSeek R1', 'GPT-4o']

const vClickOutside = {
  mounted(el: HTMLElement, binding: { value: () => void }) {
    el.__clickOutside = (e: MouseEvent) => {
      if (!el.contains(e.target as Node)) binding.value()
    }
    document.addEventListener('click', el.__clickOutside)
  },
  unmounted(el: HTMLElement) {
    document.removeEventListener('click', el.__clickOutside)
  },
}
</script>

<style scoped>
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 150ms ease-out;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(4px);
}
</style>
