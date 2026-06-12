<script setup lang="ts">
import { useData } from 'vitepress'

const { frontmatter } = useData()

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
}
</script>

<template>
  <div class="article-meta-card">
    <!-- 日期 -->
    <span v-if="frontmatter.date" class="meta-item">
      <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
        <rect x="1" y="2" width="11" height="10" rx="2" stroke="currentColor" stroke-width="1.2"/>
        <path d="M4 1v2M9 1v2M1 5h11" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
      </svg>
      {{ formatDate(String(frontmatter.date)) }}
    </span>

    <!-- 作者 -->
    <span v-if="frontmatter.author && frontmatter.author !== 'unknown'" class="meta-item">
      <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
        <circle cx="6.5" cy="4.5" r="2.5" stroke="currentColor" stroke-width="1.2"/>
        <path d="M1.5 11.5c0-2.761 2.239-5 5-5s5 2.239 5 5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
      </svg>
      {{ frontmatter.author }}
    </span>

    <!-- 来源链接 -->
    <a
      v-if="frontmatter.source"
      :href="frontmatter.source"
      target="_blank"
      rel="noopener"
      class="meta-source"
    >
      <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
        <path d="M5 2H2a1 1 0 00-1 1v7a1 1 0 001 1h7a1 1 0 001-1V7" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
        <path d="M8 1h3v3M11 1L6 6" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      原始链接
    </a>

    <!-- 标签 -->
    <div v-if="frontmatter.tags?.length" class="meta-tags">
      <span v-for="tag in frontmatter.tags" :key="tag" class="meta-tag">{{ tag }}</span>
    </div>
  </div>
</template>
