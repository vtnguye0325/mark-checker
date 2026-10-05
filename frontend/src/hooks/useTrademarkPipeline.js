import { useState, useRef } from 'react'
import * as api from '../lib/api'
import { isValidProbability } from '../lib/spectrum'

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
  const [llmRetryAt, setLlmRetryAt] = useState(null)
  const abortRef = useRef(null)
  const assessmentRef = useRef(null)

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
    setLlmRetryAt(null)
    assessmentRef.current = null

    try {
      const data = await api.predict(payload, { signal: ctrl.signal, onAuthExpired })
      if (
        !data ||
        !['distinctive', 'not_distinctive'].includes(data.label) ||
        !isValidProbability(data.prob_distinctive)
      ) {
        throw new Error('The classifier returned an unreadable result. Check the fields and try again.')
      }
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
        if (!Array.isArray(explainResult?.attributions)) {
          throw new Error('The score breakdown returned an unreadable response.')
        }
        setExplainData(explainResult)
      } catch (err) {
        console.error(err)
        if (err.name !== 'AbortError' && abortRef.current === ctrl) {
          setExplainError(err.message || 'The score breakdown did not complete.')
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
          assessmentRef.current = { payload: analyzePayload, onAuthExpired, onAnalyzeComplete }
          const assessData = await api.assess(analyzePayload, {
            signal: ctrl.signal,
            onAuthExpired,
          })
          if (typeof assessData?.analysis !== 'string' || !assessData.analysis.trim()) {
            throw new Error('The analysis returned an unreadable response.')
          }
          if (abortRef.current !== ctrl) return
          setLlmData(assessData)
          assessmentRef.current = null
          onAnalyzeComplete?.()
        } catch (err) {
          console.error(err)
          if (err.name === 'AbortError' || abortRef.current !== ctrl) {
            return
          }
          if (err.status === 429) {
            // A per-minute cap carries Retry-After and fits the wait-time line.
            // A daily cap carries no Retry-After and a message that names the
            // reset — show that verbatim so the user stops retrying.
            if (!err.retryAfter && err.detail) {
              setLlmError(err.detail)
              setLlmRetryAt(null)
            } else {
              const header = Number(err.retryAfter)
              const headerDate = Date.parse(err.retryAfter || '')
              const waitMs = Number.isFinite(header) && header > 0
                ? header * 1000
                : Number.isFinite(headerDate)
                  ? Math.max(0, headerDate - Date.now())
                  : 60_000
              const waitSeconds = Math.max(1, Math.ceil(waitMs / 1000))
              setLlmRetryAt(Date.now() + waitMs)
              setLlmError(`Too many analysis requests. Wait ${waitSeconds} seconds before you retry.`)
            }
          } else {
            setLlmError(err.message || 'The analysis did not complete. Retry when the service is available.')
            setLlmRetryAt(Date.now())
          }
          onAnalyzeComplete?.()
        } finally {
          if (abortRef.current === ctrl) setLlmLoading(false)
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError' && abortRef.current === ctrl) {
        setError(err instanceof TypeError
          ? 'We could not reach the service. Check your connection and retry.'
          : err.message)
      }
    } finally {
      if (abortRef.current === ctrl) setLoading(false)
    }
  }

  async function retryAssessment(turnstileToken = '') {
    const request = assessmentRef.current
    if (!request || !llmRetryAt || Date.now() < llmRetryAt) return
    if (abortRef.current) abortRef.current.abort()
    const ctrl = new AbortController()
    abortRef.current = ctrl
    setLlmLoading(true)
    setLlmError(null)
    setLlmRetryAt(null)
    try {
      const data = await api.assess(
        { ...request.payload, turnstile_token: turnstileToken },
        { signal: ctrl.signal, onAuthExpired: request.onAuthExpired },
      )
      if (typeof data?.analysis !== 'string' || !data.analysis.trim()) {
        throw new Error('The analysis returned an unreadable response.')
      }
      if (abortRef.current !== ctrl) return
      setLlmData(data)
      assessmentRef.current = null
    } catch (err) {
      if (err.name === 'AbortError' || abortRef.current !== ctrl) return
      if (err.status === 429) {
        if (!err.retryAfter && err.detail) {
          setLlmError(err.detail)
        } else {
          const header = Number(err.retryAfter)
          const headerDate = Date.parse(err.retryAfter || '')
          const waitMs = Number.isFinite(header) && header > 0
            ? header * 1000
            : Number.isFinite(headerDate)
              ? Math.max(0, headerDate - Date.now())
              : 60_000
          const waitSeconds = Math.max(1, Math.ceil(waitMs / 1000))
          setLlmRetryAt(Date.now() + waitMs)
          setLlmError(`Too many analysis requests. Wait ${waitSeconds} seconds before you retry.`)
        }
      } else {
        setLlmError(err.message || 'The analysis did not complete. Retry when the service is available.')
        setLlmRetryAt(Date.now())
      }
    } finally {
      if (abortRef.current === ctrl) {
        setLlmLoading(false)
        request.onAnalyzeComplete?.()
      }
    }
  }

  function reset() {
    if (abortRef.current) abortRef.current.abort()
    abortRef.current = null
    assessmentRef.current = null
    setResult(null)
    setError(null)
    setExplainData(null)
    setExplainError(null)
    setExplainLoading(false)
    setLlmData(null)
    setLlmLoading(false)
    setLlmError(null)
    setLlmRetryAt(null)
  }

  return {
    submit,
    retryAssessment,
    reset,
    state: { loading, result, error, explainLoading, explainData, explainError, llmLoading, llmData, llmError, llmRetryAt },
  }
}
