// The landing explainer. Three stages, one line each, in the order that the
// pipeline runs them. The long version is the method page.
// See docs/DESIGN_PRINCIPLES.md 5.4 and 9.
const STAGES = [
  { no: '01', name: 'Classify', text: 'A classifier grades the mark on the Abercrombie spectrum.' },
  { no: '02', name: 'Attribute', text: 'Each field is blanked in turn to show how much it moved the score.' },
  { no: '03', name: 'Cite', text: 'A retrieval step pulls the TMEP sections and TTAB decisions behind the finding.' },
]

export default function HowItWorks({ onOpenMethod }) {
  return (
    <section className="how" id="how">
      <div className="how-head">
        <h2 className="how-title">How it works</h2>
        <p className="how-deck">Three stages run in order. Each stage adds one part to the record.</p>
      </div>
      <ol className="how-grid">
        {STAGES.map((s) => (
          <li className="how-step" key={s.no}>
            <span className="how-no">Stage {s.no}</span>
            <h3 className="how-name">{s.name}</h3>
            <p className="how-text">{s.text}</p>
          </li>
        ))}
      </ol>
      <div className="how-more">
        <button type="button" className="btn" onClick={onOpenMethod}>
          Read the method <span className="btn-arrow" aria-hidden="true">→</span>
        </button>
      </div>
    </section>
  )
}
