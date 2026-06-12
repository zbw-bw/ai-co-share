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
</script>

<template>
  <div class="article-list">
    <div v-if="!articles.length" class="empty-state">
      <p class="empty-icon">📭</p>
      <p>{{ emptyText ?? '暂无文章，快来第一个分享吧！' }}</p>
      <code class="empty-hint">/ai-co-share &lt;URL&gt;</code>
    </div>

    <a
      v-for="article in articles"
      :key="article.url"
      :href="withBase(article.url)"
      class="article-card"
    >
      <div class="card-main">
        <h3 class="card-title">{{ article.frontmatter.title ?? article.url }}</h3>
        <div class="card-meta">
          <span v-if="article.frontmatter.date" class="meta-date">
            {{ new Date(article.frontmatter.date).toLocaleDateString('zh-CN') }}
          </span>
          <span v-if="article.frontmatter.author" class="meta-author">
            @{{ article.frontmatter.author }}
          </span>
        </div>
        <div v-if="article.frontmatter.tags?.length" class="card-tags">
          <span v-for="tag in article.frontmatter.tags" :key="tag" class="tag">{{ tag }}</span>
        </div>
      </div>
      <span class="card-arrow">→</span>
    </a>
  </div>
</template>

<style scoped>
.article-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 24px;
}

.article-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border: 1px solid var(--vp-c-divider);
  border-left: 3px solid var(--vp-c-brand-1);
  border-radius: 8px;
  text-decoration: none;
  color: inherit;
  background: var(--vp-c-bg-soft);
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.15s;
}

.article-card:hover {
  border-color: var(--vp-c-brand-1);
  box-shadow: 0 0 0 1px var(--vp-c-brand-1), 0 4px 20px rgba(0, 229, 179, 0.12);
  transform: translateX(3px);
}

.card-main { flex: 1; min-width: 0; }

.card-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 8px;
  color: var(--vp-c-text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-meta {
  display: flex;
  gap: 12px;
  font-size: 0.8rem;
  color: var(--vp-c-text-3);
  margin-bottom: 8px;
}

.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag {
  font-size: 0.72rem;
  padding: 2px 8px;
  border-radius: 12px;
  background: var(--vp-c-brand-soft);
  color: var(--vp-c-brand-1);
  font-family: 'JetBrains Mono', monospace;
}

.card-arrow {
  font-size: 1.2rem;
  color: var(--vp-c-brand-1);
  opacity: 0;
  margin-left: 16px;
  transition: opacity 0.2s, transform 0.2s;
}

.article-card:hover .card-arrow {
  opacity: 1;
  transform: translateX(4px);
}

.empty-state {
  text-align: center;
  padding: 48px 24px;
  color: var(--vp-c-text-3);
  border: 1px dashed var(--vp-c-divider);
  border-radius: 8px;
}

.empty-icon { font-size: 2rem; margin-bottom: 8px; }

.empty-hint {
  display: inline-block;
  margin-top: 12px;
  padding: 4px 12px;
  background: var(--vp-c-bg-soft);
  border-radius: 6px;
  font-size: 0.85rem;
  color: var(--vp-c-brand-1);
}
</style>
