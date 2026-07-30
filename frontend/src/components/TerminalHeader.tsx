import type { ReactNode } from "react"
import { motion } from "framer-motion"
import MatrixRain from "./MatrixRain"
import GlitchText from "./GlitchText"
import ReticleFrame from "./ReticleFrame"
import MouseGlow, { trackGlow, untrackGlow } from "./MouseGlow"

// Encabezado "consola" compartido por dashboards/catálogo/detalle de lab —
// barra de título con chrome de terminal + prompt, retícula de esquina y
// título con aberración cromática al pasar el mouse.
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
      className="mb-8 sm:mb-10"
    >
      <ReticleFrame color="var(--signal-amber)" size={12} className="chamfer overflow-hidden" >
        <div
          onMouseMove={trackGlow}
          onMouseLeave={untrackGlow}
          className="relative overflow-hidden"
          style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}
        >
          <MatrixRain opacity={0.045} />
          <MouseGlow color="255,176,32" size={360} opacity={0.12} />

          <div
            className="relative z-10 flex items-center gap-1.5 px-4 py-2"
            style={{ borderBottom: "1px solid var(--border-default)" }}
          >
            <span className="w-2.5 h-2.5" style={{ backgroundColor: "var(--signal-red)" }} />
            <span className="w-2.5 h-2.5" style={{ backgroundColor: "var(--signal-amber)" }} />
            <span className="w-2.5 h-2.5" style={{ backgroundColor: "var(--signal-green)" }} />
            <span
              className="ml-2 text-[10px] sm:text-xs truncate"
              style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
            >
              gaia@platlab:~$ {prompt}
            </span>
          </div>

          <div className="relative z-10 flex items-start justify-between gap-4 flex-wrap px-4 sm:px-6 py-5 sm:py-6">
            <div>
              <GlitchText as="h1" className="text-xl sm:text-2xl font-bold uppercase tracking-wide m-0">
                <span style={{ color: "var(--text-heading)" }}>{title}</span>
              </GlitchText>
              {subtitle && (
                <p className="text-xs sm:text-sm mt-1" style={{ color: "var(--text-muted)" }}>
                  {subtitle}
                </p>
              )}
            </div>
            {right}
          </div>
        </div>
      </ReticleFrame>
    </motion.header>
  )
}
