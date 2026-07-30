import { useEffect, useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import { getCatalogo, ApiError, type LaboratorioListItem, type NivelDificultad } from "./api"
import Navbar from "../components/Navbar"
import Footer from "../components/Footer"
import HeroBackground from "../components/HeroBackground"
import TerminalHeader from "../components/TerminalHeader"
import { IconFlask, IconSearch, IconArrowRight } from "../components/icons"
import { Skeleton } from "../components/ui/skeleton"

const DIFICULTAD_LABEL: Record<NivelDificultad, string> = {
  basico: "Básico",
  intermedio: "Intermedio",
  avanzado: "Avanzado",
}
const DIFICULTAD_COLOR: Record<NivelDificultad, string> = {
  basico: "var(--signal-green)",
  intermedio: "var(--signal-amber)",
  avanzado: "var(--signal-red)",
}

export default function CatalogPage() {
  const [labs, setLabs] = useState<LaboratorioListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [query, setQuery] = useState("")
  const [dificultad, setDificultad] = useState<NivelDificultad | "">("")

  useEffect(() => {
    setLoading(true)
    getCatalogo(dificultad ? { dificultad } : undefined)
      .then((res) => setLabs(res.results))
      .catch((err) => setError(err instanceof ApiError ? err.message : "No se pudo cargar el catálogo."))
      .finally(() => setLoading(false))
  }, [dificultad])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return labs
    return labs.filter(
      (l) => l.nombre.toLowerCase().includes(q) || l.temas.some((t) => t.toLowerCase().includes(q)),
    )
  }, [labs, query])

  return (
    <div className="relative min-h-screen overflow-hidden" style={{ backgroundColor: "var(--canvas)", color: "var(--text-base)" }}>
      <HeroBackground image="term" imageOpacity={0.07} overlayOpacity={0.9} texture="grid" textureOpacity={0.04} />
      <div className="relative z-10 flex flex-col min-h-screen">
        <Navbar />
        <main className="flex-1">
          <div className="mx-auto px-4 sm:px-6 md:px-8 py-8 sm:py-10 md:py-12" style={{ maxWidth: "1200px" }}>
            <TerminalHeader
              title="Catálogo de Laboratorios"
              subtitle="Este es el roadmap completo de laboratorios de GAIA: no hace falta esperar una invitación para ver qué hay disponible. Iniciá sesión para inscribirte en cualquiera de ellos."
              prompt="ls /laboratorios --publicados"
            />

            {/* Filtros */}
            <div className="flex flex-col sm:flex-row gap-3 mb-6 sm:mb-8">
              <div className="chamfer-sm flex items-center gap-2 flex-1 px-3.5 py-2.5" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
                <IconSearch style={{ color: "var(--text-muted)" }} />
                <input
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Buscar por nombre o tema…"
                  className="flex-1 bg-transparent border-none outline-none text-sm"
                  style={{ color: "var(--text-base)", fontFamily: "var(--font-mono)" }}
                />
              </div>
              <div className="flex gap-2">
                {(["", "basico", "intermedio", "avanzado"] as const).map((d) => (
                  <button
                    key={d || "todos"}
                    type="button"
                    onClick={() => setDificultad(d)}
                    className="chamfer-sm px-3 sm:px-4 py-2 text-xs font-semibold cursor-pointer transition-colors whitespace-nowrap uppercase tracking-wide"
                    style={{
                      backgroundColor: dificultad === d ? (d ? DIFICULTAD_COLOR[d] : "var(--signal-amber)") : "var(--surface)",
                      color: dificultad === d ? "#0a0700" : "var(--text-muted)",
                      border: `1px solid ${dificultad === d ? (d ? DIFICULTAD_COLOR[d] : "var(--signal-amber)") : "var(--border-default)"}`,
                      fontFamily: "var(--font-mono)",
                    }}
                  >
                    {d ? DIFICULTAD_LABEL[d] : "Todos"}
                  </button>
                ))}
              </div>
            </div>

            <AnimatePresence>
              {error && (
                <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="text-sm mb-6 px-3 py-2 chamfer-sm" style={{ color: "var(--signal-red)", backgroundColor: "rgba(255,71,87,0.08)", border: "1px solid var(--signal-red-dim)" }} role="alert">
                  ▲ {error}
                </motion.p>
              )}
            </AnimatePresence>

            {loading ? (
              <div className="grid gap-4" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))" }}>
                {Array.from({ length: 6 }).map((_, i) => (
                  <Skeleton key={i} className="chamfer h-40" style={{ backgroundColor: "var(--surface)" }} />
                ))}
              </div>
            ) : filtered.length === 0 ? (
              <div className="chamfer flex flex-col items-center gap-3 p-10 sm:p-16 text-center" style={{ border: "1px dashed var(--border-strong)" }}>
                <span className="chamfer-sm flex items-center justify-center w-12 h-12" style={{ backgroundColor: "var(--surface-hover)", color: "var(--text-muted)" }}>
                  <IconFlask />
                </span>
                <p className="text-xs uppercase tracking-widest m-0" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                  [ Sin resultados ]
                </p>
                <p className="text-sm m-0" style={{ color: "var(--text-dim)" }}>
                  Probá con otro término o quitá el filtro de dificultad.
                </p>
              </div>
            ) : (
              <div className="grid gap-4" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))" }}>
                <AnimatePresence>
                  {filtered.map((lab, i) => (
                    <motion.div
                      key={lab.id}
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.3, delay: Math.min(i * 0.04, 0.3) }}
                    >
                      <Link
                        to={`/laboratorios/${lab.id}`}
                        className="chamfer flex flex-col h-full p-4 sm:p-5 no-underline transition-colors group"
                        style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)", color: "inherit" }}
                        onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--border-amber)" }}
                        onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--border-default)" }}
                      >
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <span className="chamfer-sm flex items-center justify-center w-9 h-9 shrink-0" style={{ backgroundColor: "var(--surface-hover)", color: "var(--signal-cyan)" }}>
                            <IconFlask />
                          </span>
                          <span
                            className="text-[10px] font-bold px-2 py-0.5 chamfer-sm whitespace-nowrap uppercase tracking-wide"
                            style={{ backgroundColor: "color-mix(in srgb, " + DIFICULTAD_COLOR[lab.nivel_dificultad] + " 14%, transparent)", color: DIFICULTAD_COLOR[lab.nivel_dificultad], border: `1px solid ${DIFICULTAD_COLOR[lab.nivel_dificultad]}` }}
                          >
                            {DIFICULTAD_LABEL[lab.nivel_dificultad]}
                          </span>
                        </div>
                        <h3 className="text-sm sm:text-base font-bold mb-1.5" style={{ color: "var(--text-heading)" }}>
                          {lab.nombre}
                        </h3>
                        <p className="text-xs sm:text-sm leading-relaxed mb-3 flex-1" style={{ color: "var(--text-muted)" }}>
                          {lab.descripcion.length > 110 ? `${lab.descripcion.slice(0, 110)}…` : lab.descripcion}
                        </p>
                        {lab.temas.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 mb-3">
                            {lab.temas.slice(0, 3).map((t) => (
                              <span key={t} className="text-[10px] px-2 py-0.5" style={{ backgroundColor: "var(--surface-hover)", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                                {t}
                              </span>
                            ))}
                          </div>
                        )}
                        <span
                          className="inline-flex items-center gap-1 text-xs font-semibold mt-auto uppercase tracking-wide transition-transform group-hover:translate-x-0.5"
                          style={{ color: "var(--signal-amber)", fontFamily: "var(--font-mono)" }}
                        >
                          Ver detalle <IconArrowRight width={14} height={14} />
                        </span>
                      </Link>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            )}
          </div>
        </main>
        <Footer />
      </div>
    </div>
  )
}
