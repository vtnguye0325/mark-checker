// The tier table is the single source for Part 01 and the plate's score row.

export const SPECTRUM_TIERS = [
  { id: 'generic', label: 'Generic', range: [0.0, 0.28], note: 'Never registrable' },
  { id: 'descriptive', label: 'Descriptive', range: [0.28, 0.5], note: 'Needs acquired meaning' },
  { id: 'suggestive', label: 'Suggestive', range: [0.5, 0.7], note: 'Inherently distinctive' },
  { id: 'arbitrary', label: 'Arbitrary', range: [0.7, 0.88], note: 'Inherently distinctive' },
  { id: 'fanciful', label: 'Fanciful', range: [0.88, 1.0], note: 'Strongest protection' },
]

export function deriveCategory(probDistinctive) {
  if (!Number.isFinite(probDistinctive)) return null
  if (probDistinctive >= 0.88) return 'fanciful'
  if (probDistinctive >= 0.7) return 'arbitrary'
  if (probDistinctive >= 0.5) return 'suggestive'
  if (probDistinctive >= 0.28) return 'descriptive'
  return 'generic'
}
