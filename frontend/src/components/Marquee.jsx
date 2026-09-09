// The Abercrombie spectrum as a moving band. This is the one continuous
// animation on the page. See docs/DESIGN_PRINCIPLES.md 7. The track holds the
// five tiers twice, so the loop from 0 to -50% shows no seam.
const TIERS = ['Generic', 'Descriptive', 'Suggestive', 'Arbitrary', 'Fanciful']

function tierClass(name) {
  if (name === 'Generic') return 'marquee-g'
  if (name === 'Fanciful') return 'marquee-f'
  return undefined
}

export default function Marquee() {
  return (
    <div className="marquee" role="img" aria-label="The Abercrombie spectrum, from generic to fanciful">
      <div className="marquee-track" aria-hidden="true">
        {[0, 1].map((pass) =>
          TIERS.map((name) => (
            <span key={`${pass}-${name}`} className={tierClass(name)}>{name}</span>
          ))
        )}
      </div>
    </div>
  )
}
