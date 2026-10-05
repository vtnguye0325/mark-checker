import { NICE_CLASSES } from '../constants/niceClasses'
import TurnstileWidget from './TurnstileWidget'

const DEV_AUTH_BYPASS = import.meta.env.DEV && import.meta.env.VITE_DEV_AUTH_BYPASS === 'true'

export default function MarkForm({
  form,
  onFieldChange,
  error,
  loading,
  onSubmit,
  canSubmit,
  turnstileRef,
  onTurnstileToken,
  turnstileSiteKey,
}) {
  return (
    <form className="ledger" onSubmit={onSubmit} noValidate aria-label="Trademark name check">
      <div className="ledger-row ledger-row--mark">
        <label className="t-label ledger-lbl" htmlFor="mark">Your mark</label>
        <div className="ledger-cell">
          <input
            id="mark"
            className="field-input field-input--mark"
            type="text"
            placeholder="e.g. ZEPHYR"
            value={form.mark}
            onChange={onFieldChange('mark')}
            autoComplete="off"
            spellCheck={false}
            required
          />
        </div>
      </div>

      <div className="ledger-row">
          <label className="t-label ledger-lbl" htmlFor="description">Goods or services</label>
        <div className="ledger-cell">
          <input
            id="description"
            className="field-input"
            type="text"
            placeholder="insulated water bottles"
            value={form.description}
            onChange={onFieldChange('description')}
            required
          />
        </div>
      </div>

      <div className="ledger-row">
        <label className="t-label ledger-lbl" htmlFor="nice_class">NICE class</label>
        <div className="ledger-cell">
          <select
            id="nice_class"
            className="field-input field-input--select mono"
            value={form.nice_class}
            onChange={onFieldChange('nice_class')}
            required
          >
            <option value="">Select a class…</option>
            {NICE_CLASSES.map((c) => (
              <option key={c.value} value={c.value}>{c.label}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="ledger-row">
        <label className="t-label ledger-lbl" htmlFor="translation">
          Translation
          <span className="field-optional">Optional. The English meaning of a foreign-language mark.</span>
        </label>
        <div className="ledger-cell">
          <input
            id="translation"
            className="field-input"
            type="text"
            placeholder="the west wind"
            value={form.translation}
            onChange={onFieldChange('translation')}
          />
        </div>
      </div>

      <div className="ledger-row">
        <label className="t-label ledger-lbl" htmlFor="pseudo_mark">
          Pseudo mark
          <span className="field-optional">Optional. The constituent words of a compound mark.</span>
        </label>
        <div className="ledger-cell">
          <input
            id="pseudo_mark"
            className="field-input"
            type="text"
            placeholder="zephyr line"
            value={form.pseudo_mark}
            onChange={onFieldChange('pseudo_mark')}
          />
        </div>
      </div>

      {turnstileSiteKey && (
        <div className="ledger-row">
          <p className="t-label ledger-lbl">Verification</p>
          <div className="ledger-cell">
            <TurnstileWidget
              ref={turnstileRef}
              siteKey={turnstileSiteKey}
              onToken={onTurnstileToken}
            />
          </div>
        </div>
      )}

      {error && (
        <div className="ledger-error" role="alert">
          <p className="t-label">Could not open the record</p>
          <p>{error}</p>
        </div>
      )}

      <div className="notice">
        <span className="t-label notice-tag">Read this</span>
        <p>
          {DEV_AUTH_BYPASS
            ? 'Development mode uses a local account. This check stays in the local development database.'
            : 'The service keeps a record of each check that you run. Sign in to read that history at any time.'}
        </p>
      </div>

      <div className="ledger-actions">
        <p className="hint">
          {canSubmit
            ? 'The record opens after you submit the mark.'
            : 'Enter the mark, the goods, and the NICE class to open the record.'}
        </p>
        <button type="submit" className="btn btn--wide" disabled={!canSubmit || loading}>
          {loading ? 'Checking…' : 'Check this name'} <span className="btn-arrow" aria-hidden="true">↗</span>
        </button>
      </div>
    </form>
  )
}
