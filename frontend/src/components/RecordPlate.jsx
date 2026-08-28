import { extractVerdict } from '../lib/parseLegalAnalysis'

// The confidence row fills late, from stage 3. See IMPLEMENTATION_PLAN_D.md 2.4.
// Print `Pending` until stage 3 lands, then the scraped word. Print `Unavailable`
// if stage 3 fails, returns 429, or carries no confidence word.
function deriveConfidence({ llmData, llmLoading, llmError, explainError }) {
  // A failed stage 2 skips stage 3 entirely, so the word never arrives.
  if (llmError || explainError) return 'Unavailable'
  if (llmLoading || !llmData) return 'Pending'
  const { confidence } = extractVerdict(llmData.analysis || '')
  if (!confidence) return 'Unavailable'
  return confidence.charAt(0).toUpperCase() + confidence.slice(1)
}

export default function RecordPlate({ result, llmData, llmLoading, llmError, explainError }) {
  const isDistinctive = result.label === 'distinctive'
  const verdict = isDistinctive ? 'Distinctive' : 'Not distinctive'
  const mark = result.mark
  const score = Number.isFinite(result.prob_distinctive)
    ? result.prob_distinctive.toFixed(2)
    : 'Unavailable'
  const confidence = deriveConfidence({ llmData, llmLoading, llmError, explainError })

  return (
    <section className="plate">
      <div className="plate-verdict">
        <p className="t-label dim-on-ink">Finding</p>
        <h1 className="t-display">{verdict}</h1>
        <p className="t-body dim-on-ink" style={{ maxWidth: '52ch' }}>
          The classifier reads this mark as {isDistinctive ? 'inherently distinctive' : 'not inherently distinctive'}.
          That is a first read, not a registration decision and not legal advice.
        </p>
      </div>
      <div className="plate-side">
        <p className="t-label dim-on-ink" style={{ marginBottom: '8px' }}>Subject of this record</p>
        <p className="plate-mark">{mark}</p>
        <div className="index index--on-ink">
          <div className="row">
            <span className="t-label dim-on-ink">Goods &amp; services</span>
            <span className="row-val t-small">{result.description || '—'}</span>
          </div>
          <div className="row">
            <span className="t-label dim-on-ink">NICE class</span>
            <span className="row-val mono t-small">{result.nice_class ?? '—'}</span>
          </div>
          <div className="row">
            <span className="t-label dim-on-ink">Score</span>
            <span className="row-val mono t-h3">{score}</span>
          </div>
          <div className="row">
            <span className="t-label dim-on-ink">Confidence</span>
            <span className="row-val t-h3">{confidence}</span>
          </div>
        </div>
      </div>
    </section>
  )
}
