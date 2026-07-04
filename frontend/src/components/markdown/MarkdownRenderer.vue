<template>
  <div class="markdown-body" ref="container" v-html="renderedHtml"></div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'

const props = defineProps<{
  content: string
}>()

const container = ref<HTMLDivElement | null>(null)

/* ---- Markdown-It setup ---- */
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  breaks: true,
  highlight: (str: string, lang: string): string => {
    const language = lang && hljs.getLanguage(lang) ? lang : ''
    let highlighted: string
    if (language) {
      try {
        highlighted = hljs.highlight(str, {
          language,
          ignoreIllegals: true,
        }).value
      } catch {
        highlighted = md.utils.escapeHtml(str)
      }
    } else {
      highlighted = md.utils.escapeHtml(str)
    }
    const langLabel = language || 'text'
    return [
      '<div class="code-block">',
      '<div class="code-header">',
      `<span class="code-lang">${langLabel}</span>`,
      '<button class="copy-btn" data-code="' +
        md.utils.escapeHtml(str) +
        '">复制</button>',
      '</div>',
      '<div class="code-body"><pre><code class="hljs' +
        (language ? ` language-${language}` : '') +
        '">' +
        highlighted +
        '</code></pre></div>',
      '</div>',
    ].join('')
  },
})

const renderedHtml = computed(() => md.render(props.content))

/* ---- Wire up copy buttons after render ---- */
watch(
  renderedHtml,
  () => {
    nextTick(() => {
      if (!container.value) return
      container.value.querySelectorAll('.copy-btn').forEach((el) => {
        // Avoid duplicate listeners
        if ((el as HTMLElement).dataset._listener) return
        ;(el as HTMLElement).dataset._listener = '1'
        el.addEventListener('click', () => {
          const code = el.getAttribute('data-code') || ''
          navigator.clipboard.writeText(code).then(() => {
            el.textContent = '已复制'
            setTimeout(() => {
              el.textContent = '复制'
            }, 2000)
          })
        })
      })
    })
  },
  { immediate: true },
)
</script>
