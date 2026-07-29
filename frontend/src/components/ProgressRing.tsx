import { useEffect, useRef } from "react"
import { animate } from "animejs"

// Anillo de progreso SVG animado con anime.js (stroke-dashoffset) — usado
// en los dashboards para reemplazar números planos por algo más visual.
export default function ProgressRing({
  percent,
  size = 88,
  stroke = 8,
  color = "var(--accent-primary)",
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

  useEffect(() => {
    if (!circleRef.current) return
    const target = circumference * (1 - clamped / 100)
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
  }, [clamped, circumference])

  return (
    <div className="flex flex-col items-center gap-1.5" style={{ width: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--bg-surface-hover)"
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
          strokeLinecap="round"
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
          style={{ fill: "var(--text-heading)", fontSize: size * 0.2, fontFamily: "'Fira Code', monospace", fontWeight: 700 }}
        >
          0%
        </text>
      </svg>
      {label && (
        <span className="text-xs text-center" style={{ color: "var(--text-muted)" }}>
          {label}
        </span>
      )}
    </div>
  )
}
