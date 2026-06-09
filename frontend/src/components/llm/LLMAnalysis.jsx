function parseSections(text) {
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
  sections.forEach(s => { s.content = s.content.trim() })
  return sections.length > 0 ? sections : null
}

function renderInline(text) {
  return text.split(/\*\*(.+?)\*\*/).map((part, i) =>
    i % 2 === 1 ? <strong key={i}>{part}</strong> : part
  )
}

const TIER_COLORS = {
  generic: '#9e2a2a', descriptive: '#b45a1a',
  suggestive: '#6d5a1c', arbitrary: '#1a6b42', fanciful: '#158050',
}
const TIER_ORDER = ['generic', 'descriptive', 'suggestive', 'arbitrary', 'fanciful']

function extractVerdict(text) {
  const vm = text.match(/\b(not\s+distinctive|non[-\s]distinctive|distinctive)\b/i)
  const verdict = vm ? vm[1].toLowerCase().replace(/\s+/g, ' ') : null
  const isDistinctive = verdict !== null && !verdict.startsWith('not') && !verdict.startsWith('non')
  const cm = text.match(/\b(high|moderate|low)\s+confidence\b/i)
  return { isDistinctive, verdict, confidence: cm ? cm[1].toLowerCase() : null }
}

function parseSpectrumTiers(text) {
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

function splitSignals(text) {
  return text.split(/\n{2,}/).map(s => s.trim()).filter(Boolean)
}

function GenericCard({ title, content }) {
  return (
    <div className="llm-card">
      <div className="llm-card-title">{title}</div>
      <p className="llm-card-body">{renderInline(content)}</p>
    </div>
  )
}

function VerdictCard({ title, content }) {
  const { isDistinctive, verdict, confidence } = extractVerdict(content)
  if (!verdict) return <GenericCard title={title} content={content} />
  const confColors = { high: '#158050', moderate: '#6d5a1c', low: '#9e2a2a' }
  return (
    <div className="llm-card llm-card--verdict">
      <div className="llm-card-title">{title}</div>
      <div className="verdict-card-hero">
        <span className={`verdict-chip ${isDistinctive ? 'verdict-chip--dist' : 'verdict-chip--not'}`}>
          <span className="verdict-chip-icon">{isDistinctive ? '◆' : '◇'}</span>
          {isDistinctive ? 'Distinctive' : 'Not Distinctive'}
        </span>
        {confidence && (
          <span className="confidence-badge" style={{ '--conf-color': confColors[confidence] }}>
            {confidence} confidence
          </span>
        )}
      </div>
      <p className="llm-card-body llm-card-body--supporting">{renderInline(content)}</p>
    </div>
  )
}

function SpectrumCard({ title, content }) {
  const { tiers, remainder } = parseSpectrumTiers(content)
  if (tiers.length === 0) return <GenericCard title={title} content={content} />
  const lit = new Set(tiers.map(t => t.id))
  return (
    <div className="llm-card llm-card--spectrum">
      <div className="llm-card-title">{title}</div>
      <div className="mini-spectrum-bar">
        {TIER_ORDER.map(id => (
          <div key={id} className={`mini-seg ${lit.has(id) ? 'mini-seg--lit' : 'mini-seg--dim'}`}
            style={{ '--seg-color': TIER_COLORS[id] }} title={id} />
        ))}
      </div>
      <ul className="spectrum-tier-list">
        {tiers.map(({ name, explanation, color }) => (
          <li key={name} className="spectrum-tier-item">
            <span className="tier-name" style={{ color }}>{name}</span>
            <span className="tier-dash">—</span>
            <span className="tier-explanation">{renderInline(explanation)}</span>
          </li>
        ))}
      </ul>
      {remainder && <p className="llm-card-body llm-card-body--remainder">{renderInline(remainder)}</p>}
    </div>
  )
}

function SignalsCard({ title, content }) {
  const signals = splitSignals(content)
  if (signals.length <= 1) return <GenericCard title={title} content={content} />
  return (
    <div className="llm-card llm-card--signals">
      <div className="llm-card-title">{title}</div>
      <ul className="signals-list">
        {signals.map((s, i) => (
          <li key={i} className="signals-item">
            <span className="signals-bullet" aria-hidden="true">›</span>
            <p className="signals-text">{renderInline(s)}</p>
          </li>
        ))}
      </ul>
    </div>
  )
}

function ActionCard({ title, content }) {
  return (
    <div className="llm-card llm-card--action">
      <div className="llm-card-title">{title}</div>
      <p className="llm-card-body action-body">
        <span className="action-arrow" aria-hidden="true">→</span>
        {renderInline(content)}
      </p>
    </div>
  )
}

function renderSection({ title, content }) {
  const t = title.toLowerCase()
  if (t.includes('what the model found')) return <VerdictCard key={title} title={title} content={content} />
  if (t.includes('spectrum') || t.includes('where this mark')) return <SpectrumCard key={title} title={title} content={content} />
  if (t.includes('leaned') || t.includes('key signals')) return <SignalsCard key={title} title={title} content={content} />
  if (t.includes('what to do') || t.includes('next')) return <ActionCard key={title} title={title} content={content} />
  return <GenericCard key={title} title={title} content={content} />
}

export default function LLMAnalysis({ loading, data }) {
  if (loading) {
    return (
      <div className="llm-loading">
        <span className="btn-spinner btn-spinner--sm" />
        <span className="explain-status">Generating legal analysis…</span>
      </div>
    )
  }
  if (!data) return null

  const sections = parseSections(data.analysis)

  return (
    <div className="llm-section">
      <div className="llm-section-label">Legal Analysis</div>
      {sections ? (
        <div className="llm-cards">
          {sections.map(renderSection)}
        </div>
      ) : (
        <p className="llm-card-body">{data.analysis}</p>
      )}
    </div>
  )
}
