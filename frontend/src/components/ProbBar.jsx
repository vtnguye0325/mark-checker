import ProgressBar from './ui/ProgressBar'

export default function ProbBar({ label, value, isMain }) {
  const pct = Math.round(value * 100)
  return (
    <div className={`prob-row ${isMain ? 'prob-row--main' : ''}`}>
      <div className="prob-label">{label}</div>
      <ProgressBar
        value={pct}
        max={100}
        trackClassName="prob-track"
        indicatorClassName="prob-fill"
        getValueLabel={(v, max) => `${label}: ${Math.round((v / max) * 100)}%`}
      />
      <div className="prob-value">{pct}%</div>
    </div>
  )
}
