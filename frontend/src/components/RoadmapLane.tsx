import { motion } from "framer-motion"
import RoadmapNode from "./RoadmapNode"
import type { RoadmapCategoria } from "../pages/api"

const OFFSET_Y = 34

// Un "camino" del roadmap: los nodos de una categoría en zigzag
// (offset vertical alternado por índice, estilo mapa de niveles), con
// un conector simple entre cada par consecutivo — sin SVG ni medición
// de posiciones vía DOM, solo CSS/transform (más fácil de mantener,
// ver plan). El scroll horizontal cubre categorías con muchos nodos.
export default function RoadmapLane({
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
  return (
    <div className="mb-10 sm:mb-14">
      <div className="flex items-center gap-2 mb-6">
        <span className="chamfer-sm w-2 h-6" style={{ backgroundColor: "var(--signal-amber)" }} />
        <h2 className="text-sm sm:text-base font-bold uppercase tracking-wide m-0" style={{ color: "var(--text-heading)" }}>
          {categoria.nombre}
        </h2>
        <span className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>
          {categoria.nodos.length} laboratorio{categoria.nodos.length === 1 ? "" : "s"}
        </span>
      </div>

      {categoria.nodos.length === 0 ? (
        <div className="chamfer p-6 text-center" style={{ border: "1px dashed var(--border-strong)" }}>
          <p className="text-xs uppercase tracking-widest m-0" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
            [ Sin laboratorios todavía ]
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto pb-10 pt-2 -mx-4 px-4 sm:mx-0 sm:px-0">
          <div className="flex items-start" style={{ minWidth: "max-content" }}>
            {categoria.nodos.map((nodo, i) => {
              const offset = i % 2 === 1 ? OFFSET_Y : 0
              return (
                <motion.div
                  key={nodo.id}
                  layout
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: offset }}
                  transition={{ duration: 0.35, delay: Math.min(i * 0.06, 0.4) }}
                  className="flex items-center shrink-0"
                >
                  {i > 0 && (
                    <span
                      aria-hidden="true"
                      className="shrink-0"
                      style={{
                        width: 40,
                        height: 2,
                        marginTop: 48,
                        backgroundColor: "var(--border-strong)",
                        backgroundImage:
                          "repeating-linear-gradient(90deg, var(--border-strong) 0 6px, transparent 6px 12px)",
                        transform: `rotate(${i % 2 === 1 ? 18 : -18}deg)`,
                        transformOrigin: "center",
                      }}
                    />
                  )}
                  <div className="mx-1">
                    <RoadmapNode
                      nodo={nodo}
                      authed={authed}
                      isEstudiante={isEstudiante}
                      busy={busyNodoId === nodo.id}
                      onEnroll={onEnroll}
                    />
                  </div>
                </motion.div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
