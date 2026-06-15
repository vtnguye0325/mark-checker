import { useState } from 'react'
import AbercrombieSpectrum from '../AbercrombieSpectrum'
import ProbBar from './ProbBar'
import AttributionChart from './AttributionChart'
import LLMAnalysis from './llm/LLMAnalysis'

export default function ResultPanel({
  result,
  liveMark,
  loading,
  explainLoading,
  explainData,
  llmLoading,
  llmData,
}) {
  const [debugOpen, setDebugOpen] = useState(false)

  if (loading) {
    return (
      <div className="result-loading">
        {liveMark && <div className="result-mark result-mark--dim">{liveMark}</div>}
        <div className="loading-row">
          <div className="loading-dots"><span /><span /><span /></div>
          <p className="loading-text">Analyzing mark…</p>
        </div>
      </div>
    )
  }

  if (!result) return null

  const isDistinctive = result.label === 'distinctive'
  const displayMark = result.mark || liveMark

  return (
    <div className={`result-content ${isDistinctive ? 'result--distinctive' : 'result--not'}`}>
      <div className="result-hero">
        <div className="result-mark">{displayMark}</div>
        <div className={`verdict-badge ${isDistinctive ? 'verdict--distinctive' : 'verdict--not'}`}>
          <span className="verdict-icon">{isDistinctive ? '◆' : '◇'}</span>
          <span className="verdict-text">
            {isDistinctive ? 'Distinctive' : 'Not Distinctive'}
          </span>
        </div>
      </div>

      <div className="prob-section">
        <ProbBar label="Distinctiveness" value={result.prob_distinctive} isMain={isDistinctive} />
      </div>

      <AbercrombieSpectrum />

      <div className="result-actions">
        {explainLoading && (
          <span className="explain-status">
            <span className="btn-spinner btn-spinner--sm" /> Analyzing features…
          </span>
        )}
      </div>

      {explainData && <AttributionChart attributions={explainData.attributions} />}

      <LLMAnalysis loading={llmLoading} data={llmData} />

      <div className="debug-section">
        <button className="debug-toggle" onClick={() => setDebugOpen(o => !o)}>
          {debugOpen ? '▲' : '▼'} Model Input
        </button>
        {debugOpen && (
          <pre className="debug-text">{result.formatted_input?.replace(/\. /g, '\n')}</pre>
        )}
      </div>
    </div>
  )
}
