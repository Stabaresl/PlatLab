import { useEffect, useRef } from "react"
import { animate } from "animejs"
import useReducedMotion from "../hooks/useReducedMotion"

export default function CountUpStat({
  value,
  suffix = "",
  label,
  delay = 0,
}: {
  value: number
  suffix?: string
  label: string
  delay?: number
}) {
  const ref = useRef<HTMLSpanElement>(null)
  const reduced = useReducedMotion()

  useEffect(() => {
    if (!ref.current) return
    if (reduced) {
      ref.current.textContent = `${value}${suffix}`
      return
    }
    const counter = { val: 0 }
    const animation = animate(counter, {
      val: value,
      duration: 1400,
      delay,
      ease: "outExpo",
      onUpdate: () => {
        if (ref.current) ref.current.textContent = `${Math.round(counter.val)}${suffix}`
      },
    })
    return () => {
      animation.pause()
    }
  }, [value, suffix, delay, reduced])

  return (
    <div className="flex flex-col items-center gap-1 text-center">
      <span
        ref={ref}
        className="text-3xl sm:text-4xl font-bold text-display"
        style={{ color: "var(--signal-amber)" }}
      >
        0{suffix}
      </span>
      <span className="text-[11px] sm:text-xs uppercase tracking-wider" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
        {label}
      </span>
    </div>
  )
}
