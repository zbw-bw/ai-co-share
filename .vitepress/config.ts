import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'AI Co-Share',
  description: '团队 AI 技术学习分享',
  lang: 'zh-CN',
  lastUpdated: true,

  themeConfig: {
    nav: [
      { text: '首页', link: '/' },
      { text: 'LLM', link: '/llm/' },
      { text: 'Agent', link: '/agent/' },
      { text: 'Tools', link: '/tools/' },
      { text: 'Papers', link: '/papers/' },
      { text: '周索引', link: '/weekly/' },
    ],

    sidebar: {
      '/llm/': [{ text: 'LLM', link: '/llm/' }],
      '/agent/': [{ text: 'Agent', link: '/agent/' }],
      '/tools/': [{ text: 'Tools', link: '/tools/' }],
      '/papers/': [{ text: 'Papers', link: '/papers/' }],
      '/weekly/': [{ text: '周索引', link: '/weekly/' }],
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/YOUR_ORG/ai-co-share' },
    ],

    footer: {
      message: 'AI Co-Share — 共同学习，共同成长',
    },
  },

  base: '/ai-co-share/',
})
