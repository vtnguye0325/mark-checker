import { NICE_CLASSES } from '../constants/niceClasses'

export default function MarkForm({
  form,
  onFieldChange,
  showAdvanced,
  onToggleAdvanced,
  error,
  loading,
  result,
  onSubmit,
  onReset,
  canSubmit,
}) {
  return (
    <div className="form-panel">
      <div className="panel-label">TRADEMARK INFORMATION</div>

      <form onSubmit={onSubmit} noValidate>
        <div className="field-group">
          <label className="field-label" htmlFor="mark">NAME OF THE TRADEMARK</label>
          <input
            id="mark"
            className="field-input field-input--mark"
            type="text"
            placeholder="e.g. APPLE"
            value={form.mark}
            onChange={onFieldChange('mark')}
            autoComplete="off"
            spellCheck={false}
          />
        </div>

        <div className="field-group">
          <label className="field-label" htmlFor="description">Goods & Services DESCRIPTION</label>
          <textarea
            id="description"
            className="field-input field-input--textarea"
            placeholder="Describe the goods or services covered by the mark…"
            value={form.description}
            onChange={onFieldChange('description')}
            rows={4}
          />
        </div>

        <div className="field-group">
          <label className="field-label" htmlFor="nice_class">NICE Classification</label>
          <div className="select-wrapper">
            <select
              id="nice_class"
              className="field-input field-input--select"
              value={form.nice_class}
              onChange={onFieldChange('nice_class')}
            >
              <option value="">Select a class…</option>
              {NICE_CLASSES.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
            <span className="select-arrow">⌄</span>
          </div>
        </div>

        <button
          type="button"
          className="advanced-toggle"
          onClick={onToggleAdvanced}
        >
          {showAdvanced ? '▲' : '▶'} Advanced fields
        </button>

        {showAdvanced && (
          <div className="advanced-fields">
            <div className="field-group">
              <label className="field-label" htmlFor="translation">
                Translation
                <span className="field-hint">English meaning of a foreign-language mark</span>
              </label>
              <input
                id="translation"
                className="field-input"
                type="text"
                placeholder="e.g. the apple"
                value={form.translation}
                onChange={onFieldChange('translation')}
              />
            </div>

            <div className="field-group">
              <label className="field-label" htmlFor="pseudo_mark">
                Pseudo Mark
                <span className="field-hint">Constituent words of a compound mark</span>
              </label>
              <input
                id="pseudo_mark"
                className="field-input"
                type="text"
                placeholder="e.g. soft wear"
                value={form.pseudo_mark}
                onChange={onFieldChange('pseudo_mark')}
              />
            </div>
          </div>
        )}

        {error && <div className="error-banner">{error}</div>}

        <div className="form-actions">
          <button
            type="submit"
            className="btn-analyze"
            disabled={!canSubmit || loading}
          >
            {loading ? (
              <span className="btn-spinner" />
            ) : (
              <>Analyze <span className="btn-arrow">→</span></>
            )}
          </button>
          {result && (
            <button type="button" className="btn-reset" onClick={onReset}>
              Reset
            </button>
          )}
        </div>
      </form>
    </div>
  )
}
