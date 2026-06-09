import ProgressBar from './ui/ProgressBar'

const HIDDEN_FIELDS = new Set(['Mark Length', 'NICE Category', 'Translation'])

export default function AttributionChart({ attributions }) {
  const visible = attributions.filter(a => !HIDDEN_FIELDS.has(a.field))
  const maxAbs = Math.max(...visible.map(a => Math.abs(a.attribution)), 0.001)

  const truncate = (s, n) => (s.length > n ? `${s.slice(0, n)}…` : s)

  return (
    <div className="attr-chart">
      <div className="attr-title">Feature Attributions</div>
      <div className="attr-subtitle">
        How much each field shifts the distinctiveness score
      </div>
      {visible.map(({ field, value, attribution }) => {
        const barPct = (Math.abs(attribution) / maxAbs) * 100
        const isPos = attribution >= 0
        const fillClass = `attr-bar-fill ${isPos ? 'attr-bar--pos' : 'attr-bar--neg'}`
        return (
          <div key={field} className="attr-row">
            <div className="attr-meta">
              <span className="attr-field">{field}</span>
              <span className="attr-value">{truncate(value, 38)}</span>
            </div>
            <div className="attr-bar-wrap">
              <ProgressBar
                value={barPct}
                max={100}
                trackClassName="attr-bar-track"
                indicatorClassName={fillClass}
                getValueLabel={(v, max) =>
                  `${field}: ${isPos ? '+' : '−'}${Math.round((v / max) * 100)}% of max attribution`
                }
              />
            </div>
          </div>
        )
      })}
      <p className="attr-legend">
        <span className="attr-legend-pos">■ positive</span> — field pushes toward distinctive
        &nbsp;&nbsp;
        <span className="attr-legend-neg">■ negative</span> — field pushes against it
      </p>
    </div>
  )
}
