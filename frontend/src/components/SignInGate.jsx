import { useEffect, useRef, useState } from 'react'

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || ''

/**
 * The blocked state for anonymous visitors. Renders the Google button through
 * google.accounts.id, in the same poll-until-ready pattern that
 * TurnstileWidget.jsx uses for window.turnstile — the GIS script in index.html
 * is async and may resolve after this component mounts.
 *
 * @param {(credential: string) => Promise<unknown>} onCredential
 */
export default function SignInGate({ onCredential }) {
  const buttonRef = useRef(null)
  const onCredentialRef = useRef(onCredential)
  const [error, setError] = useState(null)

  useEffect(() => {
    onCredentialRef.current = onCredential
  }, [onCredential])

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID || !buttonRef.current) return

    let intervalId = null

    function render() {
      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: (response) => {
          Promise.resolve(onCredentialRef.current(response.credential)).catch((err) => {
            setError(err.message || 'Sign-in failed')
          })
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
          render()
        }
      }, 100)
    }

    return () => {
      if (intervalId) clearInterval(intervalId)
    }
  }, [])

  return (
    <div className="record">
      <div className="accent-rule" />
      <div className="recordbar">
        <span>
          Mark Checker · <b>Distinctiveness record</b>
        </span>
        <span>Not legal advice</span>
      </div>
      <div className="signin-gate">
        <h1 className="signin-title">Sign in to check a mark</h1>
        <p className="t-small dim signin-copy">
          Mark Checker keeps a record of every check you run. Sign in with Google to start.
        </p>
        {!GOOGLE_CLIENT_ID && (
          <p className="error-block">Sign-in is not configured. Set VITE_GOOGLE_CLIENT_ID.</p>
        )}
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
