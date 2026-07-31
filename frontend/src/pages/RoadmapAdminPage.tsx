import { useEffect, useState, type DragEvent } from "react"
import { Link } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import {
  getRoadmap,
  listUnassignedRoadmapLabs,
  createRoadmapCategoria,
  addRoadmapNodo,
  reorderRoadmapNodo,
  removeRoadmapNodo,
  ApiError,
  type RoadmapCategoria,
  type LaboratorioSinRoadmap,
} from "./api"
import Navbar from "../components/Navbar"
import Footer from "../components/Footer"
import TerminalHeader from "../components/TerminalHeader"
import SectionHeading from "../components/SectionHeading"
import { IconFlask, IconGlobe } from "../components/icons"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Skeleton } from "../components/ui/skeleton"

interface DragPayload {
  laboratorioId: string
  sourceNodoId?: string
}

// Calcula en qué índice insertar según la posición X del cursor contra
// el punto medio de cada nodo ya presente en la pista — técnica
// estándar de reorder por drag-and-drop sin librería (ver plan:
// sin dnd-kit/react-dnd instalado, HTML5 DnD nativo alcanza).
function computeDropIndex(clientX: number, container: HTMLElement): number {
  const nodos = Array.from(container.querySelectorAll<HTMLElement>("[data-node-index]"))
  for (const el of nodos) {
    const rect = el.getBoundingClientRect()
    const mid = rect.left + rect.width / 2
    if (clientX < mid) return Number(el.dataset.nodeIndex)
  }
  return nodos.length
}

export default function RoadmapAdminPage() {
  const role = localStorage.getItem("role")
  const [categorias, setCategorias] = useState<RoadmapCategoria[]>([])
  const [pool, setPool] = useState<LaboratorioSinRoadmap[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [dragOver, setDragOver] = useState<{ categoriaId: string; index: number } | null>(null)
  const [showNewCategory, setShowNewCategory] = useState(false)
  const [newCategoryName, setNewCategoryName] = useState("")
  const [busy, setBusy] = useState(false)

  const load = () => {
    setLoading(true)
    Promise.all([getRoadmap(), listUnassignedRoadmapLabs()])
      .then(([categoriasData, poolData]) => {
        setCategorias(categoriasData)
        setPool(poolData)
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "No se pudo cargar el roadmap."))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  if (role !== "administrador") {
    return (
      <div className="min-h-screen flex flex-col" style={{ backgroundColor: "var(--canvas)", color: "var(--text-base)" }}>
        <Navbar />
        <main className="flex-1 flex items-center justify-center">
          <div className="chamfer p-8 text-center" style={{ border: "1px solid var(--signal-red-dim)" }}>
            <p className="text-sm mb-3" style={{ color: "var(--text-base)" }}>No tenés permiso para ver esta página.</p>
            <Link to="/roadmap" className="text-xs uppercase tracking-wide" style={{ color: "var(--signal-cyan)", fontFamily: "var(--font-mono)" }}>
              ← Volver al roadmap
            </Link>
          </div>
        </main>
        <Footer />
      </div>
    )
  }

  const handleDragStart = (e: DragEvent, payload: DragPayload) => {
    e.dataTransfer.setData("application/json", JSON.stringify(payload))
    e.dataTransfer.effectAllowed = "move"
  }

  const handleDragOverLane = (e: DragEvent<HTMLDivElement>, categoriaId: string) => {
    e.preventDefault()
    const index = computeDropIndex(e.clientX, e.currentTarget)
    setDragOver({ categoriaId, index })
  }

  const handleDrop = async (e: DragEvent<HTMLDivElement>, categoriaId: string) => {
    e.preventDefault()
    const raw = e.dataTransfer.getData("application/json")
    setDragOver(null)
    if (!raw) return
    const payload: DragPayload = JSON.parse(raw)
    const posicion = computeDropIndex(e.clientX, e.currentTarget)

    setBusy(true)
    setError("")
    try {
      if (payload.sourceNodoId) {
        await reorderRoadmapNodo(payload.sourceNodoId, { categoria_id: categoriaId, posicion })
      } else {
        await addRoadmapNodo({ categoria_id: categoriaId, laboratorio_id: payload.laboratorioId, posicion })
      }
      load()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo actualizar el roadmap.")
      setBusy(false)
    }
  }

  const handleDropOnEmptyLane = async (categoriaId: string, laboratorioId: string) => {
    setBusy(true)
    setError("")
    try {
      await addRoadmapNodo({ categoria_id: categoriaId, laboratorio_id: laboratorioId, posicion: 0 })
      load()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo agregar el laboratorio.")
      setBusy(false)
    }
  }

  const handleRemove = async (nodoId: string) => {
    setBusy(true)
    setError("")
    try {
      await removeRoadmapNodo(nodoId)
      load()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo quitar el laboratorio.")
      setBusy(false)
    }
  }

  const handleCreateCategory = async () => {
    if (!newCategoryName.trim()) return
    setBusy(true)
    setError("")
    try {
      await createRoadmapCategoria(newCategoryName.trim())
      setNewCategoryName("")
      setShowNewCategory(false)
      load()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo crear la categoría.")
      setBusy(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: "var(--canvas)", color: "var(--text-base)" }}>
      <Navbar />
      <main className="flex-1">
        <div className="mx-auto px-4 sm:px-6 md:px-8 py-8 sm:py-10" style={{ maxWidth: "1300px" }}>
          <TerminalHeader
            title="Gestionar Roadmap"
            subtitle="Arrastrá un laboratorio hacia una pista para ubicarlo — soltalo entre dos nodos para insertarlo ahí."
            prompt="roadmap --admin"
            right={
              <Button asChild size="sm" variant="outline" className="chamfer-sm font-mono text-xs uppercase tracking-wide">
                <Link to="/roadmap">Ver roadmap público</Link>
              </Button>
            }
          />

          <AnimatePresence>
            {error && (
              <motion.p initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="text-sm mb-6 px-3 py-2 chamfer-sm" style={{ color: "var(--signal-red)", backgroundColor: "rgba(255,71,87,0.08)", border: "1px solid var(--signal-red-dim)" }} role="alert">
                ▲ {error}
              </motion.p>
            )}
          </AnimatePresence>

          {loading ? (
            <div className="flex flex-col gap-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="chamfer h-28" style={{ backgroundColor: "var(--surface)" }} />
              ))}
            </div>
          ) : (
            <div className="grid gap-8" style={{ gridTemplateColumns: "260px 1fr" }}>
              {/* ═══ POOL SIN ASIGNAR ═══ */}
              <div>
                <SectionHeading icon={<IconFlask />} title="Sin asignar" subtitle={`${pool.length} laboratorio(s)`} />
                <div className="flex flex-col gap-2">
                  {pool.length === 0 ? (
                    <p className="text-xs" style={{ color: "var(--text-dim)" }}>Todos los laboratorios de admin ya están en el roadmap.</p>
                  ) : (
                    pool.map((lab) => (
                      <div
                        key={lab.id}
                        draggable
                        onDragStart={(e) => handleDragStart(e, { laboratorioId: lab.id })}
                        className="chamfer-sm p-3 cursor-grab active:cursor-grabbing"
                        style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}
                      >
                        <span className="text-xs font-bold block truncate" style={{ color: "var(--text-heading)" }}>{lab.nombre}</span>
                        <span className="text-[10px] uppercase" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>{lab.nivel_dificultad}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* ═══ PISTAS ═══ */}
              <div>
                <div className="flex items-center justify-between mb-6">
                  <SectionHeading icon={<IconGlobe />} title="Pistas del roadmap" />
                  {showNewCategory ? (
                    <div className="flex items-center gap-2">
                      <Input
                        value={newCategoryName}
                        onChange={(e) => setNewCategoryName(e.target.value)}
                        placeholder="Nombre de la categoría"
                        className="chamfer-sm h-8 w-48 text-xs"
                        autoFocus
                      />
                      <Button size="sm" disabled={busy} onClick={handleCreateCategory} className="chamfer-sm font-mono text-[10px] uppercase">Crear</Button>
                      <Button size="sm" variant="outline" onClick={() => { setShowNewCategory(false); setNewCategoryName("") }} className="chamfer-sm font-mono text-[10px] uppercase">Cancelar</Button>
                    </div>
                  ) : (
                    <Button size="sm" onClick={() => setShowNewCategory(true)} className="chamfer-sm font-mono text-xs uppercase">+ Nueva categoría</Button>
                  )}
                </div>

                {categorias.length === 0 && (
                  <div className="chamfer p-6 text-center mb-4" style={{ border: "1px dashed var(--border-strong)" }}>
                    <p className="text-xs uppercase tracking-widest m-0" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                      [ Todavía no hay categorías — creá la primera ]
                    </p>
                  </div>
                )}

                {categorias.map((categoria) => (
                  <div key={categoria.id} className="mb-6">
                    <span className="text-xs font-bold uppercase tracking-wide mb-2 block" style={{ color: "var(--text-heading)" }}>{categoria.nombre}</span>
                    {categoria.nodos.length === 0 ? (
                      <div
                        onDragOver={(e) => e.preventDefault()}
                        onDrop={(e) => {
                          e.preventDefault()
                          const raw = e.dataTransfer.getData("application/json")
                          if (!raw) return
                          const payload: DragPayload = JSON.parse(raw)
                          if (payload.sourceNodoId) {
                            reorderRoadmapNodo(payload.sourceNodoId, { categoria_id: categoria.id, posicion: 0 }).then(load)
                          } else {
                            handleDropOnEmptyLane(categoria.id, payload.laboratorioId)
                          }
                        }}
                        className="chamfer-sm p-4 text-center"
                        style={{ border: "1px dashed var(--border-default)" }}
                      >
                        <span className="text-[10px] uppercase tracking-widest" style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
                          Soltá un laboratorio acá
                        </span>
                      </div>
                    ) : (
                      <div
                        onDragOver={(e) => handleDragOverLane(e, categoria.id)}
                        onDragLeave={() => setDragOver(null)}
                        onDrop={(e) => handleDrop(e, categoria.id)}
                        className="flex items-stretch gap-1 overflow-x-auto pb-2"
                      >
                        {categoria.nodos.map((nodo, i) => (
                          <div key={nodo.id} className="flex items-center shrink-0">
                            {dragOver?.categoriaId === categoria.id && dragOver.index === i && (
                              <span className="shrink-0" style={{ width: 3, height: 64, backgroundColor: "var(--signal-cyan)" }} />
                            )}
                            <div
                              data-node-index={i}
                              draggable
                              onDragStart={(e) => handleDragStart(e, { laboratorioId: nodo.laboratorio_id, sourceNodoId: nodo.id })}
                              className="chamfer-sm p-3 relative group cursor-grab active:cursor-grabbing"
                              style={{ width: 140, backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}
                            >
                              <span className="text-[10px] font-mono block mb-1" style={{ color: "var(--signal-amber)" }}>#{nodo.posicion + 1}</span>
                              <span className="text-[11px] font-bold block leading-tight" style={{ color: "var(--text-heading)" }}>{nodo.nombre}</span>
                              <button
                                type="button"
                                onClick={() => handleRemove(nodo.id)}
                                aria-label="Quitar del roadmap"
                                className="absolute top-1 right-1 w-5 h-5 flex items-center justify-center text-xs cursor-pointer border-none opacity-0 group-hover:opacity-100 transition-opacity"
                                style={{ backgroundColor: "rgba(255,71,87,0.15)", color: "var(--signal-red)" }}
                              >
                                ×
                              </button>
                            </div>
                          </div>
                        ))}
                        {dragOver?.categoriaId === categoria.id && dragOver.index === categoria.nodos.length && (
                          <span className="shrink-0" style={{ width: 3, height: 64, backgroundColor: "var(--signal-cyan)" }} />
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  )
}
