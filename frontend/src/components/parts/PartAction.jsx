import { useEffect, useRef, useState } from 'react'
import { parseSections } from '../../lib/parseLegalAnalysis'
import PartError from './PartError'
import PartPending from './PartPending'
import TurnstileWidget from '../TurnstileWidget'

// Copied verbatim from LLMAnalysis.jsx, which Phase 7 deletes.
function renderInline(text) {
  return text.split(/\*\*(.+?)\*\*/).map((part, i) =>
    i % 2 === 1 ? <strong key={i}>{part}</strong> : part
  )
}

// The model writes markdown. Split one section body into paragraph blocks and
// list blocks, so a run of "- " lines becomes a real list. Without this the
// bullets join into one long line and the part reads as broken prose.
const BULLET = /^\s*[-*\u2022]\s+/
const NUMBER = /^\s*\d+[.)]\s+/

function toBlocks(content) {
  const blocks = []
  let para = []
  let list = null
  const flushPara = () => {
    if (para.length === 0) return
    blocks.push({ type: 'p', text: para.join(' ') })
    para = []
  }
  const flushList = () => {
    if (!list) return
    blocks.push(list)
    list = null
  }
  for (const raw of content.split('\n')) {
    const line = raw.trim()
    if (!line) { flushPara(); flushList(); continue }
    const marker = BULLET.test(line) ? BULLET : NUMBER.test(line) ? NUMBER : null
    if (marker) {
      flushPara()
      const ordered = marker === NUMBER
      if (!list || list.ordered !== ordered) { flushList(); list = { type: 'list', ordered, items: [] } }
      list.items.push(line.replace(marker, ''))
      continue
    }
    // A line that continues the last bullet, not a new paragraph.
    if (list) { list.items[list.items.length - 1] += ' ' + line; continue }
    para.push(line)
  }
  flushPara()
  flushList()
  return blocks
}

function renderBlocks(blocks) {
  return blocks.map((b, i) =>
    b.type === 'list'
      ? b.ordered
        ? <ol className="prose-list" key={i}>{b.items.map((t, j) => <li key={j}>{renderInline(t)}</li>)}</ol>
        : <ul className="prose-list" key={i}>{b.items.map((t, j) => <li key={j}>{renderInline(t)}</li>)}</ul>
      : <p className="t-body" key={i}>{renderInline(b.text)}</p>
  )
}

// Part 02 — the recommended action, as prose under one heading.
export default function PartAction({ loading, data, error, explainError, retryAt, onRetry, turnstileSiteKey }) {
  const retryWidgetRef = useRef(null)
  const [retryToken, setRetryToken] = useState('')
  const [secondsLeft, setSecondsLeft] = useState(0)

  useEffect(() => {
    if (!retryAt) return undefined
    const update = () => setSecondsLeft(Math.max(0, Math.ceil((retryAt - Date.now()) / 1000)))
    update()
    if (retryAt <= Date.now()) return undefined
    const timer = window.setInterval(() => {
      update()
      if (retryAt <= Date.now()) window.clearInterval(timer)
    }, 1000)
    return () => window.clearInterval(timer)
  }, [retryAt])

  const head = (
    <div className="part-head">
      <span className="part-no">Part 02</span>
      <h2 className="t-h2">Our reading</h2>
    </div>
  )

  if (explainError) {
    return (
      <>
        {head}
        <PartError label="Unavailable">
          The earlier step did not complete, so no action was written.
        </PartError>
      </>
    )
  }

  if (error) {
    return (
      <>
        {head}
        <PartError label="Unavailable">{error}</PartError>
        <p className="key">
          The recommended action is part of the analysis, which did not arrive.
        </p>
        {retryAt && onRetry && (
          <div className="retry-panel">
            <p className="t-body">
              {secondsLeft > 0
                ? `Wait ${secondsLeft} seconds before you retry the analysis.`
                : 'Retry the analysis with the score and breakdown above.'}
            </p>
            {turnstileSiteKey && (
              <div className="retry-verification">
                <p className="t-label">Verify before retry</p>
                <TurnstileWidget ref={retryWidgetRef} siteKey={turnstileSiteKey} onToken={setRetryToken} />
              </div>
            )}
            <button
              type="button"
              className="btn"
              disabled={loading || secondsLeft > 0 || (!!turnstileSiteKey && !retryToken)}
              onClick={() => {
                onRetry(retryToken)
                setRetryToken('')
                retryWidgetRef.current?.reset()
              }}
            >
              Retry analysis
            </button>
          </div>
        )}
      </>
    )
  }

  if (loading && !data) {
    return (
      <>
        {head}
        <PartPending label="Writing. About 20 seconds">
          The analysis is still being written. The finding above is final. This part
          adds what to do about it, and the confidence word on the plate fills at the
          same moment.
        </PartPending>
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
        <div className="prose">{renderBlocks(toBlocks(data.analysis))}</div>
      </>
    )
  }

  return (
    <>
      {head}
      <div className="stack">
        {sections.map(({ title, content }, s) => (
          <div className="prose" key={`${s}-${title}`}>
            <h3 className="t-h3 prose-title">{title}</h3>
            {renderBlocks(toBlocks(content))}
          </div>
        ))}
      </div>
    </>
  )
}
