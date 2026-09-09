import PartError from './PartError'
import PartPending from './PartPending'

// Part 04 — the signed attribution track. Replaces AttributionChart.
const HIDDEN_FIELDS = new Set(['Mark Length', 'NICE Category', 'Translation'])

const truncate = (s, n) => (s.length > n ? `${s.slice(0, n)}…` : s)

export default function PartBasis({ loading, data, error }) {
  const head = (
    <div className="part-head">
      <span className="part-no">Part 04</span>
      <h2 className="t-h2">Why this score</h2>
    </div>
  )

  if (error) {
    return (
      <>
        {head}
        <PartError label="Unavailable">{error}</PartError>
        <p className="key">
          Parts 02 and 03 depend on this step, so they are unavailable too.
        </p>
      </>
    )
  }

  if (loading && !data) {
    return (
      <>
        {head}
        <PartPending label="Measuring. About 10 seconds">
          We are removing each part of your name in turn to watch the score move.
          The reading of the manual and past decisions starts when this step ends.
        </PartPending>
      </>
    )
  }

  if (!data) {
    return (
      <>
        {head}
        <p className="t-body dim">The score breakdown has not run yet.</p>
      </>
    )
  }

  // The endpoint answered 200, but the body is not the documented shape. Treat it
  // as a failed part, so a bad proxy response does not crash the page.
  if (!Array.isArray(data.attributions)) {
    return (
      <>
        {head}
        <PartError label="Unavailable">The score breakdown returned an unreadable response.</PartError>
        <p className="key">
          Parts 02 and 03 depend on this step, so they are unavailable too.
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
      <p className="lead">
        We removed each part of your name in turn and watched the score move. A bigger
        bar means that part mattered more.
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
      <p className="key">
        <i className="key-fill" aria-hidden="true" />
        Bars to the right helped your score. &nbsp;
        <i className="key-outline" aria-hidden="true" />
        Bars to the left hurt it.
      </p>
    </>
  )
}
