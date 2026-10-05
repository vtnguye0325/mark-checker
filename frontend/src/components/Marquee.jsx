// The Abercrombie spectrum as a moving band. This is the one continuous
// animation on the page. See docs/DESIGN_PRINCIPLES.md 7. The track holds the
// five tiers twice, so the loop from 0 to -50% shows no seam.
import { useEffect, useState } from 'react'

const TIERS = ['Generic', 'Descriptive', 'Suggestive', 'Arbitrary', 'Fanciful']

function tierClass(name) {
  if (name === 'Generic') return 'marquee-g'
  if (name === 'Fanciful') return 'marquee-f'
  return undefined
}

export default function Marquee() {
  const [playing, setPlaying] = useState(true)
  const [replayKey, setReplayKey] = useState(0)
  const [reduceMotion, setReduceMotion] = useState(false)

  useEffect(() => {
    const query = window.matchMedia('(prefers-reduced-motion: reduce)')
    const update = () => setReduceMotion(query.matches)
    update()
    query.addEventListener('change', update)
    return () => query.removeEventListener('change', update)
  }, [])

  return (
    <div className={`marquee${playing ? '' : ' marquee--paused'}`}>
      <div className="marquee-controls" aria-label="Spectrum animation controls">
        <span className="marquee-caption">The Abercrombie spectrum</span>
        <button type="button" className="marquee-control" onClick={() => setPlaying((value) => !value)} aria-label={playing ? 'Pause spectrum animation' : 'Play spectrum animation'}>
          {playing ? 'Pause' : 'Play'}
        </button>
        <button type="button" className="marquee-control" onClick={() => { setPlaying(true); setReplayKey((key) => key + 1) }} aria-label="Replay spectrum animation">
          Replay
        </button>
      </div>
      <div key={replayKey} className="marquee-track" aria-hidden="true">
        {[0, 1].map((pass) =>
          TIERS.map((name) => (
            <span key={`${pass}-${name}`} className={tierClass(name)}>{name}</span>
          ))
        )}
      </div>
      {reduceMotion && <span className="sr-only">Animation is off because reduced motion is enabled.</span>}
    </div>
  )
}
