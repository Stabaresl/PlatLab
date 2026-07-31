import { useRef, type CSSProperties, type ReactNode, type MouseEvent } from "react"
import useReducedMotion from "../hooks/useReducedMotion"
import MouseGlow, { trackGlow, untrackGlow } from "./MouseGlow"

// Envoltorio "3D" para cards de dashboard: tilt de perspectiva que sigue
// el cursor + el glow radial que ya usa MouseGlow (mismo mecanismo de
// variables CSS --mx/--my, solo se le agrega la rotación). Inspirado en
// el patrón de tarjeta holográfica de 21st.dev, adaptado a nuestros
// tokens (--signal-*) en vez de colores fijos — reemplaza al cubo 3D
// decorativo del ejemplo por una técnica aplicable a cards con datos
// reales (números, estados), no a un objeto sin información.
export default function TiltCard({
  children,
  glowColor = "56,214,245",
  glowSize = 420,
  glowOpacity = 0.14,
  intensity = 7,
  className = "",
  style = {},
}: {
  children: ReactNode
  glowColor?: string
  glowSize?: number
  glowOpacity?: number
  intensity?: number
  className?: string
  style?: CSSProperties
}) {
  const ref = useRef<HTMLDivElement>(null)
  const reduced = useReducedMotion()

  const handleMove = (e: MouseEvent<HTMLDivElement>) => {
    trackGlow(e)
    if (reduced || !ref.current) return
    const rect = e.currentTarget.getBoundingClientRect()
    const px = (e.clientX - rect.left) / rect.width
    const py = (e.clientY - rect.top) / rect.height
    const rx = (0.5 - py) * intensity
    const ry = (px - 0.5) * intensity
    ref.current.style.transform = `perspective(900px) rotateX(${rx}deg) rotateY(${ry}deg)`
  }

  const handleLeave = (e: MouseEvent<HTMLDivElement>) => {
    untrackGlow(e)
    if (ref.current) ref.current.style.transform = "perspective(900px) rotateX(0deg) rotateY(0deg)"
  }

  return (
    <div
      ref={ref}
      onMouseMove={handleMove}
      onMouseLeave={handleLeave}
      className={`relative transition-transform duration-200 ease-out will-change-transform ${className}`}
      style={style}
    >
      {!reduced && <MouseGlow color={glowColor} size={glowSize} opacity={glowOpacity} />}
      <div className="relative z-10 h-full">{children}</div>
    </div>
  )
}
