<script setup lang="ts">
import { withBase } from 'vitepress'

const categories = [
  {
    key: 'llm',
    icon: '🧠',
    label: 'LLM',
    desc: '大模型 · 提示工程 · RAG · 微调',
    href: '/ai-co-share/llm/',
    color: '#10b981',
    gradient: 'from-emerald-500/20 to-teal-500/10',
    border: 'hover:border-emerald-500/60',
    glow: 'hover:shadow-emerald-500/20',
  },
  {
    key: 'agent',
    icon: '🤖',
    label: 'Agent',
    desc: '工作流 · Multi-Agent · Tool Use · MCP',
    href: '/ai-co-share/agent/',
    color: '#3b82f6',
    gradient: 'from-blue-500/20 to-indigo-500/10',
    border: 'hover:border-blue-500/60',
    glow: 'hover:shadow-blue-500/20',
  },
  {
    key: 'tools',
    icon: '🛠️',
    label: 'Tools',
    desc: 'Claude Code · Skills · Hooks · 效率工具',
    href: '/ai-co-share/tools/',
    color: '#8b5cf6',
    gradient: 'from-violet-500/20 to-purple-500/10',
    border: 'hover:border-violet-500/60',
    glow: 'hover:shadow-violet-500/20',
  },
  {
    key: 'papers',
    icon: '📄',
    label: 'Papers',
    desc: '论文精读 · 前沿研究 · 实验复现',
    href: '/ai-co-share/papers/',
    color: '#f59e0b',
    gradient: 'from-amber-500/20 to-orange-500/10',
    border: 'hover:border-amber-500/60',
    glow: 'hover:shadow-amber-500/20',
  },
]

const stats = [
  { label: '知识分类', value: '4' },
  { label: '持续更新', value: '∞' },
  { label: '团队共建', value: '✓' },
]
</script>

<template>
  <div class="home-root">
    <!-- Animated background -->
    <div class="bg-layer" aria-hidden="true">
      <div class="bg-noise" />
      <div class="bg-orb orb-1" />
      <div class="bg-orb orb-2" />
      <div class="bg-orb orb-3" />
      <div class="bg-grid" />
    </div>

    <!-- Nav -->
    <header class="home-nav">
      <a :href="withBase('/')" class="nav-brand">
        <span class="brand-icon">⬡</span>
        <span class="brand-name">AI Co-Share</span>
      </a>
      <nav class="nav-links">
        <a :href="withBase('/llm/')">LLM</a>
        <a :href="withBase('/agent/')">Agent</a>
        <a :href="withBase('/tools/')">Tools</a>
        <a :href="withBase('/papers/')">Papers</a>
        <a :href="withBase('/weekly/')" class="nav-cta">周索引</a>
      </nav>
    </header>

    <!-- Hero -->
    <main class="hero">
      <div class="hero-content">
        <!-- Badge -->
        <div class="hero-badge">
          <span class="badge-pulse" />
          <span>Team Knowledge Base · 持续更新中</span>
        </div>

        <!-- Title -->
        <h1 class="hero-title">
          <span class="title-line-1">共同学习</span>
          <span class="title-line-2">共同成长</span>
        </h1>

        <!-- Subtitle -->
        <p class="hero-sub">
          汇聚团队对 LLM、Agent、AI 工具的前沿探索与实践沉淀
        </p>

        <!-- Stats row -->
        <div class="hero-stats">
          <div v-for="s in stats" :key="s.label" class="stat-item">
            <span class="stat-value">{{ s.value }}</span>
            <span class="stat-label">{{ s.label }}</span>
          </div>
        </div>

        <!-- CTA buttons -->
        <div class="hero-actions">
          <a :href="withBase('/weekly/')" class="btn-primary">
            查看最新周报
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </a>
          <a href="https://github.com/zbw-bw/ai-co-share" class="btn-outline" target="_blank" rel="noopener">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
            GitHub
          </a>
        </div>

        <!-- Quick share hint -->
        <div class="hero-hint">
          <span class="hint-label">快速分享</span>
          <code class="hint-code">/ai-co-share &lt;URL&gt;</code>
        </div>
      </div>

      <!-- Decorative card preview -->
      <div class="hero-visual" aria-hidden="true">
        <div class="preview-card">
          <div class="preview-header">
            <span class="preview-dot red" /><span class="preview-dot yellow" /><span class="preview-dot green" />
            <span class="preview-title">最新分享</span>
          </div>
          <div class="preview-body">
            <div class="preview-line w-3/4" />
            <div class="preview-line w-1/2" />
            <div class="preview-tags">
              <span class="preview-tag green">LLM</span>
              <span class="preview-tag blue">Agent</span>
            </div>
            <div class="preview-line w-full" />
            <div class="preview-line w-5/6" />
            <div class="preview-line w-2/3" />
          </div>
        </div>
      </div>
    </main>

    <!-- Categories -->
    <section class="categories">
      <div class="section-label">
        <span class="label-line" />
        <span>探索分类</span>
        <span class="label-line" />
      </div>

      <div class="cat-grid">
        <a
          v-for="(cat, i) in categories"
          :key="cat.key"
          :href="cat.href"
          class="cat-card"
          :style="`--accent: ${cat.color}; --delay: ${i * 100}ms`"
        >
          <div class="cat-icon-wrap">
            <span class="cat-icon">{{ cat.icon }}</span>
          </div>
          <div class="cat-body">
            <h3 class="cat-label">{{ cat.label }}</h3>
            <p class="cat-desc">{{ cat.desc }}</p>
          </div>
          <div class="cat-arrow">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M4 9h10M10 5l4 4-4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </div>
        </a>
      </div>
    </section>

    <!-- Footer -->
    <footer class="home-footer">
      <span class="footer-brand">AI Co-Share</span>
      <span class="footer-sep">·</span>
      <span>共同学习，共同成长</span>
    </footer>
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
</style>

<style scoped>
/* ── Reset & Root ─────────────────────── */
* { box-sizing: border-box; }

.home-root {
  position: relative;
  min-height: 100vh;
  background: #0a0f1e;
  color: #e2e8f0;
  font-family: 'Inter', -apple-system, 'PingFang SC', sans-serif;
  overflow-x: hidden;
}

/* ── Background ──────────────────────── */
.bg-layer {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.bg-noise {
  position: absolute;
  inset: 0;
  opacity: 0.025;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px);
  background-size: 64px 64px;
  mask-image: radial-gradient(ellipse 80% 80% at 50% 0%, black 40%, transparent 100%);
}

.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  animation: orbFloat 20s ease-in-out infinite alternate;
}

.orb-1 {
  width: 700px; height: 700px;
  background: radial-gradient(circle, rgba(16,185,129,0.12) 0%, transparent 70%);
  top: -300px; right: -200px;
  animation-duration: 28s;
}

.orb-2 {
  width: 600px; height: 600px;
  background: radial-gradient(circle, rgba(59,130,246,0.1) 0%, transparent 70%);
  bottom: -200px; left: -150px;
  animation-duration: 35s;
  animation-delay: -12s;
}

.orb-3 {
  width: 400px; height: 400px;
  background: radial-gradient(circle, rgba(139,92,246,0.08) 0%, transparent 70%);
  top: 40%; left: 40%;
  animation-duration: 22s;
  animation-delay: -6s;
}

@keyframes orbFloat {
  from { transform: translate(0, 0) scale(1); }
  to   { transform: translate(50px, 40px) scale(1.1); }
}

/* ── Nav ─────────────────────────────── */
.home-nav {
  position: relative;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 48px;
  height: 64px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  background: rgba(10,15,30,0.7);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: #e2e8f0;
}

.brand-icon {
  font-size: 1.3rem;
  color: #10b981;
  line-height: 1;
}

.brand-name {
  font-size: 0.95rem;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 4px;
}

.nav-links a {
  padding: 6px 14px;
  font-size: 0.875rem;
  font-weight: 500;
  color: #94a3b8;
  text-decoration: none;
  border-radius: 8px;
  transition: color 0.2s, background 0.2s;
}

.nav-links a:hover {
  color: #e2e8f0;
  background: rgba(255,255,255,0.06);
}

.nav-cta {
  background: rgba(16,185,129,0.12) !important;
  color: #10b981 !important;
  border: 1px solid rgba(16,185,129,0.25) !important;
}

.nav-cta:hover {
  background: rgba(16,185,129,0.2) !important;
  border-color: rgba(16,185,129,0.5) !important;
}

/* ── Hero ────────────────────────────── */
.hero {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 48px;
  padding: 96px 48px 80px;
  max-width: 1200px;
  margin: 0 auto;
}

.hero-content {
  flex: 1;
  max-width: 600px;
  animation: fadeUp 0.7s ease both;
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(28px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* Badge */
.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  border-radius: 100px;
  border: 1px solid rgba(16,185,129,0.3);
  background: rgba(16,185,129,0.08);
  font-size: 0.78rem;
  font-weight: 500;
  color: #10b981;
  letter-spacing: 0.02em;
  margin-bottom: 32px;
}

.badge-pulse {
  width: 7px; height: 7px;
  background: #10b981;
  border-radius: 50%;
  animation: pulse 2.5s ease-in-out infinite;
  flex-shrink: 0;
}

@keyframes pulse {
  0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(16,185,129,0.4); }
  50%       { opacity: 0.6; box-shadow: 0 0 0 6px rgba(16,185,129,0); }
}

/* Title */
.hero-title {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
  margin: 0 0 24px;
  letter-spacing: -0.03em;
}

.title-line-1 {
  font-size: clamp(2.4rem, 5vw, 3.6rem);
  font-weight: 800;
  color: #94a3b8;
}

.title-line-2 {
  font-size: clamp(3rem, 6.5vw, 5rem);
  font-weight: 800;
  background: linear-gradient(135deg, #10b981 0%, #3b82f6 50%, #8b5cf6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Subtitle */
.hero-sub {
  font-size: 1.05rem;
  line-height: 1.75;
  color: #64748b;
  margin: 0 0 36px;
}

/* Stats */
.hero-stats {
  display: flex;
  gap: 32px;
  margin-bottom: 40px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 800;
  color: #e2e8f0;
  line-height: 1;
}

.stat-label {
  font-size: 0.75rem;
  color: #475569;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

/* Actions */
.hero-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 28px;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: linear-gradient(135deg, #10b981, #059669);
  color: #fff;
  font-weight: 600;
  font-size: 0.9rem;
  border-radius: 10px;
  text-decoration: none;
  transition: opacity 0.2s, transform 0.15s, box-shadow 0.2s;
  box-shadow: 0 4px 20px rgba(16,185,129,0.3);
}

.btn-primary:hover {
  opacity: 0.92;
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(16,185,129,0.4);
}

.btn-outline {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border: 1px solid rgba(255,255,255,0.12);
  color: #94a3b8;
  font-size: 0.9rem;
  font-weight: 500;
  border-radius: 10px;
  text-decoration: none;
  background: rgba(255,255,255,0.03);
  transition: border-color 0.2s, color 0.2s, background 0.2s;
}

.btn-outline:hover {
  border-color: rgba(255,255,255,0.25);
  color: #e2e8f0;
  background: rgba(255,255,255,0.06);
}

/* Hint */
.hero-hint {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.hint-label {
  font-size: 0.75rem;
  color: #334155;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 500;
}

.hint-code {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  padding: 4px 12px;
  background: rgba(16,185,129,0.07);
  border: 1px solid rgba(16,185,129,0.18);
  border-radius: 6px;
  color: #10b981;
}

/* ── Hero Visual ─────────────────────── */
.hero-visual {
  flex-shrink: 0;
  animation: fadeUp 0.7s 0.2s ease both;
}

.preview-card {
  width: 320px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 24px 64px rgba(0,0,0,0.4), 0 0 0 1px rgba(255,255,255,0.04);
}

.preview-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 14px 18px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  background: rgba(255,255,255,0.02);
}

.preview-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
}
.preview-dot.red    { background: #ff5f57; }
.preview-dot.yellow { background: #febc2e; }
.preview-dot.green  { background: #28c840; }

.preview-title {
  margin-left: 8px;
  font-size: 0.78rem;
  color: #475569;
  font-weight: 500;
}

.preview-body {
  padding: 20px 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.preview-line {
  height: 10px;
  background: rgba(255,255,255,0.07);
  border-radius: 5px;
  animation: shimmer 2s ease-in-out infinite;
}

.preview-line.w-3\/4 { width: 75%; }
.preview-line.w-1\/2 { width: 50%; }
.preview-line.w-full { width: 100%; }
.preview-line.w-5\/6 { width: 83%; }
.preview-line.w-2\/3 { width: 66%; }

@keyframes shimmer {
  0%, 100% { opacity: 0.5; }
  50%       { opacity: 1; }
}

.preview-tags {
  display: flex;
  gap: 6px;
}

.preview-tag {
  font-size: 0.7rem;
  padding: 3px 10px;
  border-radius: 100px;
  font-weight: 500;
}

.preview-tag.green {
  background: rgba(16,185,129,0.15);
  color: #10b981;
}

.preview-tag.blue {
  background: rgba(59,130,246,0.15);
  color: #3b82f6;
}

/* ── Categories ──────────────────────── */
.categories {
  position: relative;
  z-index: 1;
  padding: 0 48px 96px;
  max-width: 1200px;
  margin: 0 auto;
}

.section-label {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
  font-size: 0.78rem;
  font-weight: 600;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.label-line {
  flex: 1;
  height: 1px;
  background: rgba(255,255,255,0.06);
}

.cat-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.cat-card {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 28px 28px;
  background: rgba(255,255,255,0.025);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 16px;
  text-decoration: none;
  color: inherit;
  animation: fadeUp 0.6s ease both;
  animation-delay: var(--delay, 0ms);
  transition: background 0.25s, border-color 0.25s, box-shadow 0.25s, transform 0.2s;
  position: relative;
  overflow: hidden;
}

.cat-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 0% 50%, var(--accent) 0%, transparent 60%);
  opacity: 0;
  transition: opacity 0.3s;
}

.cat-card:hover {
  background: rgba(255,255,255,0.05);
  border-color: color-mix(in srgb, var(--accent) 50%, transparent);
  box-shadow: 0 8px 40px rgba(0,0,0,0.3), 0 0 0 1px color-mix(in srgb, var(--accent) 30%, transparent);
  transform: translateY(-3px);
}

.cat-card:hover::before { opacity: 0.06; }

.cat-icon-wrap {
  width: 52px; height: 52px;
  border-radius: 14px;
  background: color-mix(in srgb, var(--accent) 15%, transparent);
  border: 1px solid color-mix(in srgb, var(--accent) 25%, transparent);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 1.5rem;
  transition: background 0.25s, border-color 0.25s;
  position: relative;
  z-index: 1;
}

.cat-card:hover .cat-icon-wrap {
  background: color-mix(in srgb, var(--accent) 22%, transparent);
  border-color: color-mix(in srgb, var(--accent) 40%, transparent);
}

.cat-body {
  flex: 1;
  min-width: 0;
  position: relative;
  z-index: 1;
}

.cat-label {
  font-size: 1.05rem;
  font-weight: 700;
  margin: 0 0 6px;
  color: #e2e8f0;
  letter-spacing: -0.01em;
}

.cat-desc {
  font-size: 0.82rem;
  color: #64748b;
  margin: 0;
  line-height: 1.6;
}

.cat-arrow {
  color: var(--accent);
  opacity: 0;
  transform: translateX(-6px);
  transition: opacity 0.2s, transform 0.2s;
  flex-shrink: 0;
  position: relative;
  z-index: 1;
}

.cat-card:hover .cat-arrow {
  opacity: 1;
  transform: translateX(0);
}

/* ── Footer ──────────────────────────── */
.home-footer {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 28px;
  border-top: 1px solid rgba(255,255,255,0.05);
  font-size: 0.8rem;
  color: #334155;
}

.footer-brand {
  font-weight: 600;
  color: #475569;
}

.footer-sep { color: #1e293b; }

/* ── Responsive ──────────────────────── */
@media (max-width: 900px) {
  .hero { flex-direction: column; padding: 72px 32px 60px; }
  .hero-visual { display: none; }
  .hero-content { max-width: 100%; }
}

@media (max-width: 640px) {
  .home-nav { padding: 0 20px; }
  .hero { padding: 56px 20px 48px; }
  .categories { padding: 0 20px 72px; }
  .cat-grid { grid-template-columns: 1fr; }
  .nav-links { gap: 0; }
  .nav-links a { padding: 6px 10px; font-size: 0.82rem; }
  .hero-stats { gap: 20px; }
}
</style>
