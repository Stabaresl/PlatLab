import type { ReactNode } from "react"

// Aberración cromática ámbar/cian al pasar el mouse — CSS puro. Recolorizado
// para calzar con la señal táctica (antes era rojo/azul genérico "glitch").
// prefers-reduced-motion lo neutraliza automáticamente (ver index.css).
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
        style={{ color: "var(--signal-amber)", mixBlendMode: "screen", animation: "chroma-shift-a 0.6s steps(2) infinite" }}
      >
        {children}
      </span>
      <span
        aria-hidden="true"
        className="absolute inset-0 pointer-events-none opacity-0 group-hover:opacity-100"
        style={{ color: "var(--signal-cyan)", mixBlendMode: "screen", animation: "chroma-shift-b 0.6s steps(2) infinite" }}
      >
        {children}
      </span>
    </Tag>
  )
}
