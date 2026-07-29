import type { ReactNode } from "react"

// Efecto "glitch RGB split" al pasar el mouse — dos copias del mismo texto
// desfasadas en rojo/cian se activan vía CSS puro (:hover + animation-play-state),
// sin JS ni librerías. Pensado para títulos, no para texto largo.
export default function GlitchText({
  children,
  className = "",
  as: Tag = "span",
}: {
  children: ReactNode
  className?: string
  as?: "span" | "h1" | "h2" | "h3"
}) {
  return (
    <Tag className={`relative inline-block group ${className}`}>
      <span className="relative z-10">{children}</span>
      <span
        aria-hidden="true"
        className="absolute inset-0 pointer-events-none opacity-0 group-hover:opacity-100"
        style={{ color: "#EF4444", mixBlendMode: "screen", animation: "glitch-shift-1 0.6s steps(2) infinite" }}
      >
        {children}
      </span>
      <span
        aria-hidden="true"
        className="absolute inset-0 pointer-events-none opacity-0 group-hover:opacity-100"
        style={{ color: "#3B82F6", mixBlendMode: "screen", animation: "glitch-shift-2 0.6s steps(2) infinite" }}
      >
        {children}
      </span>
    </Tag>
  )
}
