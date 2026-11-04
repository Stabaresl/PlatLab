import { memo } from "react"
import { motion } from "framer-motion"
import RoadmapNode from "./RoadmapNode"
import Revelar from "./movimiento/Revelar"
import BarraLlenado from "./movimiento/BarraLlenado"
import { EASE_TACTICO } from "./movimiento/curvas"
import type { RoadmapCategoria, RoadmapNodo } from "../pages/api"

const OFFSET_Y = 34

type EstadoConector = "hecho" | "activo" | "pendiente"

// El conector cuenta el camino: verde entre dos laboratorios terminados,
// con una señal que corre cuando lleva al siguiente disponible, y punteado
// mientras siga bloqueado (o para un visitante sin sesión).
function estadoConector(previo: RoadmapNodo, actual: RoadmapNodo): EstadoConector {
  if (previo.estado !== "completado") return "pendiente"
  if (actual.estado === "completado") return "hecho"
  if (actual.estado === "disponible") return "activo"
  return "pendiente"
}

const FONDO_CONECTOR: Record<EstadoConector, string> = {
  hecho: "var(--signal-green)",
  activo: "linear-gradient(90deg, var(--signal-green), var(--signal-cyan))",
  pendiente: "repeating-linear-gradient(90deg, var(--border-strong) 0 6px, transparent 6px 12px)",
}

// Un "camino" del roadmap: los nodos de una categoría en zigzag
// (offset vertical alternado por índice, estilo mapa de niveles), con
// un conector entre cada par consecutivo — sin SVG ni medición de
// posiciones vía DOM, solo CSS/transform. El scroll horizontal cubre
// categorías con muchos nodos.
function RoadmapLane({
  categoria,
  authed,
  isEstudiante,
  busyNodoId,
  onEnroll,
}: {
  categoria: RoadmapCategoria
  authed: boolean
  isEstudiante: boolean
  busyNodoId: string | null
  onEnroll: (nodoId: string) => void
}) {
  const conEstado = categoria.nodos.some((n) => n.estado !== null)
  const completados = categoria.nodos.filter((n) => n.estado === "completado").length
  const siguiente = categoria.nodos.findIndex((n) => n.estado === "disponible")

  return (
    <Revelar className="mb-10 sm:mb-14">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2 mb-6">
        <div className="flex items-center gap-2 min-w-0">
          <motion.span
            className="chamfer-sm w-2 h-6 shrink-0"
            style={{ backgroundColor: "var(--signal-amber)", originY: 1 }}
            initial={{ scaleY: 0 }}
            whileInView={{ scaleY: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, ease: EASE_TACTICO }}
          />
          <h2 className="text-sm sm:text-base font-bold uppercase tracking-wide m-0" style={{ color: "var(--text-heading)" }}>
            {categoria.nombre}
          </h2>
          <span className="text-xs font-mono whitespace-nowrap" style={{ color: "var(--text-muted)" }}>
            {categoria.nodos.length} laboratorio{categoria.nodos.length === 1 ? "" : "s"}
          </span>
        </div>
        {conEstado && categoria.nodos.length > 0 && (
          <div className="flex items-center gap-2 ml-auto" style={{ width: "min(200px, 100%)" }}>
            <BarraLlenado
              valor={completados}
              max={categoria.nodos.length}
              segmentos
              color="var(--signal-green)"
              alto={5}
              etiqueta={`${completados} de ${categoria.nodos.length} laboratorios completados en ${categoria.nombre}`}
              retraso={0.2}
            />
            <span className="text-[11px] font-mono shrink-0" style={{ color: completados > 0 ? "var(--signal-green)" : "var(--text-dim)" }}>
              {completados}/{categoria.nodos.length}
            </span>
          </div>
        )}
      </div>

      {categoria.nodos.length === 0 ? (
        <div className="chamfer p-6 text-center" style={{ border: "1px dashed var(--border-strong)" }}>
          <p className="text-xs uppercase tracking-widest m-0" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
            [ Sin laboratorios todavía ]
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto pb-10 pt-5 -mx-4 px-4 sm:mx-0 sm:px-0">
          <div className="flex items-start" style={{ minWidth: "max-content" }}>
            {categoria.nodos.map((nodo, i) => {
              const offset = i % 2 === 1 ? OFFSET_Y : 0
              const conector = i > 0 ? estadoConector(categoria.nodos[i - 1], nodo) : null
              return (
                <motion.div
                  key={nodo.id}
                  layout
                  initial={{ opacity: 0, y: 12 }}
                  whileInView={{ opacity: 1, y: offset }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.45, delay: Math.min(i * 0.08, 0.6), ease: EASE_TACTICO }}
                  className="flex items-center shrink-0"
                >
                  {conector && (
                    <motion.span
                      aria-hidden="true"
                      className="relative shrink-0 overflow-hidden"
                      style={{
                        width: 40,
                        height: 2,
                        marginTop: 48,
                        background: FONDO_CONECTOR[conector],
                        rotate: i % 2 === 1 ? 18 : -18,
                        originX: 0,
                      }}
                      initial={{ scaleX: 0 }}
                      whileInView={{ scaleX: 1 }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.5, delay: Math.min(i * 0.08, 0.6) + 0.15, ease: EASE_TACTICO }}
                    >
                      {conector === "activo" && <span className="flujo-conector" />}
                    </motion.span>
                  )}
                  <div className="mx-1">
                    <RoadmapNode
                      nodo={nodo}
                      authed={authed}
                      isEstudiante={isEstudiante}
                      busy={busyNodoId === nodo.id}
                      destacado={i === siguiente}
                      onEnroll={onEnroll}
                    />
                  </div>
                </motion.div>
              )
            })}
          </div>
        </div>
      )}
    </Revelar>
  )
}

export default memo(RoadmapLane)
