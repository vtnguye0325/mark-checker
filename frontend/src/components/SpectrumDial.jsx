import { useState } from 'react'
import { SPECTRUM_TIERS, deriveCategory, isValidProbability } from '../lib/spectrum'

const EXAMPLES = ['SOFT', 'COPPERTONE', 'WHIRLPOOL', 'APPLE', 'KODAK']

function formatRange([low, high]) {
  return `${low.toFixed(2)}–${high.toFixed(2)}`
}

export default function SpectrumDial({ mode = 'explore', score }) {
  const [selected, setSelected] = useState(2)
  const validScore = isValidProbability(score)
  const activeId = validScore ? deriveCategory(score) : null
  const activeIndex = SPECTRUM_TIERS.findIndex((tier) => tier.id === activeId)
  const currentIndex = mode === 'explore' ? selected : activeIndex
  const currentTier = SPECTRUM_TIERS[currentIndex] ?? null
  const angle = validScore ? score * 270 - 135 : 0

  return (
    <section
      className={`dial-scene dial-scene--${mode}`}
      aria-label={mode === 'explore' ? 'Explore the distinctiveness spectrum' : 'Model score on the distinctiveness spectrum'}
    >
      <div className="dial" role={mode === 'explore' ? 'group' : undefined} aria-label={mode === 'explore' ? 'Five spectrum categories' : undefined}>
        <div className="dial-face" aria-hidden="true">
          <svg className="dial-ticks" viewBox="0 0 100 100">
            {Array.from({ length: 60 }, (_, index) => {
              const long = index % 5 === 0
              return (
                <line
                  key={index}
                  x1="50"
                  y1="1.5"
                  x2="50"
                  y2={long ? '5' : '3.5'}
                  transform={`rotate(${index * 6} 50 50)`}
                />
              )
            })}
          </svg>
        </div>
        {SPECTRUM_TIERS.map((tier, index) => {
          const positions = [
            { top: '76%', left: '27%' },
            { top: '30%', left: '14%' },
            { top: '11%', left: '50%' },
            { top: '30%', left: '86%' },
            { top: '76%', left: '73%' },
          ]
          const className = `dial-node${index === currentIndex ? ' is-selected' : ''}`
          const content = <span>{String(index + 1).padStart(2, '0')}</span>
          return mode === 'explore' ? (
            <button
              className={className}
              type="button"
              key={tier.id}
              style={positions[index]}
              onClick={() => setSelected(index)}
              aria-label={`${tier.label}, score range ${formatRange(tier.range)}, show definition`}
              aria-pressed={index === selected}
            >
              {content}
            </button>
          ) : (
            <span className={className} key={tier.id} style={positions[index]}>
              {content}
            </span>
          )
        })}
        {mode === 'result' && validScore && (
          <span className="dial-marker" style={{ '--score-angle': `${angle - 90}deg` }} aria-hidden="true">
            <span />
          </span>
        )}
        <div className="dial-center" aria-live="polite">
          {mode === 'explore' ? (
            <>
              <span className="dial-index">{String(currentIndex + 1).padStart(2, '0')} / 05</span>
              <strong>{currentTier?.label}</strong>
              <span className="dial-example">Example: {EXAMPLES[currentIndex]}</span>
            </>
          ) : (
            <>
              <span className="dial-index">{validScore ? 'MODEL SCORE' : 'SCORE'}</span>
              <strong>{currentTier?.label ?? 'Unavailable'}</strong>
              <span className="dial-example">{validScore ? score.toFixed(2) : 'No valid score returned'}</span>
            </>
          )}
        </div>
      </div>
      <div className="dial-caption">
        {mode === 'explore' ? (
          <>
            <span className="t-label">Selected category</span>
            <p>{currentTier?.note}. This example teaches the spectrum; it does not assess a mark.</p>
            <span className="t-label dial-caption-note">Select a number to explore</span>
          </>
        ) : (
          <>
            <span className="t-label">{currentTier ? `Category ${String(currentIndex + 1).padStart(2, '0')} / 05` : 'Result status'}</span>
            <p>{currentTier ? `${formatRange(currentTier.range)} · ${currentTier.note}` : 'The score did not return a valid value.'}</p>
          </>
        )}
      </div>
      {mode === 'explore' && (
        <ol className="dial-text-list" aria-label="Spectrum category definitions">
          {SPECTRUM_TIERS.map((tier, index) => (
            <li key={tier.id} className={index === selected ? 'is-selected' : ''}>
              <button type="button" onClick={() => setSelected(index)} aria-pressed={index === selected}>
                <span>{String(index + 1).padStart(2, '0')}</span>
                <span>{tier.label}</span>
                <span>{formatRange(tier.range)}</span>
              </button>
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}
