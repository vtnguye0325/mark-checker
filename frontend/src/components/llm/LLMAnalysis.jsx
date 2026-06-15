import { useState } from 'react'
import {
  TIER_COLORS,
  TIER_ORDER,
  parseSections,
  extractVerdict,
  parseSpectrumTiers,
  splitSignals,
} from '../../lib/parseLegalAnalysis'

function renderInline(text) {
  return text.split(/\*\*(.+?)\*\*/).map((part, i) =>
    i % 2 === 1 ? <strong key={i}>{part}</strong> : part
  )
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
  const lit = new Set(tiers.map((t) => t.id))
  return (
    <div className="llm-card llm-card--spectrum">
      <div className="llm-card-title">{title}</div>
      <div className="mini-spectrum-bar">
        {TIER_ORDER.map((id) => (
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

function LegalSources({ sources }) {
  const [open, setOpen] = useState(false)
  if (!sources) return null
  const tmep = sources.tmep || []
  const ttab = sources.ttab || []
  if (tmep.length === 0 && ttab.length === 0) return null

  return (
    <div className="legal-sources">
      <button className="legal-sources-toggle" onClick={() => setOpen(o => !o)}>
        <span className="legal-sources-icon">{open ? '▲' : '▼'}</span>
        Legal Sources
        <span className="legal-sources-count">{tmep.length + ttab.length}</span>
      </button>
      {open && (
        <div className="legal-sources-body">
          {tmep.length > 0 && (
            <div className="ls-group">
              <div className="ls-group-label">TMEP Doctrine</div>
              {tmep.map((c) => (
                <TMEPChunk key={c.id} chunk={c} />
              ))}
            </div>
          )}
          {ttab.length > 0 && (
            <div className="ls-group">
              <div className="ls-group-label">TTAB Cases</div>
              {ttab.map((c) => (
                <TTABChunk key={c.id} chunk={c} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function TMEPChunk({ chunk }) {
  const [expanded, setExpanded] = useState(false)
  const { section_number, section_title } = chunk.metadata
  const preview = chunk.text.slice(0, 180)
  return (
    <div className="ls-chunk">
      <div className="ls-chunk-header" onClick={() => setExpanded(o => !o)}>
        <span className="ls-cite">TMEP §{section_number}</span>
        <span className="ls-title">{section_title}</span>
        <span className="ls-expand">{expanded ? '−' : '+'}</span>
      </div>
      {expanded
        ? <p className="ls-text">{chunk.text}</p>
        : <p className="ls-text ls-text--preview">{preview}{chunk.text.length > 180 ? '…' : ''}</p>
      }
    </div>
  )
}

function TTABChunk({ chunk }) {
  const [expanded, setExpanded] = useState(false)
  const { mark, nice_class, outcome } = chunk.metadata
  const preview = chunk.text.slice(0, 180)
  return (
    <div className="ls-chunk">
      <div className="ls-chunk-header" onClick={() => setExpanded(o => !o)}>
        <span className="ls-cite">{mark}</span>
        <span className={`ls-outcome ls-outcome--${outcome}`}>{outcome}</span>
        {nice_class && <span className="ls-nc">NC{nice_class}</span>}
        <span className="ls-expand">{expanded ? '−' : '+'}</span>
      </div>
      {expanded
        ? <p className="ls-text">{chunk.text}</p>
        : <p className="ls-text ls-text--preview">{preview}{chunk.text.length > 180 ? '…' : ''}</p>
      }
    </div>
  )
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
      <LegalSources sources={data.sources} />
    </div>
  )
}
