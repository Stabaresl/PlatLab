import { useRef } from "react"
import useReducedMotion from "../hooks/useReducedMotion"

// Glow radial que sigue el mouse dentro de su contenedor (position:relative
// en el padre). Usado en paneles "vivos" (hero, panel de laboratorio activo)
// para dar sensación de HUD reactivo sin animación constante de fondo.
export default function MouseGlow({
  color = "255,176,32",
  size = 480,
  opacity = 0.16,
}: {
  color?: string
  size?: number
  opacity?: number
}) {
  const ref = useRef<HTMLDivElement>(null)
  const reduced = useReducedMotion()

  if (reduced) return null

  return (
    <div
      ref={ref}
      className="absolute inset-0 pointer-events-none transition-opacity duration-300"
      aria-hidden="true"
      onMouseMove={undefined}
      style={{ opacity: 0 }}
      data-glow
    >
      <div
        className="absolute inset-0"
        style={{
          background: `radial-gradient(${size}px circle at var(--mx, 50%) var(--my, 50%), rgba(${color}, ${opacity}), transparent 70%)`,
        }}
      />
    </div>
  )
}

// Handler para colocar en el elemento contenedor (position: relative) que
// envuelve tanto el contenido como <MouseGlow />.
export function trackGlow(e: React.MouseEvent<HTMLElement>) {
  const el = e.currentTarget
  const rect = el.getBoundingClientRect()
  const x = ((e.clientX - rect.left) / rect.width) * 100
  const y = ((e.clientY - rect.top) / rect.height) * 100
  el.style.setProperty("--mx", `${x}%`)
  el.style.setProperty("--my", `${y}%`)
  const glow = el.querySelector("[data-glow]") as HTMLElement | null
  if (glow) glow.style.opacity = "1"
}

export function untrackGlow(e: React.MouseEvent<HTMLElement>) {
  const glow = e.currentTarget.querySelector("[data-glow]") as HTMLElement | null
  if (glow) glow.style.opacity = "0"
}
