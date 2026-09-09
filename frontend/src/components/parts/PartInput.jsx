// Part 05 — the eight fields the classifier read, as ruled lines.
// See IMPLEMENTATION_PLAN_D.md 2.5. The backend joins the fields with ". ",
// in this order (backend/app/services/text_formatter.py, format_mark).
const FIELD_LABELS = [
  'Mark',
  'Goods & services',
  'Translation',
  'WordNet flag',
  'Mark length',
  'NICE category',
  'NICE description',
  'Pseudo mark',
]

export default function PartInput({ formattedInput }) {
  const lines = (formattedInput || '').split('. ').filter(Boolean)
  // A goods description that holds ". " breaks the count. Then print the raw
  // lines without labels rather than mislabel them.
  const labelled = lines.length === FIELD_LABELS.length

  return (
    <>
      <div className="part-head">
        <span className="part-no">Part 05</span>
        <h2 className="t-h2">Your submission</h2>
      </div>
      <p className="lead">This is exactly what we read. Nothing else.</p>
      {lines.length === 0 ? (
        <p className="key">The classifier input was not returned.</p>
      ) : (
        <div className="index">
          {lines.map((line, i) => (
            <div className="inputline" key={i}>
              {labelled && <span className="inputline-k">{FIELD_LABELS[i]}</span>}
              <span className="inputline-v">{line}</span>
            </div>
          ))}
        </div>
      )}
    </>
  )
}
