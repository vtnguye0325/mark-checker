export function parseSections(text) {
  const lines = text.split('\n')
  const sections = []
  let current = null
  for (const line of lines) {
    const m = line.match(/^\*\*(.+?)\*\*\s*$/) || line.match(/^#{1,4}\s+(.+?)\s*$/)
    if (m) {
      if (current) sections.push(current)
      current = { title: m[1], content: '' }
    } else if (current) {
      current.content += (current.content ? '\n' : '') + line
    }
  }
  if (current) sections.push(current)
  sections.forEach((s) => { s.content = s.content.trim() })
  return sections.length > 0 ? sections : null
}

// Scrape the confidence word out of the stage-3 prose for the plate's confidence
// row. `result.label` from stage 1 owns the verdict word, so this reads only the
// confidence.
export function extractConfidence(text) {
  const cm = text.match(/\b(high|moderate|low)\s+confidence\b/i)
  return { confidence: cm ? cm[1].toLowerCase() : null }
}
