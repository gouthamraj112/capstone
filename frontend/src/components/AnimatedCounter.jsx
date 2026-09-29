import { useEffect, useRef, useState } from 'react'

/**
 * Animated number counter that smoothly counts up from 0 to the target value.
 */
export default function AnimatedCounter({ value, duration = 1200, decimals = 2 }) {
  const [displayed, setDisplayed] = useState(0)
  const startRef = useRef(null)
  const rafRef = useRef(null)
  const prevValue = useRef(0)

  useEffect(() => {
    const numVal = Number(value)
    if (isNaN(numVal)) return

    const from = prevValue.current
    const to = numVal
    prevValue.current = to
    startRef.current = null

    if (rafRef.current) cancelAnimationFrame(rafRef.current)

    function animate(timestamp) {
      if (!startRef.current) startRef.current = timestamp
      const elapsed = timestamp - startRef.current
      const progress = Math.min(elapsed / duration, 1)

      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3)
      const current = from + (to - from) * eased

      setDisplayed(current)

      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate)
      }
    }

    rafRef.current = requestAnimationFrame(animate)
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current) }
  }, [value, duration])

  const formatted = Number(displayed).toLocaleString(undefined, {
    maximumFractionDigits: decimals,
    minimumFractionDigits: 0
  })

  return <>{formatted}</>
}
