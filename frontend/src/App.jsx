import { useState, useRef } from 'react'
import { EMPTY_FORM } from './constants/formDefaults'
import AppHeader from './components/AppHeader'
import MarkForm from './components/MarkForm'
import ResultPanel from './components/ResultPanel'

export default function App() {
  const [form, setForm] = useState(EMPTY_FORM)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [showAdvanced, setShowAdvanced] = useState(true)
  const [explainLoading, setExplainLoading] = useState(false)
  const [explainData, setExplainData] = useState(null)
  const [llmLoading, setLlmLoading] = useState(false)
  const [llmData, setLlmData] = useState(null)
  const abortRef = useRef(null)

  const onFieldChange = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const buildPayload = () => ({
    mark: form.mark.trim(),
    description: form.description.trim(),
    nice_class: parseInt(form.nice_class, 10),
    ...(form.translation.trim() && { translation: form.translation.trim() }),
    ...(form.pseudo_mark.trim() && { pseudo_mark: form.pseudo_mark.trim() }),
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
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
        body: JSON.stringify(buildPayload()),
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
      const predictResult = { ...data, mark: form.mark.trim(), nice_class: parseInt(form.nice_class, 10) }
      setResult(predictResult)
      const explainResult = await handleExplain()
      if (explainResult) handleAnalyze(predictResult, explainResult)
    } catch (err) {
      if (err.name !== 'AbortError') setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleExplain = async () => {
    setExplainLoading(true)
    setExplainData(null)
    try {
      const res = await fetch('/explain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(buildPayload()),
      })
      if (!res.ok) throw new Error('Explain request failed')
      const data = await res.json()
      setExplainData(data)
      return data
    } catch (err) {
      console.error(err)
      return null
    } finally {
      setExplainLoading(false)
    }
  }

  const handleAnalyze = async (predictResult, explainResult) => {
    setLlmLoading(true)
    setLlmData(null)
    try {
      const payload = {
        mark: predictResult.mark,
        description: buildPayload().description,
        nice_class: predictResult.nice_class,
        label: predictResult.label,
        prob_distinctive: predictResult.prob_distinctive,
        attributions: explainResult.attributions,
      }
      const res = await fetch('/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      if (!res.ok) throw new Error('Analyze request failed')
      const data = await res.json()
      setLlmData(data)
    } catch (err) {
      console.error(err)
    } finally {
      setLlmLoading(false)
    }
  }

  const handleReset = () => {
    setForm(EMPTY_FORM)
    setResult(null)
    setError(null)
    setExplainData(null)
    setLlmData(null)
  }

  const canSubmit = form.mark.trim() && form.description.trim() && form.nice_class

  return (
    <div className="app">
      <AppHeader />

      <div className="workspace">
        <MarkForm
          form={form}
          onFieldChange={onFieldChange}
          showAdvanced={showAdvanced}
          onToggleAdvanced={() => setShowAdvanced(o => !o)}
          error={error}
          loading={loading}
          result={result}
          onSubmit={handleSubmit}
          onReset={handleReset}
          canSubmit={canSubmit}
        />

        <ResultPanel
          result={result}
          liveMark={form.mark.trim().toUpperCase() || ''}
          loading={loading}
          explainLoading={explainLoading}
          explainData={explainData}
          llmLoading={llmLoading}
          llmData={llmData}
        />
      </div>
    </div>
  )
}
