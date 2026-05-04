"use client"

import { useEffect, useRef, useState } from "react"

interface Props {
  value: number
  duration?: number
  formatter?: (n: number) => string
}

export function AnimatedCounter({
  value,
  duration = 1400,
  formatter = (n) => n.toLocaleString(),
}: Props) {
  const [display, setDisplay] = useState(0)
  const rafRef = useRef<number | null>(null)
  const prevRef = useRef(0)

  useEffect(() => {
    const start = performance.now()
    const from = prevRef.current
    const to = value

    const tick = (now: number) => {
      const progress = Math.min((now - start) / duration, 1)
      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3)
      const current = Math.round(from + (to - from) * eased)
      setDisplay(current)
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(tick)
      } else {
        prevRef.current = to
      }
    }

    if (rafRef.current) cancelAnimationFrame(rafRef.current)
    rafRef.current = requestAnimationFrame(tick)

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
    }
  }, [value, duration])

  return <>{formatter(display)}</>
}
