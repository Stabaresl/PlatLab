import { memo, useEffect, useRef, useState } from "react"
import { createPortal } from "react-dom"
import { Link, useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import TiltCard from "./TiltCard"
import StatusDot from "./StatusDot"
import { IconLock } from "./icons"
import { Button } from "./ui/button"
import type { RoadmapNodo, NivelDificultad } from "../pages/api"

const DIFICULTAD_LABEL: Record<NivelDificultad, string> = {
  basico: "Básico",
  intermedio: "Intermedio",
  avanzado: "Avanzado",
}

const ESTADO_COLOR = {
  completado: "var(--signal-green)",
  disponible: "var(--signal-cyan)",
  bloqueado: "var(--text-dim)",
} as const

const ESTADO_GLOW = {
  completado: "51,214,159",
  disponible: "56,214,245",
  bloqueado: "136,146,163",
} as const

// Un nodo del roadmap — círculo con el número de posición, coloreado
// según el estado del estudiante (completado/disponible/bloqueado, o
// neutro si es un visitante sin sesión). El tooltip (nombre, dificultad,
// "recomendaciones"/temas, prerequisitos) se renderiza en un portal a
// `document.body` con `position: fixed` — las pistas hacen scroll
// horizontal (`overflow-x-auto` en `RoadmapLane`), y un tooltip
// `absolute` normal quedaba recortado por ese contenedor (el navegador
// fuerza el eje vertical a comportarse como recortado apenas el eje
// horizontal deja de ser `visible`), lo que además tapaba el único
// botón de "Inscribirme" — por eso el nodo entero también es
// clickeable directamente, no depende únicamente del tooltip.
function RoadmapNode({
  nodo,
  authed,
  isEstudiante,
  busy,
  onEnroll,
}: {
  nodo: RoadmapNodo
  authed: boolean
  isEstudiante: boolean
  busy: boolean
  onEnroll: (nodoId: string) => void
}) {
  const navigate = useNavigate()
  const wrapperRef = useRef<HTMLDivElement>(null)
  const [hover, setHover] = useState(false)
  const [tooltipPos, setTooltipPos] = useState<{ top: number; left: number } | null>(null)
  const estado = nodo.estado
  const color = estado ? ESTADO_COLOR[estado] : "var(--signal-cyan)"
  const glow = estado ? ESTADO_GLOW[estado] : "56,214,245"
  const bloqueado = estado === "bloqueado"
  const disponible = estado === "disponible"

  const openTooltip = () => {
    const rect = wrapperRef.current?.getBoundingClientRect()
    if (rect) setTooltipPos({ top: rect.top, left: rect.left + rect.width / 2 })
    setHover(true)
  }
  const closeTooltip = () => setHover(false)

  useEffect(() => {
    if (!hover) return
    const onScroll = () => closeTooltip()
    window.addEventListener("scroll", onScroll, true)
    window.addEventListener("resize", onScroll)
    return () => {
      window.removeEventListener("scroll", onScroll, true)
      window.removeEventListener("resize", onScroll)
    }
  }, [hover])

  const handleActivate = () => {
    if (bloqueado || busy) return
    if (!authed) {
      navigate("/signup")
      return
    }
    if (disponible && isEstudiante) {
      onEnroll(nodo.id)
    }
  }

  return (
    <div
      ref={wrapperRef}
      className="relative flex flex-col items-center"
      style={{ cursor: bloqueado ? "default" : "pointer" }}
      onMouseEnter={openTooltip}
      onMouseLeave={closeTooltip}
      onClick={handleActivate}
      role={!bloqueado ? "button" : undefined}
      tabIndex={!bloqueado ? 0 : undefined}
      onKeyDown={(e) => { if (!bloqueado && (e.key === "Enter" || e.key === " ")) handleActivate() }}
    >
      <TiltCard
        glowColor={glow}
        intensity={bloqueado ? 0 : 6}
        className="chamfer flex flex-col items-center justify-center shrink-0"
        style={{
          width: 96,
          height: 96,
          backgroundColor: "var(--surface)",
          border: `2px solid ${color}`,
          opacity: bloqueado ? 0.55 : 1,
          cursor: bloqueado ? "not-allowed" : "pointer",
        }}
      >
        {bloqueado ? (
          <IconLock style={{ color }} width={22} height={22} />
        ) : (
          <span className="text-lg font-bold text-display" style={{ color }}>
            {nodo.posicion + 1}
          </span>
        )}
        <span
          className="mt-1 text-[9px] uppercase tracking-widest text-center px-1 leading-tight"
          style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
        >
          {DIFICULTAD_LABEL[nodo.nivel_dificultad]}
        </span>
      </TiltCard>

      <span
        className="mt-2 text-[11px] font-semibold text-center max-w-[110px] leading-tight"
        style={{ color: "var(--text-heading)" }}
      >
        {nodo.nombre}
      </span>

      {hover && tooltipPos &&
        createPortal(
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.15 }}
            onMouseEnter={openTooltip}
            onMouseLeave={closeTooltip}
            className="chamfer-sm p-3"
            style={{
              position: "fixed",
              top: tooltipPos.top,
              left: tooltipPos.left,
              transform: "translate(-50%, calc(-100% - 12px))",
              width: 240,
              zIndex: 1000,
              backgroundColor: "var(--canvas-raised)",
              border: `1px solid ${color}`,
              boxShadow: "0 12px 28px rgba(0,0,0,0.5)",
            }}
          >
            <div className="flex items-center justify-between gap-2 mb-1.5">
              <span className="text-xs font-bold" style={{ color: "var(--text-heading)" }}>
                {nodo.nombre}
              </span>
              {estado && (
                <StatusDot
                  variant={estado === "completado" ? "online" : estado === "disponible" ? "info" : "idle"}
                  label={estado === "completado" ? "Completado" : estado === "disponible" ? "Disponible" : "Bloqueado"}
                  pulse={estado === "disponible"}
                />
              )}
            </div>

            {nodo.temas.length > 0 && (
              <div className="flex flex-wrap gap-1 mb-2">
                {nodo.temas.map((t) => (
                  <span
                    key={t}
                    className="text-[9px] px-1.5 py-0.5"
                    style={{ backgroundColor: "var(--surface-hover)", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
                  >
                    {t}
                  </span>
                ))}
              </div>
            )}

            {nodo.prerequisitos.length > 0 && (
              <p className="text-[11px] mb-2 leading-relaxed" style={{ color: "var(--text-muted)" }}>
                <span className="font-semibold" style={{ color: "var(--text-base)" }}>Requiere completar:</span>{" "}
                {nodo.prerequisitos.map((p) => p.nombre).join(", ")}
              </p>
            )}

            {disponible && isEstudiante && (
              <Button
                size="sm"
                disabled={busy}
                onClick={(e) => { e.stopPropagation(); onEnroll(nodo.id) }}
                className="w-full chamfer-sm font-mono text-[10px] uppercase tracking-wide"
              >
                {busy ? "Inscribiendo…" : "Inscribirme"}
              </Button>
            )}
            {estado === "completado" && (
              <span className="text-[10px] uppercase tracking-wide" style={{ color: "var(--signal-green)", fontFamily: "var(--font-mono)" }}>
                ✓ Ya lo completaste
              </span>
            )}
            {!authed && (
              <Link
                to="/signup"
                onClick={(e) => e.stopPropagation()}
                className="block text-center text-[10px] uppercase tracking-wide no-underline chamfer-sm px-2 py-1.5"
                style={{ backgroundColor: "var(--surface-hover)", color: "var(--signal-amber)", fontFamily: "var(--font-mono)" }}
              >
                Crea tu cuenta para inscribirte
              </Link>
            )}
          </motion.div>,
          document.body,
        )}
    </div>
  )
}

// RoadmapLane re-renderiza sus nodos cada vez que busyNodoId cambia (se
// inscribe alguien en cualquier nodo de la pista) — memo evita que los
// nodos que no cambiaron (mismo nodo/busy/authed) vuelvan a montar el
// tooltip en portal y recalcular su posición.
export default memo(RoadmapNode)
