import useReducedMotion from "../hooks/useReducedMotion"

// Grilla táctica de fondo — más lenta y sutil que un "grid cyberpunk" stock
// (7s de deriva, opacidad baja) para leer como HUD de operaciones, no como
// plantilla. Se apaga por completo con prefers-reduced-motion.
export default function CyberGrid({
  opacity = 0.35,
  color = "255,176,32",
  fade = true,
}: {
  opacity?: number
  color?: string
  fade?: boolean
}) {
  const reduced = useReducedMotion()

  return (
    <div
      className="absolute inset-0 pointer-events-none overflow-hidden"
      aria-hidden="true"
      style={{
        opacity,
        backgroundImage: `
          linear-gradient(rgba(${color},0.4) 1px, transparent 1px),
          linear-gradient(90deg, rgba(${color},0.4) 1px, transparent 1px)
        `,
        backgroundSize: "48px 48px",
        animation: reduced ? undefined : "grid-drift 7s linear infinite",
        maskImage: fade ? "radial-gradient(ellipse at center, black 20%, transparent 75%)" : undefined,
        WebkitMaskImage: fade ? "radial-gradient(ellipse at center, black 20%, transparent 75%)" : undefined,
      }}
    />
  )
}
