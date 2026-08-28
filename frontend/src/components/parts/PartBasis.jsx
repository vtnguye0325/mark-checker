import PartError from './PartError'

// Part 02 — the signed attribution track. Replaces AttributionChart.
const HIDDEN_FIELDS = new Set(['Mark Length', 'NICE Category', 'Translation'])

const truncate = (s, n) => (s.length > n ? `${s.slice(0, n)}…` : s)

export default function PartBasis({ loading, data, error }) {
  const head = (
    <div className="part-head">
      <span className="part-no">Part 02</span>
      <h2 className="t-h2">Basis for the finding</h2>
    </div>
  )

  if (error) {
    return (
      <>
        {head}
        <PartError label="Unavailable">{error}</PartError>
        <p className="t-small dim" style={{ marginTop: '16px' }}>
          Parts 03 and 04 depend on this step, so they are unavailable too.
        </p>
      </>
    )
  }

  if (loading && !data) {
    return (
      <>
        {head}
        <div className="index">
          <div className="row row--tall">
            <span className="t-small dim">Measuring each field in turn…</span>
            <span className="row-val t-label dim">Running</span>
          </div>
          <div className="row row--tall">
            <span className="t-small dim">Retrieving TMEP and TTAB doctrine</span>
            <span className="row-val t-label dim">Queued</span>
          </div>
        </div>
      </>
    )
  }

  if (!data) {
    return (
      <>
        {head}
        <p className="t-body dim">The basis step has not run yet.</p>
      </>
    )
  }

  // The endpoint answered 200, but the body is not the documented shape. Treat it
  // as a failed part, so a bad proxy response does not crash the page.
  if (!Array.isArray(data.attributions)) {
    return (
      <>
        {head}
        <PartError label="Unavailable">The basis step returned an unreadable response.</PartError>
        <p className="t-small dim" style={{ marginTop: '16px' }}>
          Parts 03 and 04 depend on this step, so they are unavailable too.
        </p>
      </>
    )
  }

  const visible = data.attributions
    .filter((a) => a && Number.isFinite(a.attribution) && !HIDDEN_FIELDS.has(a.field))

  if (visible.length === 0) {
    return (
      <>
        {head}
        <p className="t-small dim">No field contributions to show.</p>
      </>
    )
  }

  const maxAbs = Math.max(...visible.map((a) => Math.abs(a.attribution)), 0.001)

  return (
    <>
      {head}
      <p className="t-body" style={{ marginBottom: '32px' }}>
        Each input field was blanked in turn and the score re-measured. The swing is
        that field's contribution to the finding on the plate.
      </p>
      <div className="index">
        {visible.map(({ field, value, attribution }) => {
          const abs = Math.abs(attribution)
          const pct = (abs / maxAbs) * 100 + '%'
          const sign = attribution > 0 ? '+' : attribution < 0 ? '−' : ''
          const word = attribution > 0 ? 'toward' : attribution < 0 ? 'against' : 'neutral'
          return (
            <div key={field} className="attr">
              <div className="attr-head">
                <span>
                  <span className="t-h3">{field}</span>{' '}
                  <span className="t-small dim mono">{truncate(String(value ?? ''), 38)}</span>
                </span>
                <span className="mono t-small">{sign}{abs.toFixed(2)} {word}</span>
              </div>
              <div className="attr-track">
                <span className="attr-neg">
                  {attribution < 0 && <i className="attr-outline" style={{ width: pct }} />}
                </span>
                <span className="attr-pos">
                  {attribution > 0 && <i className="attr-fill" style={{ width: pct }} />}
                </span>
              </div>
            </div>
          )
        })}
      </div>
      <p className="t-small dim" style={{ marginTop: '16px', maxWidth: '68ch' }}>
        <span style={{ display: 'inline-block', width: '20px', height: '10px', background: 'var(--ink)', marginRight: '8px' }} />
        Filled, right of the axis: the field pushes toward distinctive. &nbsp;
        <span style={{ display: 'inline-block', width: '20px', height: '10px', border: '1px solid var(--ink)', marginRight: '8px' }} />
        Outlined, left of the axis: it pushes against. Fill and side carry the sign,
        so the chart reads without color.
      </p>
    </>
  )
}
