import PartError from './PartError'

// Part 03 — the authority the analysis relied on. Replaces LegalSources.
export default function PartAuthority({ loading, data, error, explainError }) {
  const head = (
    <div className="part-head">
      <span className="part-no">Part 03</span>
      <h2 className="t-h2">Authority relied on</h2>
    </div>
  )

  if (explainError) {
    return (
      <>
        {head}
        <PartError label="Unavailable">
          The basis step did not complete, so no authority was retrieved.
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
          The analysis names its authority; without it, this part stays empty.
        </p>
      </>
    )
  }

  if (loading && !data) {
    return (
      <>
        {head}
        <p className="t-body dim">The retrieval agent is still pulling passages.</p>
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
        <p className="t-body dim">The analysis cited no external authority.</p>
      </>
    )
  }

  const first = tmep[0]?.text ? tmep[0] : null
  const rest = first ? tmep.slice(1) : tmep
  const showAlso = rest.length > 0 || ttab.length > 0

  return (
    <>
      {head}
      <p className="t-body" style={{ marginBottom: '24px' }}>
        The retrieval agent pulled these passages before the analysis was written, and
        the analysis may cite nothing else.
      </p>

      {first && (
        <blockquote className="quote">
          {first.text}
          <cite className="t-label dim-on-ink">
            TMEP § {first.metadata?.section_number ?? '—'} — {first.metadata?.section_title ?? '—'}
          </cite>
        </blockquote>
      )}

      {showAlso && (
        <>
          <p className="t-label" style={{ marginTop: '48px' }}>
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
                <span className="row-val t-small">TTAB — {c.metadata?.outcome ?? '—'}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </>
  )
}
