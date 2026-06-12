import { createContentLoader } from 'vitepress'

export default createContentLoader('papers/*.md', {
  includeSrc: false,
  transform(data) {
    return data
      .filter(p => !p.url.endsWith('/papers/'))
      .sort((a, b) => +new Date(b.frontmatter.date ?? 0) - +new Date(a.frontmatter.date ?? 0))
  }
})
