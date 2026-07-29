import type { ReactNode } from "react"
import { motion } from "framer-motion"
import MatrixRain from "./MatrixRain"
import GlitchText from "./GlitchText"

// Encabezado "ventana de terminal" compartido por dashboards/catálogo/detalle
// de lab — reemplaza el <header> plano (solo <h1>+<p>) por algo con más
// identidad temática: barra de título con los 3 puntos clásicos + prompt,
// lluvia de caracteres de fondo muy tenue (<MatrixRain />), y el título con
// efecto glitch al pasar el mouse (<GlitchText />). Menos "soso" que un
// simple <h1>, mismo contenido/información.
export default function TerminalHeader({
  title,
  subtitle,
  prompt = "session",
  right,
}: {
  title: string
  subtitle?: string
  prompt?: string
  right?: ReactNode
}) {
  return (
    <motion.header
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="relative overflow-hidden rounded-lg mb-8 sm:mb-10"
      style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--ui-border-default)" }}
    >
      <MatrixRain opacity={0.05} />

      <div
        className="relative z-10 flex items-center gap-1.5 px-4 py-2"
        style={{ borderBottom: "1px solid var(--ui-border-default)" }}
      >
        <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: "#EF4444" }} />
        <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: "#F59E0B" }} />
        <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: "#22C55E" }} />
        <span
          className="ml-2 text-[10px] sm:text-xs truncate"
          style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
        >
          gaia@platlab:~$ {prompt}
        </span>
      </div>

      <div className="relative z-10 flex items-start justify-between gap-4 flex-wrap px-4 sm:px-6 py-5 sm:py-6">
        <div>
          <GlitchText
            as="h1"
            className="text-2xl sm:text-3xl font-semibold m-0"
          >
            <span style={{ color: "var(--text-heading)", fontFamily: "var(--font-heading)" }}>
              {title}
            </span>
          </GlitchText>
          {subtitle && (
            <p className="text-xs sm:text-sm mt-1" style={{ color: "var(--text-muted)" }}>
              {subtitle}
            </p>
          )}
        </div>
        {right}
      </div>
    </motion.header>
  )
}
