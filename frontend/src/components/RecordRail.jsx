// The metadata rows and the part index. `parts` is an array of
// { id, name, no, status, present }. Render a link when the part is on the page
// and a plain row when it is not.
export default function RecordRail({ meta, parts, current }) {
  const metaRows = [
    ['Filed', meta.filed],
    ['Class', meta.nice_class],
    ['Score', meta.score],
    ['Model', meta.model],
    ['Sources', meta.sources],
  ]

  return (
    <aside className="rail">
      <div className="rail-meta">
        <p className="t-label" style={{ marginBottom: '16px' }}>Record</p>
        <div className="rail-rows">
          {metaRows.map(([label, value]) => (
            <div className="rail-row" key={label}>
              <span>{label}</span>
              <span>{value ?? '—'}</span>
            </div>
          ))}
        </div>
      </div>
      <nav className="rail-nav" aria-label="Parts of this record">
        <p className="t-label" style={{ marginBottom: '16px' }}>Parts</p>
        <div className="rail-links">
          {parts.map((part) =>
            part.present ? (
              <a
                className={`rail-link${part.id === current ? ' rail-link--here' : ''}`}
                href={`#${part.id}`}
                key={part.id}
                aria-current={part.id === current ? 'location' : undefined}
              >
                <span>{part.name}</span>
                <span className="mono">{part.status}</span>
              </a>
            ) : (
              <div className="rail-row" key={part.id}>
                <span>{part.name}</span>
                <span className="mono">{part.status}</span>
              </div>
            )
          )}
        </div>
      </nav>
    </aside>
  )
}
