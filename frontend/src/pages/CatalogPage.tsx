import { useEffect, useMemo, useState } from "react"
import { Link } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import { getCatalogo, ApiError, type LaboratorioListItem, type NivelDificultad } from "./api"
import Navbar from "../components/Navbar"
import Footer from "../components/Footer"
import SectionHeading from "../components/SectionHeading"
import { IconFlask, IconSearch, IconArrowRight } from "../components/icons"

// Catálogo público de laboratorios (HV-02 del backend) — antes solo se veían
// los labs ya asignados por un instructor; esta vista muestra el "roadmap"
// completo de laboratorios publicados, visible sin necesidad de invitación,
// tanto para visitantes anónimos como para cualquier usuario logueado.
const DIFICULTAD_LABEL: Record<NivelDificultad, string> = {
  basico: "Básico",
  intermedio: "Intermedio",
  avanzado: "Avanzado",
}
const DIFICULTAD_COLOR: Record<NivelDificultad, string> = {
  basico: "#22C55E",
  intermedio: "#F59E0B",
  avanzado: "#EF4444",
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
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: "var(--bg-canvas)", color: "var(--text-base)" }}>
      <Navbar />
      <main className="flex-1">
        <div className="mx-auto px-4 sm:px-6 md:px-8 py-8 sm:py-10 md:py-12" style={{ maxWidth: "1200px" }}>
          <motion.header
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35 }}
            className="mb-6 sm:mb-8"
          >
            <h1 className="text-2xl sm:text-3xl font-semibold m-0" style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}>
              Catálogo de Laboratorios
            </h1>
            <p className="text-xs sm:text-sm mt-1 max-w-2xl" style={{ color: "var(--text-muted)" }}>
              Este es el roadmap completo de laboratorios de GAIA: no hace falta esperar una invitación
              para ver qué hay disponible. Iniciá sesión para inscribirte en cualquiera de ellos.
            </p>
          </motion.header>

          {/* Filtros */}
          <div className="flex flex-col sm:flex-row gap-3 mb-6 sm:mb-8">
            <div
              className="flex items-center gap-2 flex-1 px-3.5 py-2.5 rounded"
              style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--ui-border-default)" }}
            >
              <IconSearch style={{ color: "var(--text-muted)" }} />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Buscar por nombre o tema..."
                className="flex-1 bg-transparent border-none outline-none text-sm"
                style={{ color: "var(--text-base)", fontFamily: "'Fira Sans', sans-serif" }}
              />
            </div>
            <div className="flex gap-2">
              {(["", "basico", "intermedio", "avanzado"] as const).map((d) => (
                <button
                  key={d || "todos"}
                  type="button"
                  onClick={() => setDificultad(d)}
                  className="px-3 sm:px-4 py-2 rounded text-xs sm:text-sm font-medium cursor-pointer transition-colors whitespace-nowrap"
                  style={{
                    backgroundColor: dificultad === d ? "var(--accent-primary)" : "var(--bg-surface)",
                    color: dificultad === d ? "#fff" : "var(--text-muted)",
                    border: `1px solid ${dificultad === d ? "var(--accent-primary)" : "var(--ui-border-default)"}`,
                    fontFamily: "'Fira Code', monospace",
                  }}
                >
                  {d ? DIFICULTAD_LABEL[d] : "Todos"}
                </button>
              ))}
            </div>
          </div>

          <AnimatePresence>
            {error && (
              <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="text-sm mb-6" style={{ color: "var(--accent-danger)" }}>
                {error}
              </motion.p>
            )}
          </AnimatePresence>

          {loading ? (
            <div className="grid gap-4" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))" }}>
              {Array.from({ length: 6 }).map((_, i) => (
                <motion.div
                  key={i}
                  animate={{ opacity: [0.4, 0.8, 0.4] }}
                  transition={{ duration: 1.4, repeat: Infinity, delay: i * 0.08 }}
                  className="h-40 rounded-lg"
                  style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--ui-border-default)" }}
                />
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <div className="p-8 sm:p-12 rounded-lg text-center" style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--ui-border-default)" }}>
              <SectionHeading icon={<IconFlask />} title="Sin resultados" subtitle="Probá con otro término o quitá el filtro de dificultad." />
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
                      className="flex flex-col h-full p-4 sm:p-5 rounded-lg no-underline transition-colors group"
                      style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--ui-border-default)", color: "inherit" }}
                      onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--accent-primary)" }}
                      onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--ui-border-default)" }}
                    >
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <span
                          className="flex items-center justify-center w-9 h-9 rounded-md shrink-0"
                          style={{ backgroundColor: "var(--bg-surface-hover)", color: "var(--accent-primary)" }}
                        >
                          <IconFlask />
                        </span>
                        <span
                          className="text-[11px] font-medium px-2 py-0.5 rounded-full whitespace-nowrap"
                          style={{
                            backgroundColor: `${DIFICULTAD_COLOR[lab.nivel_dificultad]}18`,
                            color: DIFICULTAD_COLOR[lab.nivel_dificultad],
                            border: `1px solid ${DIFICULTAD_COLOR[lab.nivel_dificultad]}40`,
                          }}
                        >
                          {DIFICULTAD_LABEL[lab.nivel_dificultad]}
                        </span>
                      </div>
                      <h3 className="text-sm sm:text-base font-semibold mb-1.5" style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}>
                        {lab.nombre}
                      </h3>
                      <p className="text-xs sm:text-sm leading-relaxed mb-3 flex-1" style={{ color: "var(--text-muted)" }}>
                        {lab.descripcion.length > 110 ? `${lab.descripcion.slice(0, 110)}…` : lab.descripcion}
                      </p>
                      {lab.temas.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 mb-3">
                          {lab.temas.slice(0, 3).map((t) => (
                            <span key={t} className="text-[10px] px-2 py-0.5 rounded-full" style={{ backgroundColor: "var(--bg-surface-hover)", color: "var(--text-muted)" }}>
                              {t}
                            </span>
                          ))}
                        </div>
                      )}
                      <span
                        className="inline-flex items-center gap-1 text-xs font-semibold mt-auto transition-transform group-hover:translate-x-0.5"
                        style={{ color: "var(--accent-primary)", fontFamily: "'Fira Code', monospace" }}
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
  )
}
