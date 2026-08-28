// Part 05 — the ruled lines from formatted_input. See IMPLEMENTATION_PLAN_D.md 2.5.
export default function PartInput({ formattedInput }) {
  const lines = (formattedInput || '').split('. ').filter(Boolean)

  return (
    <>
      <div className="part-head">
        <span className="part-no">Part 05</span>
        <h2 className="t-h2">Classifier input</h2>
      </div>
      <p className="t-body" style={{ marginBottom: '24px' }}>
        The string below is the exact text the model read. Everything above derives from it.
      </p>
      {lines.length === 0 ? (
        <p className="t-small dim">The classifier input was not returned.</p>
      ) : (
        <div className="index">
          {lines.map((line, i) => (
            <div className="row" key={i}>
              <span className="mono t-small">{line}</span>
            </div>
          ))}
        </div>
      )}
    </>
  )
}
