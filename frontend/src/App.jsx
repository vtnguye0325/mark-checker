import { useState } from 'react'
import { EMPTY_FORM } from './constants/formDefaults'
import { useTrademarkPipeline } from './hooks/useTrademarkPipeline'
import AppHeader from './components/AppHeader'
import MarkForm from './components/MarkForm'
import ResultPanel from './components/ResultPanel'

export default function App() {
  const [form, setForm] = useState(EMPTY_FORM)
  const [showAdvanced, setShowAdvanced] = useState(true)
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
    submit(buildPayload())
  }

  const handleReset = () => {
    setForm(EMPTY_FORM)
    reset()
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
          error={state.error}
          loading={state.loading}
          result={state.result}
          onSubmit={handleSubmit}
          onReset={handleReset}
          canSubmit={canSubmit}
        />

        <ResultPanel
          result={state.result}
          liveMark={form.mark.trim().toUpperCase() || ''}
          loading={state.loading}
          explainLoading={state.explainLoading}
          explainData={state.explainData}
          llmLoading={state.llmLoading}
          llmData={state.llmData}
        />
      </div>
    </div>
  )
}
