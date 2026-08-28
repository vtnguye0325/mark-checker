import { SPECTRUM_TIERS, deriveCategory } from '../../lib/spectrum'

// Part 01 — the ruled tier table. Fills the square on the matching row.
export default function PartSpectrum({ score }) {
  const activeId = deriveCategory(score)

  return (
    <>
      <div className="part-head">
        <span className="part-no">Part 01</span>
        <h2 className="t-h2">Position on the spectrum</h2>
      </div>

      <div className="index">
        {SPECTRUM_TIERS.map((tier) => {
          const here = tier.id === activeId
          const [lo, hi] = tier.range
          return (
            <div
              key={tier.id}
              className={`tier${here ? ' tier--here' : ''}`}
              aria-current={here ? 'true' : undefined}
            >
              <span className="tier-glyph" aria-hidden="true" />
              <span className="t-h3">{tier.label}{here ? ' — this mark' : ''}</span>
              <span className="tier-note">{tier.note}</span>
              <span className="tier-range">{lo.toFixed(2)}–{hi.toFixed(2)}</span>
            </div>
          )
        })}
      </div>

      {activeId ? (
        <p className="t-small dim" style={{ marginTop: '16px' }}>
          The filled square marks the tier. The score on the plate above falls inside
          the range printed on that row.
        </p>
      ) : (
        <p className="t-small dim" style={{ marginTop: '16px' }}>
          The classifier did not return a score, so no tier is marked.
        </p>
      )}
    </>
  )
}
