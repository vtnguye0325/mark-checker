import { useState, useRef } from 'react'

async function safeJson(res) {
  const text = await res.text()
  if (!text) return {}
  try { return JSON.parse(text) } catch { return { detail: text } }
}

// POST one stage. A 401 means the session expired mid-pipeline: ask the caller
// to re-authenticate, then retry the same stage once. Retry once only, or a
// backend that answers 401 forever loops.
async function authedFetch(url, body, ctrl, onAuthExpired) {
  const opts = {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(body),
    signal: ctrl.signal,
  }
  let res = await fetch(url, opts)
  if (res.status === 401 && onAuthExpired) {
    const ok = await onAuthExpired()
    if (ok) res = await fetch(url, opts)
  }
  return res
}

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
      const res = await authedFetch('/ml-predict', payload, ctrl, onAuthExpired)
      if (!res.ok) {
        const err = await safeJson(res)
        const msg = Array.isArray(err.detail)
          ? err.detail.map((d) => d.msg).join('; ')
          : (err.detail || 'Request failed')
        throw new Error(msg)
      }
      const data = await safeJson(res)
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
        const res2 = await authedFetch(
          '/llm-explain', { ...payload, query_id: queryId }, ctrl, onAuthExpired,
        )
        if (!res2.ok) throw new Error('Explain request failed')
        explainResult = await safeJson(res2)
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
          const res3 = await authedFetch('/llm-assess', analyzePayload, ctrl, onAuthExpired)
          if (abortRef.current !== ctrl) return
          if (res3.status === 429) {
            const retryAfter = res3.headers.get('Retry-After')
            const body = await safeJson(res3)
            // A per-minute cap carries Retry-After and fits the wait-time line.
            // A daily cap carries no Retry-After and a message that names the
            // reset — show that verbatim so the user stops retrying.
            if (!retryAfter && body.detail) {
              setLlmError(body.detail)
            } else {
              const wait = retryAfter ? `${retryAfter} seconds` : 'a moment'
              setLlmError(`Too many analysis requests. Please wait ${wait} and try again.`)
            }
            onAnalyzeComplete?.()
            return
          }
          if (!res3.ok) throw new Error('LLM assess request failed')
          setLlmData(await safeJson(res3))
          onAnalyzeComplete?.()
        } catch (err) {
          console.error(err)
          if (err.name !== 'AbortError' && abortRef.current === ctrl) {
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
