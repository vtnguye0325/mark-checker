/**
 * The one place that talks to the backend.
 *
 * Every call goes through `request()`, so the base URL, the cookie mode, the
 * error reading, and the single 401 retry are written once. Each endpoint gets
 * a named function below; no component holds a URL.
 */

// Same origin in production, because nginx reverse-proxies the API paths. Set
// VITE_API_BASE only when the frontend runs on a different origin.
const BASE = import.meta.env.VITE_API_BASE ?? ''

/** A non-2xx response. `status`, `detail`, and `retryAfter` read the same way every time. */
export class ApiError extends Error {
  constructor(message, { status, detail = null, retryAfter = null } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
    this.retryAfter = retryAfter
  }
}

async function readBody(res) {
  const text = await res.text()
  if (!text) return {}
  try {
    return JSON.parse(text)
  } catch {
    return { detail: text }
  }
}

/**
 * Read the error message out of a response body.
 *
 * FastAPI sends `detail` as a string, or as a list of objects for a validation
 * error. slowapi sends `error`, not `detail`. Return null when the body carries
 * no message, so the caller can pick its own wording.
 */
function readDetail(body) {
  const { detail } = body
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    const parts = detail.map((d) => d?.msg).filter(Boolean)
    if (parts.length) return parts.join('; ')
  }
  if (typeof body.error === 'string') return body.error
  return null
}

/**
 * Send one request and return the parsed JSON body.
 *
 * Throws `ApiError` on a non-2xx response. On a 401 the caller may pass
 * `onAuthExpired`; it runs once, and the request repeats once when it resolves
 * truthy. Retry once only, or a backend that answers 401 forever loops.
 * An aborted request throws the browser's AbortError, which keeps its name.
 */
async function request(path, { method = 'GET', body, signal, onAuthExpired } = {}) {
  const opts = { method, credentials: 'include', signal }
  if (body !== undefined) {
    opts.headers = { 'Content-Type': 'application/json' }
    opts.body = JSON.stringify(body)
  }

  let res = await fetch(`${BASE}${path}`, opts)
  if (res.status === 401 && onAuthExpired) {
    const ok = await onAuthExpired()
    if (ok) res = await fetch(`${BASE}${path}`, opts)
  }

  if (!res.ok) {
    const parsed = await readBody(res)
    const detail = readDetail(parsed)
    throw new ApiError(detail || `Request failed (${res.status})`, {
      status: res.status,
      detail,
      retryAfter: res.headers.get('Retry-After'),
    })
  }
  return readBody(res)
}

// ---------------------------------------------------------------------------
// The check pipeline
// ---------------------------------------------------------------------------

export function predict(payload, opts) {
  return request('/ml-predict', { method: 'POST', body: payload, ...opts })
}

export function explain(payload, opts) {
  return request('/llm-explain', { method: 'POST', body: payload, ...opts })
}

export function assess(payload, opts) {
  return request('/llm-assess', { method: 'POST', body: payload, ...opts })
}

// ---------------------------------------------------------------------------
// History
// ---------------------------------------------------------------------------

export function history(limit, opts) {
  return request(`/history?limit=${limit}`, opts)
}

export function historyRecord(id, opts) {
  return request(`/history/${id}`, opts)
}

// ---------------------------------------------------------------------------
// Session
// ---------------------------------------------------------------------------

/** Return the signed-in account, or null when no session exists. */
export async function me(opts) {
  try {
    return await request('/auth/me', opts)
  } catch (err) {
    if (err instanceof ApiError) return null
    throw err
  }
}

export function signInWithGoogle(credential, opts) {
  return request('/auth/google', { method: 'POST', body: { credential }, ...opts })
}

export function signOut(opts) {
  return request('/auth/logout', { method: 'POST', ...opts })
}
