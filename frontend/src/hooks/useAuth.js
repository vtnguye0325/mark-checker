import { useCallback, useEffect, useState } from 'react'

/**
 * Session state for the app.
 *
 * `status` is one of:
 *   - 'loading'    — the initial GET /auth/me has not returned yet. Render
 *                    nothing decisive, or every reload flashes the sign-in screen.
 *   - 'signed-in'  — `user` holds the account.
 *   - 'signed-out' — no session. This is a normal state, not an error.
 *
 * The backend sets an HttpOnly session cookie, which this code cannot read, so
 * the only way to learn whether a session exists is to ask GET /auth/me.
 */
export function useAuth() {
  const [user, setUser] = useState(null)
  const [status, setStatus] = useState('loading')

  useEffect(() => {
    let cancelled = false
    fetch('/auth/me', { credentials: 'include' })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (cancelled) return
        setUser(data)
        setStatus(data ? 'signed-in' : 'signed-out')
      })
      .catch(() => {
        if (cancelled) return
        setStatus('signed-out')
      })
    return () => {
      cancelled = true
    }
  }, [])

  const signIn = useCallback(async (credential) => {
    const res = await fetch('/auth/google', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ credential }),
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Sign-in failed')
    }
    const data = await res.json()
    setUser(data)
    setStatus('signed-in')
    return data
  }, [])

  const signOut = useCallback(async () => {
    try {
      await fetch('/auth/logout', { method: 'POST', credentials: 'include' })
    } finally {
      // Stop GIS from signing the user straight back in on the next visit.
      window.google?.accounts?.id?.disableAutoSelect?.()
      setUser(null)
      setStatus('signed-out')
    }
  }, [])

  // Called when a protected route returns 401 mid-session.
  const sessionExpired = useCallback(() => {
    setUser(null)
    setStatus('signed-out')
  }, [])

  return { user, status, signIn, signOut, sessionExpired }
}
