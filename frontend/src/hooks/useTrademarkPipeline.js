import { useState, useRef } from 'react'

export function useTrademarkPipeline() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [explainLoading, setExplainLoading] = useState(false)
  const [explainData, setExplainData] = useState(null)
  const [llmLoading, setLlmLoading] = useState(false)
  const [llmData, setLlmData] = useState(null)
  const abortRef = useRef(null)

  async function submit(payload, turnstileToken = '', onAnalyzeComplete = null) {
    if (abortRef.current) abortRef.current.abort()
    const ctrl = new AbortController()
    abortRef.current = ctrl

    setLoading(true)
    setError(null)
    setResult(null)
    setExplainData(null)
    setLlmData(null)

    try {
      const res = await fetch('/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: ctrl.signal,
      })
      if (!res.ok) {
        const err = await res.json()
        const msg = Array.isArray(err.detail)
          ? err.detail.map((d) => d.msg).join('; ')
          : (err.detail || 'Request failed')
        throw new Error(msg)
      }
      const data = await res.json()
      const predictResult = { ...data, mark: payload.mark, nice_class: payload.nice_class }
      setResult(predictResult)

      setExplainLoading(true)
      let explainResult = null
      try {
        const res2 = await fetch('/explain', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        })
        if (!res2.ok) throw new Error('Explain request failed')
        explainResult = await res2.json()
        setExplainData(explainResult)
      } catch (err) {
        console.error(err)
      } finally {
        setExplainLoading(false)
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
          }
          const res3 = await fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(analyzePayload),
          })
          if (!res3.ok) throw new Error('Analyze request failed')
          setLlmData(await res3.json())
          onAnalyzeComplete?.()
        } catch (err) {
          console.error(err)
          onAnalyzeComplete?.()
        } finally {
          setLlmLoading(false)
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function reset() {
    setResult(null)
    setError(null)
    setExplainData(null)
    setLlmData(null)
  }

  return {
    submit,
    reset,
    state: { loading, result, error, explainLoading, explainData, llmLoading, llmData },
  }
}
