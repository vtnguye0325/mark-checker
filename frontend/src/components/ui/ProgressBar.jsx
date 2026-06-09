import { Root, Indicator } from '@radix-ui/react-progress'

/**
 * Accessible progress bar built on @radix-ui/react-progress.
 * Visual styling uses existing App.css track/fill classes.
 */
export default function ProgressBar({
  value,
  max = 100,
  trackClassName = '',
  indicatorClassName = '',
  getValueLabel,
}) {
  const v = typeof value === 'number' && !Number.isNaN(value) ? value : 0
  const clamped = Math.min(Math.max(v, 0), max)
  const pct = max > 0 ? (clamped / max) * 100 : 0

  return (
    <Root
      className={trackClassName}
      value={clamped}
      max={max}
      getValueLabel={getValueLabel}
    >
      <Indicator
        className={indicatorClassName}
        style={{ '--target-width': `${pct}%` }}
      />
    </Root>
  )
}
