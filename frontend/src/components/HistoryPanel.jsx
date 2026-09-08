import { useCallback, useEffect, useRef, useState } from 'react'
import { useScrollSpy } from '../hooks/useScrollSpy'
import RecordPlate from './RecordPlate'
import RecordRail from './RecordRail'
import PartSpectrum from './parts/PartSpectrum'
import PartBasis from './parts/PartBasis'
import PartAuthority from './parts/PartAuthority'
import PartAction from './parts/PartAction'
import PartInput from './parts/PartInput'

const LIST_LIMIT = 50

// GET /history and GET /history/{id}. Both filter by the session user on the
// server, so this component never sends an id it owns; it only renders what
// comes back. A 401 means the session lapsed; a 429 means the per-IP rate limit;
// a 503 means Postgres is down.
async function getJSON(url, signal) {
  const resp = await fetch(url, { credentials: 'include', signal })
  if (resp.status === 401) {
    const err = new Error('Sign in again to see your history.')
    err.code = 401
    throw err
  }
  if (resp.status === 429) {
    throw new Error('Too many requests. Wait a moment and try again.')
  }
  if (!resp.ok) {
    let detail = 'History is unavailable right now.'
    try {
      // FastAPI validation errors send `detail` as a list of objects; only take
      // a plain string. slowapi sends `error`, not `detail`, so 429 is handled
      // above and never reaches here.
      const body = await resp.json()
      if (typeof body.detail === 'string') detail = body.detail
    } catch {
      // keep the default
    }
    throw new Error(detail)
  }
  return resp.json()
}

function fmtDate(iso) {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
}

// A stored row carries the same fields the live pipeline produces, so the part
// components render it unchanged. Every stage is finished, so loading is false
// and the per-stage error is null. A stage that never completed left its column
// null; the part component then shows its own empty state.
function shapeRecord(row) {
  const result = {
    label: row.label,
    prob_distinctive: row.prob_distinctive,
    mark: row.mark,
    description: row.description,
    nice_class: row.nice_class,
    formatted_input: row.formatted_input,
  }
  const explainData = Array.isArray(row.attributions) ? { attributions: row.attributions } : null
  const llmData = row.analysis ? { analysis: row.analysis, sources: row.sources ?? null } : null
  return { result, explainData, llmData }
}

function DetailView({ row, onBack }) {
  const { result, explainData, llmData } = shapeRecord(row)
  const parts = [
    { id: 'p1', name: 'Spectrum', no: '01', status: 'Ready', present: true },
    { id: 'p2', name: 'Basis', no: '02', status: explainData ? 'Ready' : 'Unavailable', present: true },
    { id: 'p3', name: 'Authority', no: '03', status: llmData ? 'Ready' : 'Unavailable', present: true },
    { id: 'p4', name: 'Action', no: '04', status: llmData ? 'Ready' : 'Unavailable', present: true },
    { id: 'p5', name: 'Input', no: '05', status: 'Ready', present: true },
  ]
  const current = useScrollSpy(parts.length)
  const sources = llmData?.sources
  const sourceCount = sources
    ? (sources.tmep?.length || 0) + (sources.ttab?.length || 0)
    : 0
  const meta = {
    filed: fmtDate(row.created_at),
    nice_class: row.nice_class ?? null,
    score: Number.isFinite(row.prob_distinctive) ? row.prob_distinctive.toFixed(2) : null,
    model: 'ModernBERT',
    sources: sourceCount || null,
  }
  const accent = result.label === 'distinctive' ? 'record--distinctive' : result.label ? 'record--not' : ''

  return (
    <div className={accent}>
      <button type="button" className="btn btn--secondary history-back" onClick={onBack}>
        Back to the list
      </button>
      <RecordPlate result={result} llmData={llmData} llmLoading={false} llmError={null} explainError={null} />
      <div className="doc">
        <RecordRail meta={meta} parts={parts} current={current} />
        <main className="body">
          <section className="part" id="p1">
            <PartSpectrum score={result.prob_distinctive} />
          </section>
          <section className="part" id="p2">
            <PartBasis loading={false} data={explainData} error={null} />
          </section>
          <section className="part" id="p3">
            <PartAuthority loading={false} data={llmData} error={null} explainError={null} />
          </section>
          <section className="part" id="p4">
            <PartAction loading={false} data={llmData} error={null} explainError={null} />
          </section>
          <section className="part" id="p5">
            <PartInput formattedInput={result.formatted_input} />
          </section>
        </main>
      </div>
    </div>
  )
}

export default function HistoryPanel({ onSessionExpired }) {
  const [items, setItems] = useState(null)
  const [listError, setListError] = useState(null)
  const [selected, setSelected] = useState(null)
  const [detailError, setDetailError] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)
  // Rising counter so a slow detail fetch that resolves after a newer click, or
  // after unmount, is dropped instead of setting state.
  const reqRef = useRef(0)
  const mountedRef = useRef(true)

  const handle401 = useCallback(() => {
    if (onSessionExpired) onSessionExpired()
  }, [onSessionExpired])

  useEffect(() => {
    mountedRef.current = true
    const ctrl = new AbortController()
    getJSON(`/history?limit=${LIST_LIMIT}`, ctrl.signal)
      .then((data) => mountedRef.current && setItems(data))
      .catch((err) => {
        if (err.name === 'AbortError' || !mountedRef.current) return
        if (err.code === 401) handle401()
        setListError(err.message)
      })
    return () => {
      mountedRef.current = false
      ctrl.abort()
    }
  }, [handle401])

  const openRecord = useCallback((id) => {
    const myReq = ++reqRef.current
    setDetailError(null)
    setDetailLoading(true)
    getJSON(`/history/${id}`)
      .then((row) => {
        if (myReq !== reqRef.current || !mountedRef.current) return
        setSelected(row)
        window.scrollTo(0, 0)
      })
      .catch((err) => {
        if (myReq !== reqRef.current || !mountedRef.current) return
        if (err.code === 401) handle401()
        setDetailError(err.message)
      })
      .finally(() => {
        if (myReq === reqRef.current && mountedRef.current) setDetailLoading(false)
      })
  }, [handle401])

  if (selected) {
    return <DetailView row={selected} onBack={() => setSelected(null)} />
  }

  return (
    <div className="doc">
      <aside className="rail">
        <p className="t-label" style={{ marginBottom: '16px' }}>History</p>
        <p className="t-small dim">Your own checks, newest first. Nobody else can see them.</p>
      </aside>
      <main className="body">
        <div className="part-head">
          <span className="part-no">Record</span>
          <h2 className="t-h2">Your checks</h2>
        </div>

        {listError && <div className="error-block"><p className="t-label">Unavailable</p><p>{listError}</p></div>}
        {detailError && <div className="error-block"><p className="t-label">Unavailable</p><p>{detailError}</p></div>}

        {!listError && items === null && <p className="t-body dim">Loading your history…</p>}

        {!listError && items && items.length === 0 && (
          <p className="t-body dim">You have not run a check yet. Your checks show here once you do.</p>
        )}

        {items && items.length > 0 && (
          <div className="index">
            {items.map((it) => (
              <button
                type="button"
                key={it.id}
                className="history-row row"
                onClick={() => openRecord(it.id)}
                disabled={detailLoading}
              >
                <span>
                  <span className="t-h3">{it.mark}</span>{' '}
                  <span className="t-small dim mono">NC {it.nice_class}</span>
                </span>
                <span className="row-val t-small">
                  {it.label === 'distinctive' ? 'Distinctive' : it.label === 'not_distinctive' ? 'Not distinctive' : '—'}
                  {' · '}
                  <span className="mono">
                    {Number.isFinite(it.prob_distinctive) ? it.prob_distinctive.toFixed(2) : '—'}
                  </span>
                  {' · '}
                  {fmtDate(it.created_at)}
                </span>
              </button>
            ))}
          </div>
        )}

        {items && items.length === LIST_LIMIT && (
          <p className="t-small dim" style={{ marginTop: '16px' }}>
            Showing your {LIST_LIMIT} most recent checks.
          </p>
        )}
      </main>
    </div>
  )
}
