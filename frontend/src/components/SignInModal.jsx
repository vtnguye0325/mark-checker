import { useEffect, useRef, useState } from 'react'

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''
const POLL_TIMEOUT_MS = 8000

/**
 * Sign-in modal rendered over the form. The form stays mounted underneath, so
 * the values the visitor typed survive the sign-in.
 *
 * Renders the Google button through google.accounts.id, in the same
 * poll-until-ready pattern that TurnstileWidget.jsx uses for window.turnstile —
 * the GIS script in index.html is async and may resolve after this mounts.
 *
 * @param {(credential: string) => Promise<unknown>} onCredential  posts to /auth/google
 * @param {() => void} onSignedIn  called after onCredential resolves (runs the pending check in Step 10)
 * @param {() => void} onClose     called on cancel; the form keeps its values and no check runs
 */
export default function SignInModal({ onCredential, onSignedIn, onClose }) {
  const buttonRef = useRef(null)
  const onCredentialRef = useRef(onCredential)
  const onSignedInRef = useRef(onSignedIn)
  const [error, setError] = useState(null)

  useEffect(() => {
    onCredentialRef.current = onCredential
    onSignedInRef.current = onSignedIn
  })

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) {
      setError('Sign-in is not configured. Set VITE_GOOGLE_CLIENT_ID.')
      return
    }
    if (!buttonRef.current) return

    let intervalId = null
    let timeoutId = null

    function render() {
      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: (response) => {
          setError(null)
          Promise.resolve(onCredentialRef.current(response.credential))
            .then(() => onSignedInRef.current?.())
            .catch((err) => setError(err.message || 'Sign-in failed'))
        },
      })
      window.google.accounts.id.renderButton(buttonRef.current, {
        theme: 'outline',
        size: 'large',
        text: 'signin_with',
      })
    }

    if (window.google?.accounts?.id) {
      render()
    } else {
      intervalId = setInterval(() => {
        if (window.google?.accounts?.id) {
          clearInterval(intervalId)
          clearTimeout(timeoutId)
          render()
        }
      }, 100)
      // Google blocked in the browser -> button never renders. Show a plain
      // line after the timeout, not an empty box.
      timeoutId = setTimeout(() => {
        clearInterval(intervalId)
        setError('Cannot load Google sign-in. Check that accounts.google.com is reachable.')
      }, POLL_TIMEOUT_MS)
    }

    return () => {
      if (intervalId) clearInterval(intervalId)
      if (timeoutId) clearTimeout(timeoutId)
    }
  }, [])

  return (
    <div className="modal-scrim" onClick={onClose}>
      <div
        className="modal-card"
        role="dialog"
        aria-modal="true"
        aria-label="Sign in"
        onClick={(e) => e.stopPropagation()}
      >
        <button type="button" className="modal-close" onClick={onClose} aria-label="Close">
          ×
        </button>
        <h2 className="modal-title">Sign in to run the check</h2>
        <p className="t-small dim modal-copy">
          Mark Checker keeps a record of every check you run. Your form values stay as they are.
        </p>
        <div ref={buttonRef} className="signin-button" />
        {error && (
          <div className="error-block">
            <p className="t-label">Sign-in failed</p>
            <p>{error}</p>
          </div>
        )}
      </div>
    </div>
  )
}
