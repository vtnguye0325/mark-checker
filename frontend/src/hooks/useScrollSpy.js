import { useEffect, useState } from 'react'

// Set the current part in the rail from scroll position. `count` is the number
// of parts on the page; the effect re-runs when it changes, so a part that
// mounts behind a later flag still gets observed. The observer watches each
// `.part-head`, not the section, so the 64px section padding does not advance
// the rail early. The `rootMargin` top inset clears the sticky mobile nav; the
// bottom inset holds the reading line near the top third of the viewport.
export function useScrollSpy(count) {
  const [current, setCurrent] = useState(null)

  useEffect(() => {
    if (!count) {
      setCurrent(null)
      return
    }
    const heads = Array.from(document.querySelectorAll('main.body section.part .part-head'))
    if (heads.length === 0) return

    // Hold every head's state, not just the ones this callback changed. An
    // IntersectionObserver passes only the changed entries, so a scroll back up
    // would otherwise empty the list and freeze the rail on the part below.
    const visible = new Map()
    const idOf = (el) => el.closest('section.part').id

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) visible.set(idOf(entry.target), entry)
        const shown = [...visible.values()]
          .filter((e) => e.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)
        if (shown[0]) setCurrent(idOf(shown[0].target))
      },
      { rootMargin: '-88px 0px -60% 0px', threshold: 0 },
    )
    heads.forEach((h) => observer.observe(h))
    return () => observer.disconnect()
  }, [count])

  return current
}
