import { useEffect, useRef } from "react"
import { animate } from "animejs"

// Contador animado (anime.js tween sobre un objeto plano, no sobre el DOM
// directamente) — se usa en la franja "En números" de la landing.
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

  useEffect(() => {
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
  }, [value, suffix, delay])

  return (
    <div className="flex flex-col items-center gap-1 text-center">
      <span
        ref={ref}
        className="text-3xl sm:text-4xl font-bold"
        style={{ color: "var(--accent-primary)", fontFamily: "'Fira Code', monospace" }}
      >
        0{suffix}
      </span>
      <span className="text-xs sm:text-sm" style={{ color: "var(--text-muted)" }}>
        {label}
      </span>
    </div>
  )
}
