<template>
  <div class="max-w-content mx-auto px-6 py-8 space-y-6">
    <div>
      <h2 class="text-lg font-semibold text-text">Artifacts</h2>
      <p class="text-sm text-secondary mt-1">查看和管理 Agent 生成的代码、文档和产物。</p>
    </div>

    <div class="grid gap-3">
      <div
        v-for="item in artifacts"
        :key="item.title"
        class="flex items-center justify-between p-5 rounded-xl border border-border bg-white transition-colors duration-150 hover:bg-hover"
      >
        <div class="flex items-center gap-4">
          <div
            class="w-10 h-10 rounded-xl bg-code-bg flex items-center justify-center"
          >
            <component :is="item.icon" class="w-5 h-5 text-secondary" />
          </div>
          <div>
            <div class="text-sm font-medium text-text">{{ item.title }}</div>
            <div class="text-xs text-secondary mt-0.5">{{ item.type }} · {{ item.date }}</div>
          </div>
        </div>
        <button
          class="px-4 py-1.5 rounded-lg border border-border text-text text-sm hover:bg-hover transition-colors duration-150"
        >
          查看
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Code, FileText, Brain } from 'lucide-vue-next'
import type { FunctionalComponent, SVGAttributes } from 'vue'

const artifacts: {
  icon: FunctionalComponent<SVGAttributes>
  title: string
  type: string
  date: string
}[] = [
  { icon: Code, title: 'API 路由设计', type: '代码', date: '2026-07-04' },
  { icon: FileText, title: '项目架构文档', type: '文档', date: '2026-07-03' },
  { icon: Brain, title: 'Agent 工作流分析', type: '报告', date: '2026-07-02' },
]
</script>
