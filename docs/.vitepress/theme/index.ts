import { h } from 'vue'
import DefaultTheme from 'vitepress/theme'
import { useData } from 'vitepress'
import HomeLayout from './HomeLayout.vue'
import ArticleList from './ArticleList.vue'
import ArticleMeta from './ArticleMeta.vue'
import type { Theme } from 'vitepress'
import './custom.css'

export default {
  extends: DefaultTheme,
  Layout() {
    const { frontmatter } = useData()
    // 自定义首页
    if (frontmatter.value.customHome) {
      return h(HomeLayout)
    }
    // 文章页：在正文前注入 meta 卡片
    return h(DefaultTheme.Layout, null, {
      'doc-before': () => frontmatter.value.title ? h(ArticleMeta) : null,
    })
  },
  enhanceApp({ app }) {
    app.component('ArticleList', ArticleList)
  }
} satisfies Theme
