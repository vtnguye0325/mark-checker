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
  llmError,
}) {
  const [debugOpen, setDebugOpen] = useState(false)

  // Only block on the first stage (/predict). Once `result` lands, render the
  // verdict and let the slower stages (features, LLM) fill in as each finishes.
  if (loading && !result) {
    return (
      <div className="result-loading">
        {liveMark && <div className="result-mark result-mark--dim">{liveMark}</div>}
        <div className="loading-row">
          <div className="loading-dots"><span /><span /><span /></div>
          <p className="loading-text">Classifying mark…</p>
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

      {llmError && <div className="error-message">{llmError}</div>}
      <LLMAnalysis loading={llmLoading} data={llmData} />

      <div className="debug-section">
        <button className="debug-toggle" onClick={() => setDebugOpen(o => !o)}>
          {debugOpen ? '▲' : '▼'} Model Input
        </button>
        {debugOpen && (
          <div className="debug-blocks">
            <div className="debug-block">
              <div className="debug-block-label">Classifier Input</div>
              <pre className="debug-text">{result.formatted_input?.replace(/\. /g, '\n')}</pre>
            </div>
            {llmData?.prompt && (
              <>
                <div className="debug-block">
                  <div className="debug-block-label">LLM System Prompt</div>
                  <pre className="debug-text">{llmData.prompt.system}</pre>
                </div>
                <div className="debug-block">
                  <div className="debug-block-label">LLM User Message</div>
                  <pre className="debug-text">{llmData.prompt.user}</pre>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
