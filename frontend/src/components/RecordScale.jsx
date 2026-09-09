import { SPECTRUM_TIERS, deriveCategory } from '../lib/spectrum'

// The frozen scale: the landing marquee, stopped and measured. The five tiers
// sit in columns sized by their score range, and a pin marks the score.
export default function RecordScale({ score }) {
  const activeId = deriveCategory(score)
  const hasScore = Number.isFinite(score)
  const pinLeft = hasScore ? `${Math.min(100, Math.max(0, score * 100))}%` : null

  return (
    <section className="scale" aria-label="Where this mark sits on the Abercrombie spectrum">
      <div className="scale-head">
        <p className="t-label">The spectrum, measured</p>
        <p className="t-label dim-on-ink">
          {hasScore ? `Score ${score.toFixed(2)} of 1.00` : 'Score unavailable'}
        </p>
      </div>
      <div className="scale-track">
        {SPECTRUM_TIERS.map((tier) => {
          const [lo, hi] = tier.range
          return (
            <div key={tier.id} className={tier.id === activeId ? 'scale-here' : undefined}>
              <span className="scale-tier">{tier.label}</span>
              <span className="scale-range mono">{lo.toFixed(2)}–{hi.toFixed(2)}</span>
            </div>
          )
        })}
      </div>
      <div className="scale-pin">
        {pinLeft && (
          <>
            <i style={{ left: pinLeft }} />
            <span style={{ left: pinLeft }}>This mark</span>
          </>
        )}
      </div>
    </section>
  )
}
