// The account strip. On the landing page it is a paper masthead with the
// brand at the left and the account actions as bordered cells at the right.
// On the record and the history views it is the ink record bar.
export default function RecordBar({
  status,
  email,
  onSignIn,
  onSignOut,
  onToggleHistory,
  showingHistory,
  onToggleMethod,
  showingMethod,
  landing = false,
}) {
  const actions = (
    <>
      <button type="button" className="recordbar-link" onClick={onToggleMethod}>
        {showingMethod ? 'Back to the check' : 'How it works'}
      </button>
      {status === 'signed-in' && (
        <>
          {email && <span className="recordbar-email">{email}</span>}
          <button type="button" className="recordbar-link" onClick={onToggleHistory}>
            {showingHistory ? 'Back to the check' : 'History'}
          </button>
          <button type="button" className="recordbar-link" onClick={onSignOut}>
            Sign out
          </button>
        </>
      )}
      {status === 'signed-out' && (
        <button type="button" className="recordbar-link" onClick={onSignIn}>
          Sign in
        </button>
      )}
    </>
  )

  if (landing) {
    return (
      <header className="masthead">
        <span className="masthead-brand">Mark Checker</span>
        <nav className="masthead-nav" aria-label="Account">{actions}</nav>
      </header>
    )
  }

  return (
    <div className="recordbar">
      <span><b>Trademark Name Checker</b></span>
      <span className="recordbar-account">
        <span>Not legal advice</span>
        {actions}
      </span>
    </div>
  )
}
