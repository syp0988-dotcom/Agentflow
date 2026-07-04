<template>
  <div class="max-w-content mx-auto px-6 py-8 space-y-6">
    <div>
      <h2 class="text-lg font-semibold text-text">Agent 管理</h2>
      <p class="text-sm text-secondary mt-1">管理 OmniForge 中的自定义智能 Agent，并配置它们的工作流。</p>
    </div>

    <div class="grid gap-3">
      <div
        v-for="agent in agents"
        :key="agent.name"
        class="flex items-center justify-between p-5 rounded-xl border border-border bg-white transition-colors duration-150 hover:bg-hover"
      >
        <div class="flex items-center gap-4">
          <div
            class="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-sm"
            :style="{ backgroundColor: agent.color }"
          >
            {{ agent.initials }}
          </div>
          <div>
            <div class="text-sm font-medium text-text">{{ agent.name }}</div>
            <div class="text-xs text-secondary mt-0.5">{{ agent.description }}</div>
          </div>
        </div>
        <button
          class="px-4 py-1.5 rounded-lg bg-primary text-white text-sm font-medium hover:bg-primary-hover transition-colors duration-150"
        >
          管理
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const agents = [
  {
    name: 'Code Assistant',
    initials: 'CA',
    color: '#7C5CFC',
    description: '擅长修复代码、生成测试用例和优化方案',
  },
  {
    name: 'Research Agent',
    initials: 'RA',
    color: '#E86A33',
    description: '擅长查找资料、总结背景和生成执行策略',
  },
  {
    name: 'Knowledge Agent',
    initials: 'KA',
    color: '#34C759',
    description: '管理和检索知识库中的文档内容',
  },
]
</script>
