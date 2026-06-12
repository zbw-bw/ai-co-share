<script setup lang="ts">
import { useData } from 'vitepress'

const { frontmatter } = useData()

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
}
</script>

<template>
  <div class="article-header">
    <!-- 大标题（frontmatter title） -->
    <h1 class="article-title">{{ frontmatter.title }}</h1>

    <!-- Meta 信息行 -->
    <div class="article-meta">
      <!-- 日期 -->
      <span v-if="frontmatter.date" class="meta-item">
        <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
          <rect x="1" y="2" width="11" height="10" rx="2" stroke="currentColor" stroke-width="1.2"/>
          <path d="M4 1v2M9 1v2M1 5h11" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
        </svg>
        {{ formatDate(String(frontmatter.date)) }}
      </span>

      <!-- 作者（排除 unknown） -->
      <span v-if="frontmatter.author && frontmatter.author !== 'unknown'" class="meta-item">
        <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
          <circle cx="6.5" cy="4.5" r="2.5" stroke="currentColor" stroke-width="1.2"/>
          <path d="M1.5 11.5c0-2.761 2.239-5 5-5s5 2.239 5 5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
        </svg>
        {{ frontmatter.author }}
      </span>

      <!-- 原始链接 -->
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
        原始链接 ↗
      </a>
    </div>

    <!-- 标签行 -->
    <div v-if="frontmatter.tags?.length" class="meta-tags">
      <span v-for="tag in frontmatter.tags" :key="tag" class="meta-tag">{{ tag }}</span>
    </div>

    <!-- 分隔线 -->
    <div class="article-divider" />
  </div>
</template>

<style scoped>
.article-header {
  margin-bottom: 40px;
}

/* 大标题 */
.article-title {
  font-size: 2rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1.25;
  margin: 0 0 20px;
  color: var(--vp-c-text-1);
  border: none !important;
  padding: 0 !important;
}

.dark .article-title {
  background: linear-gradient(135deg, #e2e8f0 0%, #94a3b8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Meta 信息行 */
.article-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 14px;
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 0.82rem;
  color: var(--vp-c-text-3);
  font-family: 'JetBrains Mono', monospace;
}

.meta-item svg {
  flex-shrink: 0;
  opacity: 0.6;
}

.meta-source {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 0.82rem;
  font-family: 'JetBrains Mono', monospace;
  color: var(--vp-c-brand-1) !important;
  text-decoration: none !important;
  font-weight: 500;
  transition: opacity 0.2s;
}

.meta-source:hover {
  opacity: 0.75;
}

/* 标签行 */
.meta-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 28px;
}

.meta-tag {
  font-size: 0.7rem;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: 100px;
  background: var(--vp-c-brand-soft);
  color: var(--vp-c-brand-1);
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 0.02em;
}

/* 分隔线 */
.article-divider {
  height: 1px;
  background: var(--vp-c-divider);
  margin-bottom: 40px;
}
</style>
