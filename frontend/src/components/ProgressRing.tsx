import { useEffect, useRef } from "react"
import { animate } from "animejs"
import useReducedMotion from "../hooks/useReducedMotion"

// Anillo de progreso SVG — esquinas cuadradas (strokeLinecap butt en vez de
// round) para calzar con el lenguaje "instrumento de panel" en vez de un
// donut chart genérico.
export default function ProgressRing({
  percent,
  size = 88,
  stroke = 6,
  color = "var(--signal-amber)",
  label,
}: {
  percent: number
  size?: number
  stroke?: number
  color?: string
  label?: string
}) {
  const circleRef = useRef<SVGCircleElement>(null)
  const textRef = useRef<SVGTextElement>(null)
  const radius = (size - stroke) / 2
  const circumference = 2 * Math.PI * radius
  const clamped = Math.max(0, Math.min(100, percent))
  const reduced = useReducedMotion()

  useEffect(() => {
    if (!circleRef.current) return
    const target = circumference * (1 - clamped / 100)

    if (reduced) {
      circleRef.current.style.strokeDashoffset = String(target)
      if (textRef.current) textRef.current.textContent = `${Math.round(clamped)}%`
      return
    }

    const counter = { val: 0 }
    const animation = animate(counter, {
      val: clamped,
      duration: 1200,
      ease: "outExpo",
      onUpdate: () => {
        if (textRef.current) textRef.current.textContent = `${Math.round(counter.val)}%`
      },
    })
    animate(circleRef.current, {
      strokeDashoffset: [circumference, target],
      duration: 1200,
      ease: "outExpo",
    })
    return () => {
      animation.pause()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clamped, circumference, reduced])

  return (
    <div className="flex flex-col items-center gap-1.5" style={{ width: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--surface-hover)"
          strokeWidth={stroke}
        />
        <circle
          ref={circleRef}
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="butt"
          strokeDasharray={circumference}
          strokeDashoffset={circumference}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
        <text
          ref={textRef}
          x="50%"
          y="50%"
          textAnchor="middle"
          dominantBaseline="middle"
          style={{ fill: "var(--text-heading)", fontSize: size * 0.19, fontFamily: "var(--font-mono)", fontWeight: 700 }}
        >
          0%
        </text>
      </svg>
      {label && (
        <span className="text-[11px] uppercase tracking-wider text-center" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
          {label}
        </span>
      )}
    </div>
  )
}
