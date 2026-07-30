import type { ReactNode } from "react"

// Marco de 4 esquinas tipo "retícula de mira" — decora paneles clave (hero,
// card de laboratorio activo, panel de examen) sin depender de border-radius.
// Puramente decorativo (aria-hidden), no compite con el foco real del teclado.
export default function ReticleFrame({
  children,
  color = "var(--signal-amber)",
  size = 16,
  thickness = 2,
  className = "",
}: {
  children?: ReactNode
  color?: string
  size?: number
  thickness?: number
  className?: string
}) {
  const corner = (pos: "tl" | "tr" | "bl" | "br") => {
    const vertical = pos[0] === "t" ? "top" : "bottom"
    const horizontal = pos[1] === "l" ? "left" : "right"
    return (
      <span
        key={pos}
        aria-hidden="true"
        className="absolute pointer-events-none"
        style={{
          width: size,
          height: size,
          [vertical]: -thickness / 2,
          [horizontal]: -thickness / 2,
          borderTop: vertical === "top" ? `${thickness}px solid ${color}` : undefined,
          borderBottom: vertical === "bottom" ? `${thickness}px solid ${color}` : undefined,
          borderLeft: horizontal === "left" ? `${thickness}px solid ${color}` : undefined,
          borderRight: horizontal === "right" ? `${thickness}px solid ${color}` : undefined,
        }}
      />
    )
  }

  return (
    <div className={`relative ${className}`}>
      {corner("tl")}
      {corner("tr")}
      {corner("bl")}
      {corner("br")}
      {children}
    </div>
  )
}
