import { createContentLoader } from 'vitepress'

export default createContentLoader('agent/*.md', {
  includeSrc: false,
  transform(data) {
    return data
      .filter(p => !p.url.endsWith('/agent/'))
      .sort((a, b) => +new Date(b.frontmatter.date ?? 0) - +new Date(a.frontmatter.date ?? 0))
  }
})
