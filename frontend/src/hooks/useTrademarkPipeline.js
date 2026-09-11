import { useState, useRef } from 'react'
import * as api from '../lib/api'

export function useTrademarkPipeline() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [explainLoading, setExplainLoading] = useState(false)
  const [explainData, setExplainData] = useState(null)
  const [explainError, setExplainError] = useState(null)
  const [llmLoading, setLlmLoading] = useState(false)
  const [llmData, setLlmData] = useState(null)
  const [llmError, setLlmError] = useState(null)
  const abortRef = useRef(null)

  async function submit(payload, turnstileToken = '', opts = {}) {
    const { onAnalyzeComplete = null, onAuthExpired = null } = opts
    if (abortRef.current) abortRef.current.abort()
    const ctrl = new AbortController()
    abortRef.current = ctrl

    setLoading(true)
    setError(null)
    setResult(null)
    setExplainData(null)
    setExplainError(null)
    setLlmData(null)
    setLlmError(null)

    try {
      const data = await api.predict(payload, { signal: ctrl.signal, onAuthExpired })
      const queryId = data.query_id || null
      const predictResult = {
        ...data,
        mark: payload.mark,
        nice_class: payload.nice_class,
        description: payload.description,
      }
      setResult(predictResult)

      setExplainLoading(true)
      let explainResult = null
      try {
        explainResult = await api.explain(
          { ...payload, query_id: queryId },
          { signal: ctrl.signal, onAuthExpired },
        )
        setExplainData(explainResult)
      } catch (err) {
        console.error(err)
        if (err.name !== 'AbortError' && abortRef.current === ctrl) {
          setExplainError('The score breakdown did not complete. Try again.')
        }
      } finally {
        if (abortRef.current === ctrl) setExplainLoading(false)
      }

      if (explainResult) {
        setLlmLoading(true)
        try {
          const analyzePayload = {
            mark: predictResult.mark,
            description: payload.description,
            nice_class: predictResult.nice_class,
            label: predictResult.label,
            prob_distinctive: predictResult.prob_distinctive,
            attributions: explainResult.attributions,
            turnstile_token: turnstileToken,
            query_id: queryId,
          }
          const assessData = await api.assess(analyzePayload, {
            signal: ctrl.signal,
            onAuthExpired,
          })
          if (abortRef.current !== ctrl) return
          setLlmData(assessData)
          onAnalyzeComplete?.()
        } catch (err) {
          console.error(err)
          if (err.name === 'AbortError' || abortRef.current !== ctrl) {
            onAnalyzeComplete?.()
            return
          }
          if (err.status === 429) {
            // A per-minute cap carries Retry-After and fits the wait-time line.
            // A daily cap carries no Retry-After and a message that names the
            // reset — show that verbatim so the user stops retrying.
            if (!err.retryAfter && err.detail) {
              setLlmError(err.detail)
            } else {
              const wait = err.retryAfter ? `${err.retryAfter} seconds` : 'a moment'
              setLlmError(`Too many analysis requests. Please wait ${wait} and try again.`)
            }
          } else {
            setLlmError('The analysis did not complete. Try again.')
          }
          onAnalyzeComplete?.()
        } finally {
          if (abortRef.current === ctrl) setLlmLoading(false)
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError' && abortRef.current === ctrl) setError(err.message)
    } finally {
      if (abortRef.current === ctrl) setLoading(false)
    }
  }

  function reset() {
    setResult(null)
    setError(null)
    setExplainData(null)
    setExplainError(null)
    setExplainLoading(false)
    setLlmData(null)
    setLlmLoading(false)
    setLlmError(null)
  }

  return {
    submit,
    reset,
    state: { loading, result, error, explainLoading, explainData, explainError, llmLoading, llmData, llmError },
  }
}
