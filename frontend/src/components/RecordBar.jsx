export default function RecordBar({ status, email, onSignIn, onSignOut }) {
  return (
    <div className="recordbar">
      <span><b>Trademark Name Checker</b></span>
      <span className="recordbar-account">
        <span>Not legal advice</span>
        {status === 'signed-in' && (
          <>
            {email && <span className="recordbar-email">{email}</span>}
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
      </span>
    </div>
  )
}
