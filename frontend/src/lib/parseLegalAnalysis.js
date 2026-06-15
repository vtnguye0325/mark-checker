export const TIER_COLORS = {
  generic: '#9e2a2a',
  descriptive: '#b45a1a',
  suggestive: '#6d5a1c',
  arbitrary: '#1a6b42',
  fanciful: '#158050',
}

export const TIER_ORDER = ['generic', 'descriptive', 'suggestive', 'arbitrary', 'fanciful']

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

export function extractVerdict(text) {
  const vm = text.match(/\b(not\s+distinctive|non[-\s]distinctive|distinctive)\b/i)
  const verdict = vm ? vm[1].toLowerCase().replace(/\s+/g, ' ') : null
  const isDistinctive = verdict !== null && !verdict.startsWith('not') && !verdict.startsWith('non')
  const cm = text.match(/\b(high|moderate|low)\s+confidence\b/i)
  return { isDistinctive, verdict, confidence: cm ? cm[1].toLowerCase() : null }
}

export function parseSpectrumTiers(text) {
  const re = /^[-•]\s+\*\*([^*]+)\*\*\s*[—–-]\s*(.+)$/gm
  const tiers = []
  let m
  while ((m = re.exec(text)) !== null) {
    const id = m[1].trim().toLowerCase()
    tiers.push({ name: m[1].trim(), id, explanation: m[2].trim(), color: TIER_COLORS[id] ?? '#5a6356' })
  }
  const remainder = text.replace(re, '').trim()
  return { tiers, remainder }
}

export function splitSignals(text) {
  return text.split(/\n{2,}/).map((s) => s.trim()).filter(Boolean)
}
