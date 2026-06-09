const SPECTRUM = [
  {
    id: 'generic',
    label: 'Generic',
    desc: 'Non Distinctive',
    stripColor: '#9e2a2a',
  },
  {
    id: 'descriptive',
    label: 'Descriptive',
    desc: 'Non Distinctive',
    stripColor: '#b45a1a',
  },
  {
    id: 'suggestive',
    label: 'Suggestive',
    desc: 'Inherently distinctive',
    stripColor: '#6d5a1c',
  },
  {
    id: 'arbitrary',
    label: 'Arbitrary',
    desc: 'Inherently distinctive',
    stripColor: '#1a6b42',
  },
  {
    id: 'fanciful',
    label: 'Fanciful',
    desc: 'Inherently distinctive',
    stripColor: '#158050',
  },
]

function deriveCategory(probDistinctive) {
  if (probDistinctive >= 0.88) return 'fanciful'
  if (probDistinctive >= 0.70) return 'arbitrary'
  if (probDistinctive >= 0.50) return 'suggestive'
  if (probDistinctive >= 0.28) return 'descriptive'
  return 'generic'
}

export { deriveCategory }

export default function AbercrombieSpectrum() {
  return (
    <div className="abcr">
      <div className="abcr-header">
        <span className="abcr-section-label">Abercrombie Spectrum</span>
      </div>

      <div className="abcr-segments">
        {SPECTRUM.map((seg) => (
          <div
            key={seg.id}
            className="abcr-seg"
            style={{ '--strip': seg.stripColor }}
          >
            <span className="abcr-seg-name">{seg.label}</span>
          </div>
        ))}
      </div>

      <div className="abcr-descs">
        {SPECTRUM.map((seg) => (
          <div key={seg.id} className="abcr-desc-item">
            {seg.desc}
          </div>
        ))}
      </div>
    </div>
  )
}
