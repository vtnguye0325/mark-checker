import { forwardRef, useEffect, useImperativeHandle, useRef } from 'react'

/**
 * Renders a Cloudflare Turnstile widget and exposes a reset() handle.
 *
 * The global window.turnstile is injected by the script tag in index.html.
 * We poll until it's ready rather than relying on a load event because the
 * script is loaded async and may resolve after this component mounts.
 *
 * @param {string}   siteKey  - VITE_TURNSTILE_SITE_KEY (public)
 * @param {Function} onToken  - called with token string on success, '' on error/expiry
 */
const TurnstileWidget = forwardRef(function TurnstileWidget({ siteKey, onToken }, ref) {
  const containerRef = useRef(null)
  const widgetIdRef = useRef(null)
  const onTokenRef = useRef(onToken)

  useEffect(() => { onTokenRef.current = onToken }, [onToken])

  useImperativeHandle(ref, () => ({
    reset() {
      if (widgetIdRef.current != null && window.turnstile) {
        window.turnstile.reset(widgetIdRef.current)
        onTokenRef.current('')
      }
    },
  }))

  useEffect(() => {
    if (!siteKey || !containerRef.current) return

    let intervalId = null

    function render() {
      widgetIdRef.current = window.turnstile.render(containerRef.current, {
        sitekey: siteKey,
        callback: (token) => onTokenRef.current(token),
        'error-callback': () => onTokenRef.current(''),
        'expired-callback': () => onTokenRef.current(''),
      })
    }

    if (window.turnstile) {
      render()
    } else {
      intervalId = setInterval(() => {
        if (window.turnstile) {
          clearInterval(intervalId)
          render()
        }
      }, 100)
    }

    return () => {
      if (intervalId) clearInterval(intervalId)
      if (widgetIdRef.current != null && window.turnstile) {
        window.turnstile.remove(widgetIdRef.current)
        widgetIdRef.current = null
      }
    }
  }, [siteKey])

  if (!siteKey) return null
  return <div ref={containerRef} className="turnstile-widget" />
})

export default TurnstileWidget
