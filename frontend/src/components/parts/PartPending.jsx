// A part that is still on its way. The yellow label states the wait, the
// prose states what arrives, and the bones hold the space. Bones do not move.
export default function PartPending({ label, children }) {
  return (
    <div className="pending-block" aria-busy="true">
      <p className="t-label pending-label">{label}</p>
      <p>{children}</p>
      <div className="bones" aria-hidden="true">
        <span className="bone" /><span className="bone" /><span className="bone" /><span className="bone" />
      </div>
    </div>
  )
}
