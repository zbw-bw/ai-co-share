<script setup lang="ts">
import { withBase } from 'vitepress'

defineProps<{
  articles: Array<{
    url: string
    frontmatter: {
      title?: string
      date?: string
      author?: string
      tags?: string[]
      source?: string
    }
  }>
  emptyText?: string
}>()

function formatDate(dateStr: string) {
  const d = new Date(dateStr)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' })
}
</script>

<template>
  <div class="article-list">
    <!-- Empty state -->
    <div v-if="!articles.length" class="empty-state">
      <div class="empty-icon">📭</div>
      <p class="empty-text">{{ emptyText ?? '暂无文章，快来第一个分享吧！' }}</p>
      <p class="empty-hint">在 CatDesk 中输入 <span class="hint-cmd">/ai-co-share &lt;URL&gt;</span> 即可分享</p>
    </div>

    <!-- Article cards -->
    <a
      v-for="(article, i) in articles"
      :key="article.url"
      :href="withBase(article.url)"
      class="article-card"
      :style="`--delay: ${i * 60}ms`"
    >
      <div class="card-left">
        <div v-if="article.frontmatter.date" class="card-date">
          {{ formatDate(article.frontmatter.date) }}
        </div>
        <h3 class="card-title">{{ article.frontmatter.title ?? article.url }}</h3>
        <div class="card-footer">
          <span v-if="article.frontmatter.author" class="card-author">
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><circle cx="6" cy="4" r="2.5" stroke="currentColor" stroke-width="1.2"/><path d="M1.5 10.5c0-2.485 2.015-4.5 4.5-4.5s4.5 2.015 4.5 4.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
            {{ article.frontmatter.author }}
          </span>
          <div v-if="article.frontmatter.tags?.length" class="card-tags">
            <span v-for="tag in article.frontmatter.tags" :key="tag" class="tag">{{ tag }}</span>
          </div>
        </div>
      </div>
      <div class="card-arrow">
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path d="M4 9h10M10 5l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
    </a>
  </div>
</template>

<style scoped>
.article-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 28px;
}

/* ── Empty state ─────────────────────── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 64px 24px;
  border: 1px dashed var(--vp-c-divider);
  border-radius: 16px;
  text-align: center;
}

.empty-icon { font-size: 2.5rem; }

.empty-text {
  font-size: 0.95rem;
  color: var(--vp-c-text-3);
  margin: 0;
}

.empty-hint {
  font-size: 0.82rem;
  color: var(--vp-c-text-3);
  margin: 0;
}

.hint-cmd {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.82em;
  color: var(--vp-c-brand-1);
  background: none;
  border: none;
  padding: 0;
}

/* ── Article card ────────────────────── */
.article-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 24px;
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 12px;
  text-decoration: none;
  color: inherit;
  animation: slideIn 0.4s ease both;
  animation-delay: var(--delay, 0ms);
  transition: background 0.2s, border-color 0.2s, box-shadow 0.2s, transform 0.15s;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}

.article-card:hover {
  background: var(--vp-c-bg-elv);
  border-color: var(--vp-c-brand-1);
  box-shadow: 0 4px 24px rgba(0,0,0,0.08), 0 0 0 1px var(--vp-c-brand-1);
  transform: translateY(-2px);
}

/* ── Card content ────────────────────── */
.card-left { flex: 1; min-width: 0; }

.card-date {
  font-size: 0.75rem;
  color: var(--vp-c-text-3);
  font-weight: 500;
  margin-bottom: 6px;
  font-family: 'JetBrains Mono', monospace;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 10px;
  color: var(--vp-c-text-1);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-footer {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.card-author {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.78rem;
  color: var(--vp-c-text-3);
  font-weight: 500;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.tag {
  font-size: 0.7rem;
  font-weight: 500;
  padding: 2px 9px;
  border-radius: 100px;
  background: var(--vp-c-brand-soft);
  color: var(--vp-c-brand-1);
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 0.02em;
}

/* ── Arrow ───────────────────────────── */
.card-arrow {
  color: var(--vp-c-brand-1);
  opacity: 0;
  transform: translateX(-6px);
  transition: opacity 0.2s, transform 0.2s;
  flex-shrink: 0;
}

.article-card:hover .card-arrow {
  opacity: 1;
  transform: translateX(0);
}
</style>
