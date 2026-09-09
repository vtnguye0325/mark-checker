import PartError from './PartError'
import PartPending from './PartPending'

// Part 03 — the sources the analysis read. Replaces LegalSources.
export default function PartAuthority({ loading, data, error, explainError }) {
  const head = (
    <div className="part-head">
      <span className="part-no">Part 03</span>
      <h2 className="t-h2">Our sources</h2>
    </div>
  )

  if (explainError) {
    return (
      <>
        {head}
        <PartError label="Unavailable">
          The earlier step did not complete, so we read no sources.
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
          The answer names its sources. Without the answer, this part stays empty.
        </p>
      </>
    )
  }

  if (loading && !data) {
    return (
      <>
        {head}
        <PartPending label="Retrieving. About 20 seconds">
          We are reading the trademark manual and past decisions. They appear here
          when the answer lands.
        </PartPending>
      </>
    )
  }

  if (!data) {
    return (
      <>
        {head}
        <p className="t-body dim">Queued.</p>
      </>
    )
  }

  const tmep = data.sources?.tmep ?? []
  const ttab = data.sources?.ttab ?? []

  if (tmep.length === 0 && ttab.length === 0) {
    return (
      <>
        {head}
        <p className="t-body dim">The answer cited no outside source.</p>
      </>
    )
  }

  const first = tmep[0]?.text ? tmep[0] : null
  const rest = first ? tmep.slice(1) : tmep
  const showAlso = rest.length > 0 || ttab.length > 0

  return (
    <>
      {head}
      <p className="lead">
        We read these sections before writing the answer. The answer uses nothing else.
        TMEP is the trademark examiner's manual. TTAB is the trademark appeal board.
      </p>

      {first && (
        <blockquote className="quote">
          {first.text}
          <cite>
            TMEP § {first.metadata?.section_number ?? '—'}. {first.metadata?.section_title ?? '—'}
          </cite>
        </blockquote>
      )}

      {showAlso && (
        <>
          <p className="t-label" style={{ marginBottom: '14px' }}>
            {first ? 'Also retrieved, not cited' : 'Retrieved'}
          </p>
          <div className="index">
            {rest.map((c, i) => (
              <div className="row" key={c?.id ?? `tmep-${i}`}>
                <span>
                  <span className="mono t-small">§ {c.metadata?.section_number ?? '—'}</span>{' '}
                  <span className="t-h3">{c.metadata?.section_title ?? '—'}</span>
                </span>
                <span className="row-val t-small dim">TMEP</span>
              </div>
            ))}
            {ttab.map((c, i) => (
              <div className="row" key={c?.id ?? `ttab-${i}`}>
                <span>
                  <span className="t-h3">{c.metadata?.mark ?? '—'}</span>{' '}
                  <span className="mono t-small dim">NC {c.metadata?.nice_class ?? '—'}</span>
                </span>
                <span className="row-val t-small dim">TTAB. {c.metadata?.outcome ?? '—'}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </>
  )
}
