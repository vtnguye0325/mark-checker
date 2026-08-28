import { parseSections } from '../../lib/parseLegalAnalysis'
import PartError from './PartError'

// Copied verbatim from LLMAnalysis.jsx, which Phase 7 deletes.
function renderInline(text) {
  return text.split(/\*\*(.+?)\*\*/).map((part, i) =>
    i % 2 === 1 ? <strong key={i}>{part}</strong> : part
  )
}

// Part 04 — the recommended action, as prose under one heading.
export default function PartAction({ loading, data, error, explainError }) {
  const head = (
    <div className="part-head">
      <span className="part-no">Part 04</span>
      <h2 className="t-h2">Recommended action</h2>
    </div>
  )

  if (explainError) {
    return (
      <>
        {head}
        <PartError label="Unavailable">
          The basis step did not complete, so no action was written.
        </PartError>
      </>
    )
  }

  if (error) {
    return (
      <>
        {head}
        <PartError label="Unavailable">{error}</PartError>
        <p className="t-small dim" style={{ marginTop: '16px' }}>
          The recommended action is part of the analysis, which did not arrive.
        </p>
      </>
    )
  }

  if (loading && !data) {
    return (
      <>
        {head}
        <p className="t-body dim">The analysis is still being written.</p>
      </>
    )
  }

  if (!data) {
    return (
      <>
        {head}
        <p className="t-body dim">Queued. This part fills after the analysis lands.</p>
      </>
    )
  }

  // The endpoint answered 200, but the body is not the documented shape. Treat it
  // as a failed part, so a bad proxy response does not crash the page.
  if (typeof data.analysis !== 'string' || !data.analysis) {
    return (
      <>
        {head}
        <PartError label="Unavailable">The analysis returned an unreadable response.</PartError>
      </>
    )
  }

  const sections = parseSections(data.analysis)

  if (!sections) {
    return (
      <>
        {head}
        <p className="t-body">{data.analysis}</p>
      </>
    )
  }

  return (
    <>
      {head}
      <div className="stack">
        {sections.map(({ title, content }, s) => (
          <div key={`${s}-${title}`}>
            <h3 className="t-h3">{title}</h3>
            {content.split(/\n{2,}/).map((para, i) => (
              <p className="t-body" key={i}>{renderInline(para)}</p>
            ))}
          </div>
        ))}
      </div>
    </>
  )
}
