import { useRef, useState } from 'react'
import { EMPTY_FORM } from './constants/formDefaults'
import { useTrademarkPipeline } from './hooks/useTrademarkPipeline'
import { useScrollSpy } from './hooks/useScrollSpy'
import RecordBar from './components/RecordBar'
import RecordPlate from './components/RecordPlate'
import RecordRail from './components/RecordRail'
import MarkForm from './components/MarkForm'
import ProgressBar from './components/ui/ProgressBar'
import PartSpectrum from './components/parts/PartSpectrum'
import PartBasis from './components/parts/PartBasis'
import PartAuthority from './components/parts/PartAuthority'
import PartAction from './components/parts/PartAction'
import PartInput from './components/parts/PartInput'

const TURNSTILE_SITE_KEY = import.meta.env.VITE_TURNSTILE_SITE_KEY || ''

// Build the part index from the four loading and error flags in one place, so the
// rail and the body never disagree. See IMPLEMENTATION_PLAN_D.md 2.1.
function buildParts(state) {
  const { result, explainLoading, explainData, explainError, llmLoading, llmData, llmError } = state
  const spectrumReady = !!result
  const basisPresent = !!explainData
  const basisStatus = explainError
    ? 'Unavailable'
    : explainLoading
      ? 'Loading'
      : explainData
        ? 'Ready'
        : 'Queued'
  const stageThreeStatus = (has) =>
    explainError || llmError
      ? 'Unavailable'
      : llmLoading
        ? 'Loading'
        : has
          ? 'Ready'
          : 'Queued'
  // Base stage-3 presence on the response, not on one optional key. `sources` is
  // typed `dict | None`, so a finished assess can carry `sources: null`.
  const authorityPresent = !!llmData
  const actionPresent = !!llmData
  return [
    { id: 'p1', name: 'Spectrum', no: '01', status: spectrumReady ? 'Ready' : 'Queued', present: spectrumReady },
    { id: 'p2', name: 'Basis', no: '02', status: basisStatus, present: basisPresent || !!explainError },
    { id: 'p3', name: 'Authority', no: '03', status: stageThreeStatus(authorityPresent), present: authorityPresent || !!llmError || !!explainError },
    { id: 'p4', name: 'Action', no: '04', status: stageThreeStatus(actionPresent), present: actionPresent || !!llmError || !!explainError },
    { id: 'p5', name: 'Input', no: '05', status: spectrumReady ? 'Ready' : 'Queued', present: spectrumReady },
  ]
}

export default function App() {
  const [form, setForm] = useState(EMPTY_FORM)
  const [turnstileToken, setTurnstileToken] = useState('')
  const turnstileRef = useRef(null)
  const filedRef = useRef(null)
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
    filedRef.current = null
    setForm(EMPTY_FORM)
    turnstileRef.current?.reset()
    setTurnstileToken('')
    reset()
  }

  const canSubmit =
    form.mark.trim() && form.description.trim() && form.nice_class &&
    (!TURNSTILE_SITE_KEY || turnstileToken)

  const { result, loading } = state
  const hasActivity = loading || !!result

  const accent =
    result?.label === 'distinctive' ? 'record--distinctive'
      : result?.label ? 'record--not'
        : ''

  if (result && !filedRef.current) {
    filedRef.current = new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
  }

  const parts = buildParts(state)
  const currentPart = useScrollSpy(result ? parts.filter((p) => p.present).length : 0)
  const sourceCount = state.llmData?.sources
    ? (state.llmData.sources.tmep?.length || 0) + (state.llmData.sources.ttab?.length || 0)
    : 0
  const meta = {
    filed: filedRef.current,
    nice_class: result?.nice_class ?? null,
    score: Number.isFinite(result?.prob_distinctive) ? result.prob_distinctive.toFixed(2) : null,
    model: result ? 'ModernBERT' : null,
    sources: sourceCount || null,
  }

  return (
    <div className={`record ${accent}`}>
      <div className="accent-rule" />
      <RecordBar />

      {result && (
        <RecordPlate
          result={result}
          llmData={state.llmData}
          llmLoading={state.llmLoading}
          llmError={state.llmError}
          explainError={state.explainError}
        />
      )}

      <div className="doc">
        {hasActivity
          ? <RecordRail meta={meta} parts={parts} current={currentPart} />
          : (
            <aside className="rail">
              <p className="t-small dim">The record opens after you submit a mark.</p>
            </aside>
          )}

        <main className="body">
          {!hasActivity && (
            <MarkForm
              form={form}
              onFieldChange={onFieldChange}
              error={state.error}
              loading={loading}
              onSubmit={handleSubmit}
              canSubmit={canSubmit}
              turnstileRef={turnstileRef}
              onTurnstileToken={setTurnstileToken}
              turnstileSiteKey={TURNSTILE_SITE_KEY}
            />
          )}

          {loading && !result && (
            <ProgressBar
              trackClassName="progress"
              indicatorClassName="progress-ind"
              getValueLabel={() => 'Reading the mark'}
            />
          )}

          {result && (
            <>
              <section className="part" id="p1">
                <PartSpectrum score={result.prob_distinctive} />
              </section>
              <section className="part" id="p2">
                <PartBasis loading={state.explainLoading} data={state.explainData} error={state.explainError} />
              </section>
              <section className="part" id="p3">
                <PartAuthority loading={state.llmLoading} data={state.llmData} error={state.llmError} explainError={state.explainError} />
              </section>
              <section className="part" id="p4">
                <PartAction loading={state.llmLoading} data={state.llmData} error={state.llmError} explainError={state.explainError} />
              </section>
              <section className="part" id="p5">
                <PartInput formattedInput={result.formatted_input} />
              </section>

              <div style={{ paddingTop: '48px' }}>
                <button type="button" className="btn btn--secondary" onClick={handleReset}>
                  Check another name
                </button>
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  )
}
