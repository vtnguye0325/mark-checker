import { useCallback, useEffect, useState } from 'react'
import * as api from '../lib/api'

const DEV_AUTH_BYPASS = import.meta.env.DEV && import.meta.env.VITE_DEV_AUTH_BYPASS === 'true'

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
    if (DEV_AUTH_BYPASS) {
      setUser({ id: 'local-development-user', email: 'dev@localhost', name: 'Local developer' })
      setStatus('signed-in')
      return
    }

    let cancelled = false
    api
      .me()
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
    let data
    try {
      data = await api.signInWithGoogle(credential)
    } catch (err) {
      throw new Error(err.detail || 'Sign-in failed')
    }
    setUser(data)
    setStatus('signed-in')
    return data
  }, [])

  const signOut = useCallback(async () => {
    if (DEV_AUTH_BYPASS) return
    try {
      await api.signOut()
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
