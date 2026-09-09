// The long explainer behind the "Read the method" button on the landing page.
// It uses the part layout of the record, so the two states read the same.
// See docs/DESIGN_PRINCIPLES.md 9.
const SECTIONS = [
  {
    no: '01',
    name: 'Classify',
    body: [
      'A ModernBERT classifier reads the mark, the goods description, and the NICE class as one text. It returns a probability from 0.00 to 1.00 that the mark is distinctive.',
      'The Abercrombie spectrum orders marks from generic to descriptive, suggestive, arbitrary, and fanciful. A generic term names the goods and cannot register. A fanciful term is coined for the goods and registers most easily. The score places the mark on that line. It is a probability, never a certainty.',
    ],
  },
  {
    no: '02',
    name: 'Attribute',
    body: [
      'The service blanks each input field in turn and runs the classifier again. The change in the score is the weight of that field.',
      'A large swing on the goods description means the mark reads as descriptive of those goods. A large swing on the mark itself means the name carries the finding on its own.',
    ],
  },
  {
    no: '03',
    name: 'Cite',
    body: [
      'A retrieval step searches the TMEP and the TTAB decisions for passages that match the mark and the goods. The language model then writes the analysis from those passages only.',
      'Each record states the finding, the recommended action, and the risk. Every claim points to a section or a decision that you can open and read.',
    ],
  },
]

const LIMITS = [
  'The service reads the mark as text. It does not search the USPTO register for a conflicting mark.',
  'The classifier is trained on past records. A new class of goods or a new form of name can fall outside that training.',
  'The service keeps a record of each check that you run. You can read that history when you sign in.',
  'This is a first read. It is not legal advice, and it does not replace a trademark attorney.',
]

export default function MethodPage({ onBack }) {
  return (
    <main className="method">
      <section className="method-head">
        <h1 className="method-title">The method</h1>
        <p className="method-deck">
          Three stages run in order on every check. Each stage adds one part to the record.
          This page states what each stage does and where the numbers come from.
        </p>
      </section>

      {SECTIONS.map((s) => (
        <section className="method-part" key={s.no}>
          <div className="method-part-head">
            <span className="method-no">Stage {s.no}</span>
            <h2 className="method-name">{s.name}</h2>
          </div>
          {s.body.map((p) => <p className="method-text" key={p.slice(0, 24)}>{p}</p>)}
        </section>
      ))}

      <section className="method-part">
        <div className="method-part-head">
          <span className="method-no">Limits</span>
          <h2 className="method-name">What it does not do</h2>
        </div>
        <ul className="method-list">
          {LIMITS.map((l) => <li key={l.slice(0, 24)}>{l}</li>)}
        </ul>
      </section>

      <div className="close">
        <p>Every check writes one record. Start one now.</p>
        <button type="button" className="btn btn--wide" onClick={onBack}>
          Check a name <span className="btn-arrow" aria-hidden="true">→</span>
        </button>
      </div>
    </main>
  )
}
