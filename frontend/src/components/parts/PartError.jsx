// A failed or rate-limited stage. A ruled block with a label word, so a reader
// scanning the record tells a failure from a finding without reading the prose.
export default function PartError({ label, children }) {
  return (
    <div className="error-block">
      <p className="t-label">{label}</p>
      <p>{children}</p>
    </div>
  )
}
