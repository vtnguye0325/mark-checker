import { useEffect, useRef, useState } from 'react'
import { EMPTY_FORM } from './constants/formDefaults'
import { useTrademarkPipeline } from './hooks/useTrademarkPipeline'
import { useScrollSpy } from './hooks/useScrollSpy'
import { useAuth } from './hooks/useAuth'
import SignInModal from './components/SignInModal'
import RecordBar from './components/RecordBar'
import HistoryPanel from './components/HistoryPanel'
import RecordPlate from './components/RecordPlate'
import RecordRail from './components/RecordRail'
import RecordScale from './components/RecordScale'
import MarkForm from './components/MarkForm'
import Marquee from './components/Marquee'
import HowItWorks from './components/HowItWorks'
import MethodPage from './components/MethodPage'
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
  // The reader order is the answer first, then the evidence behind it. The
  // pipeline still runs the basis step before the analysis, so part 04 can fill
  // before parts 02 and 03. Each part states its own state, so that is safe.
  return [
    { id: 'p1', name: 'Spectrum', no: '01', status: spectrumReady ? 'Ready' : 'Queued', present: spectrumReady },
    { id: 'p2', name: 'Reading', no: '02', status: stageThreeStatus(actionPresent), present: actionPresent || !!llmError || !!explainError },
    { id: 'p3', name: 'Sources', no: '03', status: stageThreeStatus(authorityPresent), present: authorityPresent || !!llmError || !!explainError },
    { id: 'p4', name: 'Why', no: '04', status: basisStatus, present: basisPresent || !!explainError },
    { id: 'p5', name: 'Submission', no: '05', status: spectrumReady ? 'Ready' : 'Queued', present: spectrumReady },
  ]
}

export default function App() {
  const { user, status, signIn, signOut, sessionExpired } = useAuth()
  const [signInOpen, setSignInOpen] = useState(false)
  // 'check' is the form and the live result; 'history' is the stored records;
  // 'method' is the long explainer behind the landing button.
  // Only a signed-in user reaches 'history', so drop back to 'check' on sign-out.
  const [view, setView] = useState('check')
  const [form, setForm] = useState(EMPTY_FORM)
  const [turnstileToken, setTurnstileToken] = useState('')
  const turnstileRef = useRef(null)
  const filedRef = useRef(null)
  // A check the visitor started before signing in. Held here, not in form state,
  // because the form unmounts once the pipeline runs.
  const pendingPayloadRef = useRef(null)
  // Resolver for an onAuthExpired promise while the pipeline waits on a re-sign-in.
  const authResolverRef = useRef(null)
  const { submit, reset, state } = useTrademarkPipeline()

  const onFieldChange = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const buildPayload = () => ({
    mark: form.mark.trim(),
    description: form.description.trim(),
    nice_class: parseInt(form.nice_class, 10),
    ...(form.translation.trim() && { translation: form.translation.trim() }),
    ...(form.pseudo_mark.trim() && { pseudo_mark: form.pseudo_mark.trim() }),
  })

  const runSubmit = (payload) => {
    submit(payload, turnstileToken, {
      onAnalyzeComplete: () => {
        turnstileRef.current?.reset()
        setTurnstileToken('')
      },
      // The pipeline hit a 401. Clear the user, open the modal, and resolve
      // true once the sign-in returns so the stage retries.
      onAuthExpired: () =>
        new Promise((resolve) => {
          sessionExpired()
          authResolverRef.current = resolve
          setSignInOpen(true)
        }),
    })
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    const payload = buildPayload()
    // Prompt for the sign-in at the check button, not at page load. Keep the
    // typed values and run the check from the modal callback.
    if (status !== 'signed-in') {
      pendingPayloadRef.current = payload
      setSignInOpen(true)
      return
    }
    runSubmit(payload)
  }

  const handleSignedIn = () => {
    setSignInOpen(false)
    const resolve = authResolverRef.current
    if (resolve) {
      authResolverRef.current = null
      resolve(true)
      return
    }
    const payload = pendingPayloadRef.current
    if (payload) {
      pendingPayloadRef.current = null
      runSubmit(payload)
    }
  }

  // A check clicked while GET /auth/me was still in flight. Once the status
  // resolves to signed-in, run the held payload instead of dropping it. The ref
  // is cleared first, so this and handleSignedIn cannot both run it.
  useEffect(() => {
    if (status !== 'signed-in') return
    const payload = pendingPayloadRef.current
    if (!payload) return
    pendingPayloadRef.current = null
    setSignInOpen(false)
    runSubmit(payload)
  })

  // A view change swaps the whole page. Start the new view at the top, or the
  // reader lands in the middle of it.
  useEffect(() => { window.scrollTo(0, 0) }, [view])

  // The history view needs a session. Drop back to the check when the session
  // ends, so a signed-out user never sees a dead panel.
  useEffect(() => {
    if (status === 'signed-out' && view === 'history') setView('check')
  }, [status, view])

  const handleSignInClose = () => {
    setSignInOpen(false)
    pendingPayloadRef.current = null
    const resolve = authResolverRef.current
    if (resolve) {
      authResolverRef.current = null
      resolve(false)
    }
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

  // The modal opens only on an explicit action (the check button, a 401, or the
  // RecordBar link), never automatically, so there is no reload flash to guard
  // against. Do not show it once the user is signed in.
  const canOpenSignIn = status !== 'signed-in'

  // The landing state is the specimen page: masthead, headline, marquee, and
  // the ledger form. The record state adds the accent rule, the ink record bar,
  // the plate, and the rail. See docs/DESIGN_PRINCIPLES.md 9.
  const landing = view === 'check' && !hasActivity

  return (
    <div className={`record ${accent}`}>
      {!landing && view !== 'method' && <div className="accent-rule" />}
      <RecordBar
        landing={landing}
        status={status}
        email={user?.email}
        onSignIn={() => setSignInOpen(true)}
        onSignOut={signOut}
        showingHistory={view === 'history'}
        onToggleHistory={() => setView((v) => (v === 'history' ? 'check' : 'history'))}
        showingMethod={view === 'method'}
        onToggleMethod={() => setView((v) => (v === 'method' ? 'check' : 'method'))}
      />

      {signInOpen && canOpenSignIn && (
        <SignInModal
          onCredential={signIn}
          onSignedIn={handleSignedIn}
          onClose={handleSignInClose}
        />
      )}

      {view === 'history' && <HistoryPanel onSessionExpired={sessionExpired} />}

      {view === 'method' && (
        <>
          <MethodPage onBack={() => setView('check')} />
          <footer className="foot">
            <span>Mark Checker</span>
            <span>ModernBERT classifier · TMEP + TTAB retrieval</span>
            <span>Probability, never certainty.</span>
          </footer>
        </>
      )}

      {landing && (
        <>
          <section className="head">
            <h1 className="headline"><span className="headline-lead">Is your</span>trademark<em>registrable?</em></h1>
            <div className="deck">
              <span className="stamp">First read. Not legal advice</span>
              <p>
                Our agent reads your trademark name and grades its distinctiveness on the Abercrombie
                spectrum, from <b>generic</b> to <b>distinctive</b>, with the reason for the
                grade. The more distinctive the name, the better it registers. Fill the sheet
                to start.
              </p>
            </div>
          </section>
          <Marquee />
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
          <HowItWorks onOpenMethod={() => setView('method')} />
          <footer className="foot">
            <span>Mark Checker</span>
            <span>ModernBERT classifier · TMEP + TTAB retrieval</span>
          </footer>
        </>
      )}

      {view === 'check' && result && (
        <RecordPlate
          result={result}
          llmData={state.llmData}
          llmLoading={state.llmLoading}
          llmError={state.llmError}
          explainError={state.explainError}
        />
      )}
      {view === 'check' && result && <RecordScale score={result.prob_distinctive} />}

      {view === 'check' && hasActivity && (
      <div className="doc">
        <RecordRail meta={meta} parts={parts} current={currentPart} />

        <main className="body">
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
                <PartAction loading={state.llmLoading} data={state.llmData} error={state.llmError} explainError={state.explainError} />
              </section>
              <section className="part" id="p3">
                <PartAuthority loading={state.llmLoading} data={state.llmData} error={state.llmError} explainError={state.explainError} />
              </section>
              <section className="part" id="p4">
                <PartBasis loading={state.explainLoading} data={state.explainData} error={state.explainError} />
              </section>
              <section className="part" id="p5">
                <PartInput formattedInput={result.formatted_input} />
              </section>

              <div className="close">
                <p>One check at a time. A new record clears this one from the screen, not from your history.</p>
                <button type="button" className="btn btn--wide" onClick={handleReset}>
                  Check another name <span className="btn-arrow" aria-hidden="true">→</span>
                </button>
              </div>
            </>
          )}
        </main>
      </div>
      )}

      {view === 'check' && result && (
        <footer className="foot">
          <span>Mark Checker</span>
          <span>ModernBERT classifier · TMEP + TTAB retrieval</span>
          <span>Probability, never certainty.</span>
        </footer>
      )}
    </div>
  )
}
