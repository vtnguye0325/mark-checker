export default function RecordBar({ email, onSignOut }) {
  return (
    <div className="recordbar">
      <span>Mark Checker · <b>Distinctiveness record</b></span>
      <span className="recordbar-account">
        {email && <span className="recordbar-email">{email}</span>}
        {onSignOut ? (
          <button type="button" className="recordbar-signout" onClick={onSignOut}>
            Sign out
          </button>
        ) : (
          <span>Not legal advice</span>
        )}
      </span>
    </div>
  )
}
