import { NICE_CLASSES } from '../constants/niceClasses'
import TurnstileWidget from './TurnstileWidget'

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
    <form onSubmit={onSubmit} noValidate>
      <div className="subject">
        <label className="t-label dim" htmlFor="mark">Subject of this record</label>
        <input
          id="mark"
          className="field-input field-input--mark"
          type="text"
          placeholder="ENTER A MARK"
          value={form.mark}
          onChange={onFieldChange('mark')}
          autoComplete="off"
          spellCheck={false}
          required
        />
      </div>

      <label className="field" htmlFor="description">
        <span className="t-label">Goods &amp; services</span>
        <input
          id="description"
          className="field-input"
          type="text"
          placeholder="insulated water bottles"
          value={form.description}
          onChange={onFieldChange('description')}
          required
        />
      </label>

      <label className="field" htmlFor="nice_class">
        <span className="t-label">NICE class</span>
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
      </label>

      <label className="field" htmlFor="translation">
        <span className="t-label">
          Translation{' '}
          <span className="field-optional">— optional, the English meaning of a foreign-language mark</span>
        </span>
        <input
          id="translation"
          className="field-input"
          type="text"
          placeholder="e.g. the west wind"
          value={form.translation}
          onChange={onFieldChange('translation')}
        />
      </label>

      <label className="field" htmlFor="pseudo_mark">
        <span className="t-label">
          Pseudo mark{' '}
          <span className="field-optional">— optional, the constituent words of a compound mark</span>
        </span>
        <input
          id="pseudo_mark"
          className="field-input"
          type="text"
          placeholder="e.g. zephyr line"
          value={form.pseudo_mark}
          onChange={onFieldChange('pseudo_mark')}
        />
      </label>

      {error && (
        <div className="error-block" role="alert">
          <p className="t-label">Could not open the record</p>
          <p>{error}</p>
        </div>
      )}

      {turnstileSiteKey && (
        <div className="turnstile-block">
          <p className="t-label dim" style={{ marginBottom: '12px' }}>Verification</p>
          <TurnstileWidget
            ref={turnstileRef}
            siteKey={turnstileSiteKey}
            onToken={onTurnstileToken}
          />
        </div>
      )}

      <div className="form-actions">
        <button type="submit" className="btn" disabled={!canSubmit || loading}>
          {loading ? 'Opening…' : 'Open record'}
        </button>
        {!canSubmit && (
          <p className="t-small dim">
            Enter the mark, the goods, and the NICE class to open the record.
          </p>
        )}
      </div>
    </form>
  )
}
