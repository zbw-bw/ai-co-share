import { h } from 'vue'
import DefaultTheme from 'vitepress/theme'
import { useData } from 'vitepress'
import HomeLayout from './HomeLayout.vue'
import ArticleList from './ArticleList.vue'
import type { Theme } from 'vitepress'

export default {
  extends: DefaultTheme,
  Layout() {
    const { frontmatter } = useData()
    if (frontmatter.value.customHome) {
      return h(HomeLayout)
    }
    return h(DefaultTheme.Layout)
  },
  enhanceApp({ app }) {
    app.component('ArticleList', ArticleList)
  }
} satisfies Theme
