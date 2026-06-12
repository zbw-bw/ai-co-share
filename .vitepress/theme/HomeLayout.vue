<script setup lang="ts">
import { withBase } from 'vitepress'

const categories = [
  {
    key: 'llm',
    icon: '⬡',
    label: 'LLM',
    desc: '大模型 · 提示工程 · RAG · 微调',
    href: '/ai-co-share/llm/',
    color: '#00e5b3',
  },
  {
    key: 'agent',
    icon: '◈',
    label: 'Agent',
    desc: '工作流 · Multi-Agent · Tool Use · MCP',
    href: '/ai-co-share/agent/',
    color: '#4a9eff',
  },
  {
    key: 'tools',
    icon: '⌬',
    label: 'Tools',
    desc: 'Claude Code · Skills · Hooks · 效率工具',
    href: '/ai-co-share/tools/',
    color: '#a78bfa',
  },
  {
    key: 'papers',
    icon: '◻',
    label: 'Papers',
    desc: '论文精读 · 前沿研究 · 实验复现',
    href: '/ai-co-share/papers/',
    color: '#f59e0b',
  },
]
</script>

<template>
  <div class="home-root">
    <!-- Background grid -->
    <div class="bg-grid" aria-hidden="true" />
    <div class="bg-blob bg-blob-1" aria-hidden="true" />
    <div class="bg-blob bg-blob-2" aria-hidden="true" />

    <!-- Nav -->
    <header class="home-nav">
      <a :href="withBase('/')" class="nav-brand">
        <span class="brand-bracket">[</span>
        <span class="brand-text">AI Co-Share</span>
        <span class="brand-bracket">]</span>
      </a>
      <nav class="nav-links">
        <a :href="withBase('/llm/')">LLM</a>
        <a :href="withBase('/agent/')">Agent</a>
        <a :href="withBase('/tools/')">Tools</a>
        <a :href="withBase('/papers/')">Papers</a>
        <a :href="withBase('/weekly/')" class="nav-weekly">周索引 ↗</a>
      </nav>
    </header>

    <!-- Hero -->
    <main class="hero">
      <div class="hero-inner">
        <div class="hero-badge">
          <span class="badge-dot" />
          <span>Team Knowledge Base</span>
        </div>

        <h1 class="hero-title">
          <span class="title-sub">共同学习</span>
          <span class="title-main">共同成长</span>
        </h1>

        <p class="hero-desc">
          汇聚团队对 LLM、Agent、AI 工具前沿探索<br />
          <span class="desc-mono">// 分享即贡献，积累即力量</span>
        </p>

        <div class="hero-actions">
          <a :href="withBase('/weekly/')" class="btn-primary">
            <span>查看最新周报</span>
            <span class="btn-arrow">→</span>
          </a>
          <a href="https://github.com/zbw-bw/ai-co-share" class="btn-ghost" target="_blank">
            GitHub ↗
          </a>
        </div>

        <div class="hero-hint">
          <span class="hint-label">快速分享</span>
          <code class="hint-code">/ai-co-share &lt;URL&gt;</code>
        </div>
      </div>
    </main>

    <!-- Category grid -->
    <section class="categories">
      <div class="section-header">
        <span class="section-label">// TOPICS</span>
      </div>
      <div class="cat-grid">
        <a
          v-for="(cat, i) in categories"
          :key="cat.key"
          :href="cat.href"
          class="cat-card"
          :style="`--accent: ${cat.color}; --delay: ${i * 80}ms`"
        >
          <div class="cat-icon">{{ cat.icon }}</div>
          <div class="cat-body">
            <h3 class="cat-label">{{ cat.label }}</h3>
            <p class="cat-desc">{{ cat.desc }}</p>
          </div>
          <span class="cat-arrow">↗</span>
        </a>
      </div>
    </section>

    <!-- Footer -->
    <footer class="home-footer">
      <span>AI Co-Share — 共同学习，共同成长</span>
    </footer>
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&display=swap');
</style>

<style scoped>
/* ── Root ─────────────────────────────── */
.home-root {
  position: relative;
  min-height: 100vh;
  background: #070d1a;
  color: #e2e8f4;
  overflow: hidden;
  font-family: -apple-system, 'PingFang SC', 'Hiragino Sans GB', sans-serif;
}

/* ── Background ──────────────────────── */
.bg-grid {
  position: fixed;
  inset: 0;
  background-image:
    linear-gradient(rgba(0, 229, 179, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 229, 179, 0.04) 1px, transparent 1px);
  background-size: 48px 48px;
  pointer-events: none;
  z-index: 0;
}

.bg-blob {
  position: fixed;
  border-radius: 50%;
  filter: blur(80px);
  pointer-events: none;
  z-index: 0;
  animation: blobDrift 20s ease-in-out infinite alternate;
}

.bg-blob-1 {
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(0, 229, 179, 0.08) 0%, transparent 70%);
  top: -200px;
  right: -100px;
  animation-duration: 25s;
}

.bg-blob-2 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(74, 158, 255, 0.07) 0%, transparent 70%);
  bottom: -150px;
  left: -100px;
  animation-duration: 30s;
  animation-delay: -10s;
}

@keyframes blobDrift {
  from { transform: translate(0, 0) scale(1); }
  to   { transform: translate(40px, 30px) scale(1.08); }
}

/* ── Nav ─────────────────────────────── */
.home-nav {
  position: relative;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 48px;
  border-bottom: 1px solid rgba(0, 229, 179, 0.1);
  backdrop-filter: blur(12px);
}

.nav-brand {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.95rem;
  font-weight: 600;
  color: #e2e8f4;
  text-decoration: none;
  letter-spacing: 0.02em;
}

.brand-bracket { color: #00e5b3; }

.nav-links {
  display: flex;
  gap: 28px;
  align-items: center;
}

.nav-links a {
  font-size: 0.875rem;
  color: #8892a4;
  text-decoration: none;
  transition: color 0.2s;
  font-weight: 500;
}

.nav-links a:hover { color: #e2e8f4; }

.nav-weekly {
  color: #00e5b3 !important;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem !important;
}

/* ── Hero ────────────────────────────── */
.hero {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: center;
  padding: 100px 48px 80px;
}

.hero-inner {
  max-width: 700px;
  width: 100%;
  animation: fadeUp 0.6s ease both;
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(24px); }
  to   { opacity: 1; transform: translateY(0); }
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.78rem;
  color: #00e5b3;
  border: 1px solid rgba(0, 229, 179, 0.3);
  border-radius: 20px;
  padding: 5px 14px;
  margin-bottom: 28px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.badge-dot {
  width: 6px;
  height: 6px;
  background: #00e5b3;
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.3; }
}

.hero-title {
  display: block;
  line-height: 1.1;
  margin-bottom: 24px;
}

.title-sub {
  display: block;
  font-size: clamp(2rem, 5vw, 3.2rem);
  font-weight: 700;
  color: #8892a4;
  letter-spacing: -0.02em;
}

.title-main {
  display: block;
  font-size: clamp(2.8rem, 7vw, 4.8rem);
  font-weight: 800;
  background: linear-gradient(135deg, #00e5b3 0%, #4a9eff 60%, #a78bfa 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.03em;
}

.hero-desc {
  font-size: 1rem;
  line-height: 1.8;
  color: #8892a4;
  margin-bottom: 36px;
}

.desc-mono {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.82rem;
  color: rgba(0, 229, 179, 0.7);
}

.hero-actions {
  display: flex;
  gap: 14px;
  margin-bottom: 32px;
  flex-wrap: wrap;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: #00e5b3;
  color: #070d1a;
  font-weight: 700;
  font-size: 0.9rem;
  border-radius: 8px;
  text-decoration: none;
  transition: background 0.2s, transform 0.15s, box-shadow 0.2s;
}

.btn-primary:hover {
  background: #00ffc6;
  transform: translateY(-1px);
  box-shadow: 0 8px 24px rgba(0, 229, 179, 0.3);
}

.btn-arrow { transition: transform 0.2s; }
.btn-primary:hover .btn-arrow { transform: translateX(4px); }

.btn-ghost {
  display: inline-flex;
  align-items: center;
  padding: 12px 24px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: #8892a4;
  font-size: 0.9rem;
  border-radius: 8px;
  text-decoration: none;
  transition: border-color 0.2s, color 0.2s;
}

.btn-ghost:hover { border-color: #8892a4; color: #e2e8f4; }

.hero-hint {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: 0.8rem;
}

.hint-label {
  color: #4a5568;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.hint-code {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.82rem;
  padding: 3px 10px;
  background: rgba(0, 229, 179, 0.08);
  border: 1px solid rgba(0, 229, 179, 0.2);
  border-radius: 5px;
  color: #00e5b3;
}

/* ── Categories ──────────────────────── */
.categories {
  position: relative;
  z-index: 1;
  padding: 0 48px 80px;
  max-width: 1100px;
  margin: 0 auto;
  width: 100%;
}

.section-header {
  margin-bottom: 20px;
}

.section-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: rgba(0, 229, 179, 0.5);
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.cat-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

@media (max-width: 640px) {
  .cat-grid { grid-template-columns: 1fr; }
  .home-nav { padding: 16px 20px; }
  .hero { padding: 60px 20px 40px; }
  .categories { padding: 0 20px 60px; }
  .nav-links { gap: 16px; }
}

.cat-card {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 24px 28px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-left: 3px solid var(--accent);
  border-radius: 10px;
  text-decoration: none;
  color: inherit;
  animation: fadeUp 0.5s ease both;
  animation-delay: var(--delay, 0ms);
  transition: background 0.2s, border-color 0.2s, box-shadow 0.2s, transform 0.15s;
}

.cat-card:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: var(--accent);
  box-shadow: 0 0 0 1px var(--accent), 0 8px 32px rgba(0, 0, 0, 0.3);
  transform: translateY(-2px);
}

.cat-icon {
  font-size: 1.6rem;
  color: var(--accent);
  font-family: 'JetBrains Mono', monospace;
  flex-shrink: 0;
  width: 40px;
  text-align: center;
  line-height: 1;
}

.cat-body { flex: 1; min-width: 0; }

.cat-label {
  font-size: 1.05rem;
  font-weight: 700;
  margin: 0 0 4px;
  color: #e2e8f4;
}

.cat-desc {
  font-size: 0.82rem;
  color: #8892a4;
  margin: 0;
  line-height: 1.5;
}

.cat-arrow {
  font-size: 1rem;
  color: var(--accent);
  opacity: 0;
  transition: opacity 0.2s, transform 0.2s;
}

.cat-card:hover .cat-arrow { opacity: 1; transform: translate(2px, -2px); }

/* ── Footer ──────────────────────────── */
.home-footer {
  position: relative;
  z-index: 1;
  text-align: center;
  padding: 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  font-size: 0.8rem;
  color: #4a5568;
  font-family: 'JetBrains Mono', monospace;
}
</style>
