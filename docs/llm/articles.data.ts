import { createContentLoader } from 'vitepress'

export default createContentLoader('llm/*.md', {
  includeSrc: false,
  transform(data) {
    return data
      .filter(p => !p.url.endsWith('/llm/'))
      .sort((a, b) => +new Date(b.frontmatter.date ?? 0) - +new Date(a.frontmatter.date ?? 0))
  }
})

export type ArticleData = Awaited<ReturnType<typeof import('./articles.data').default['load']>>
