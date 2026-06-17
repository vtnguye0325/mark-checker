import { useRef, useState } from 'react'
import { EMPTY_FORM } from './constants/formDefaults'
import { useTrademarkPipeline } from './hooks/useTrademarkPipeline'
import AppHeader from './components/AppHeader'
import MarkForm from './components/MarkForm'
import ResultPanel from './components/ResultPanel'

const TURNSTILE_SITE_KEY = import.meta.env.VITE_TURNSTILE_SITE_KEY || ''

export default function App() {
  const [form, setForm] = useState(EMPTY_FORM)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [turnstileToken, setTurnstileToken] = useState('')
  const turnstileRef = useRef(null)
  const { submit, reset, state } = useTrademarkPipeline()

  const onFieldChange = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const buildPayload = () => ({
    mark: form.mark.trim(),
    description: form.description.trim(),
    nice_class: parseInt(form.nice_class, 10),
    ...(form.translation.trim() && { translation: form.translation.trim() }),
    ...(form.pseudo_mark.trim() && { pseudo_mark: form.pseudo_mark.trim() }),
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    submit(buildPayload(), turnstileToken, () => {
      turnstileRef.current?.reset()
      setTurnstileToken('')
    })
  }

  const handleReset = () => {
    setForm(EMPTY_FORM)
    turnstileRef.current?.reset()
    setTurnstileToken('')
    reset()
  }

  const canSubmit =
    form.mark.trim() && form.description.trim() && form.nice_class &&
    (!TURNSTILE_SITE_KEY || turnstileToken)
  const hasActivity = state.loading || !!state.result

  return (
    <div className="app">
      <AppHeader />
      <main className={`main${hasActivity ? '' : ' main--empty'}`}>
        <div className="input-area">
          <MarkForm
            form={form}
            onFieldChange={onFieldChange}
            showAdvanced={showAdvanced}
            onToggleAdvanced={() => setShowAdvanced(o => !o)}
            error={state.error}
            loading={state.loading}
            result={state.result}
            onSubmit={handleSubmit}
            onReset={handleReset}
            canSubmit={canSubmit}
            turnstileRef={turnstileRef}
            onTurnstileToken={setTurnstileToken}
            turnstileSiteKey={TURNSTILE_SITE_KEY}
          />
        </div>

        {hasActivity && (
          <>
            <div className="result-divider">
              <div className="divider-line" />
              <span className="divider-label">Analysis Result</span>
              <div className="divider-line" />
            </div>
            <ResultPanel
              result={state.result}
              liveMark={form.mark.trim().toUpperCase() || ''}
              loading={state.loading}
              explainLoading={state.explainLoading}
              explainData={state.explainData}
              llmLoading={state.llmLoading}
              llmData={state.llmData}
              llmError={state.llmError}
            />
          </>
        )}
      </main>
    </div>
  )
}
