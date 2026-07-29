import { useEffect, useMemo, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  getInstructorDashboard,
  listStudents,
  listAssignments,
  ApiError,
  type InstructorDashboardItem,
  type EstudianteFiltrado,
  type Asignacion,
  type EstadoAsignacion,
} from "./api"
import Navbar from "../components/Navbar"
import Footer from "../components/Footer"

const ESTADO_COLORS: Record<EstadoAsignacion, string> = {
  pendiente: "#3B82F6",
  aceptada: "#22C55E",
  rechazada: "#EF4444",
  activa: "#22C55E",
  vencida: "#EF4444",
}

const ESTADO_LABELS: Record<EstadoAsignacion, string> = {
  pendiente: "Pendiente",
  aceptada: "Aceptada",
  rechazada: "Rechazada",
  activa: "Activa",
  vencida: "Vencida",
}

export default function InstructorDashboard() {
  const [labs, setLabs] = useState<InstructorDashboardItem[]>([])
  const [students, setStudents] = useState<EstudianteFiltrado[]>([])
  const [assignments, setAssignments] = useState<Asignacion[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  const PAGE_SIZE = 4
  const [page, setPage] = useState(0)

  useEffect(() => {
    let cancelled = false
    Promise.all([getInstructorDashboard(), listStudents(), listAssignments()])
      .then(([labsData, studentsData, assignmentsData]) => {
        if (cancelled) return
        setLabs(labsData)
        setStudents(studentsData)
        setAssignments(assignmentsData)
      })
      .catch((err) => {
        if (cancelled) return
        setError(err instanceof ApiError ? err.message : "No se pudo cargar el panel.")
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [])

  const labName = (id: string) => labs.find((l) => l.laboratorio_id === id)?.nombre || `Lab ${id.slice(0, 8)}`
  const studentName = (estudianteId: string, laboratorioId: string) =>
    students.find((s) => s.estudiante_id === estudianteId && s.laboratorio_id === laboratorioId)?.nombre_completo
    || students.find((s) => s.estudiante_id === estudianteId)?.nombre_completo
    || `Estudiante ${estudianteId.slice(0, 8)}`

  const invitaciones = useMemo(
    () => [...assignments].sort((a, b) => b.fecha_invitacion.localeCompare(a.fecha_invitacion)),
    [assignments],
  )

  const topEstudiantes = useMemo(
    () => [...students].sort((a, b) => b.porcentaje_completitud - a.porcentaje_completitud),
    [students],
  )
  const totalPages = Math.max(1, Math.ceil(topEstudiantes.length / PAGE_SIZE))
  const visible = topEstudiantes.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: "var(--bg-canvas)", color: "var(--text-base)" }}>
      <Navbar />
    <main className="flex-1">
      <div
        className="mx-auto px-4 sm:px-6 md:px-8 py-6 sm:py-8 md:py-10"
        style={{ maxWidth: "1200px" }}
      >
        {/* ══════════════════════════════════
            HEADER
            ══════════════════════════════════ */}
        <motion.header
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
          className="mb-8 sm:mb-10"
        >
          <h1
            className="text-2xl sm:text-3xl font-semibold m-0"
            style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}
          >
            Panel del Instructor
          </h1>
          <p className="text-xs sm:text-sm mt-1" style={{ color: "var(--text-muted)" }}>
            Gestioná tus laboratorios y estudiantes
          </p>
        </motion.header>

        <AnimatePresence>
          {error && (
            <motion.p
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="text-sm mb-6"
              style={{ color: "var(--accent-danger)" }}
            >
              {error}
            </motion.p>
          )}
        </AnimatePresence>

        {loading ? (
          <SkeletonBlock />
        ) : (
          <>
            {/* ══════════════════════════════════
                LABORATORIOS CREADOS
                ══════════════════════════════════ */}
            <section className="mb-8 sm:mb-10">
              <h2
                className="text-lg sm:text-xl font-semibold mb-4 sm:mb-5"
                style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}
              >
                Laboratorios Creados
              </h2>

              <div className="grid gap-3 sm:gap-4" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))" }}>
                {labs.map((lab, i) => {
                  const isPublished = lab.estado === "publicado"
                  return (
                    <motion.div
                      key={lab.laboratorio_id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, delay: i * 0.05 }}
                      className="flex flex-col p-4 sm:p-5 rounded-lg transition-colors"
                      style={{
                        backgroundColor: "var(--bg-surface)",
                        border: `1px solid ${isPublished ? "var(--ui-border-secondary)" : "var(--ui-border-default)"}`,
                      }}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <span className="text-sm sm:text-base font-medium leading-snug" style={{ color: "var(--text-heading)" }}>
                          {lab.nombre}
                        </span>
                        <span
                          className="text-xs font-medium px-2 py-0.5 rounded-full shrink-0 ml-3"
                          style={{
                            backgroundColor: isPublished ? "rgba(34,197,94,0.12)" : "rgba(148,163,184,0.15)",
                            color: isPublished ? "#22C55E" : "var(--text-muted)",
                            border: `1px solid ${isPublished ? "rgba(34,197,94,0.3)" : "transparent"}`,
                          }}
                        >
                          {isPublished ? "Publicado" : "Borrador"}
                        </span>
                      </div>

                      <div className="flex items-center gap-4 mt-auto text-xs" style={{ color: "var(--text-muted)" }}>
                        <span>
                          Estudiantes: <span style={{ color: "var(--text-base)" }}>{lab.estudiantes_inscritos}</span>
                        </span>
                        <span>
                          Completitud:{" "}
                          <span style={{ color: "var(--text-base)" }}>{Math.round(lab.porcentaje_completitud_promedio)}%</span>
                        </span>
                      </div>
                    </motion.div>
                  )
                })}

                {/* Card para crear nuevo (próximamente) */}
                <button
                  type="button"
                  title="Próximamente"
                  className="flex items-center justify-center p-4 sm:p-5 rounded-lg border-2 border-dashed cursor-not-allowed transition-colors opacity-60"
                  style={{ backgroundColor: "transparent", borderColor: "var(--ui-border-default)", color: "var(--text-muted)", minHeight: "120px" }}
                >
                  <div className="flex flex-col items-center gap-1">
                    <span className="text-lg font-medium">+</span>
                    <span className="text-xs font-medium" style={{ fontFamily: "'Fira Code', monospace" }}>
                      Nuevo Laboratorio
                    </span>
                  </div>
                </button>
              </div>
            </section>

            {/* ══════════════════════════════════
                INVITACIONES
                ══════════════════════════════════ */}
            <section className="mb-8 sm:mb-10">
              <h2
                className="text-lg sm:text-xl font-semibold mb-4 sm:mb-5"
                style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}
              >
                Invitaciones
              </h2>

              {invitaciones.length === 0 ? (
                <p className="text-sm" style={{ color: "var(--text-muted)" }}>Todavía no invitaste estudiantes.</p>
              ) : (
                <div className="rounded-lg overflow-x-auto" style={{ border: "1px solid var(--ui-border-default)" }}>
                  <table className="w-full border-collapse">
                    <thead>
                      <tr style={{ backgroundColor: "var(--bg-surface)" }}>
                        {["Estudiante", "Laboratorio", "Estado", "Fecha"].map((col) => (
                          <th
                            key={col}
                            className="text-left text-xs font-semibold px-3 sm:px-4 py-2.5 sm:py-3 whitespace-nowrap"
                            style={{ color: "var(--text-muted)", borderBottom: "1px solid var(--ui-border-default)", fontFamily: "'Fira Code', monospace" }}
                          >
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {invitaciones.slice(0, 12).map((inv) => (
                        <tr
                          key={inv.id}
                          style={{ borderBottom: "1px solid var(--ui-border-default)", backgroundColor: "var(--bg-canvas)" }}
                          className="transition-colors"
                          onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "var(--bg-surface-hover)" }}
                          onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "var(--bg-canvas)" }}
                        >
                          <td className="px-3 sm:px-4 py-2.5 sm:py-3 text-sm whitespace-nowrap" style={{ color: "var(--text-heading)" }}>
                            {studentName(inv.estudiante_id, inv.laboratorio_id)}
                          </td>
                          <td className="px-3 sm:px-4 py-2.5 sm:py-3 text-sm whitespace-nowrap" style={{ color: "var(--text-base)" }}>
                            {labName(inv.laboratorio_id)}
                          </td>
                          <td className="px-3 sm:px-4 py-2.5 sm:py-3 whitespace-nowrap">
                            <span
                              className="text-xs font-medium px-2 py-0.5 rounded-full"
                              style={{
                                backgroundColor: `${ESTADO_COLORS[inv.estado]}18`,
                                color: ESTADO_COLORS[inv.estado],
                                border: `1px solid ${ESTADO_COLORS[inv.estado]}40`,
                              }}
                            >
                              {ESTADO_LABELS[inv.estado]}
                            </span>
                          </td>
                          <td className="px-3 sm:px-4 py-2.5 sm:py-3 text-sm whitespace-nowrap" style={{ color: "var(--text-muted)", fontFamily: "'Fira Code', monospace" }}>
                            {new Date(inv.fecha_invitacion).toLocaleDateString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>

            {/* ══════════════════════════════════
                TOP ESTUDIANTES — carrusel funcional
                ══════════════════════════════════ */}
            <section>
              <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3 sm:gap-0 mb-5">
                <div>
                  <h2 className="text-lg sm:text-xl font-semibold" style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}>
                    Top Estudiantes
                  </h2>
                  <p className="text-xs sm:text-sm mt-1" style={{ color: "var(--text-muted)" }}>
                    Estudiantes ordenados por mayor avance
                  </p>
                </div>

                <div className="flex items-center gap-2 self-start sm:self-auto">
                  <CarouselButton label="Anterior" disabled={page === 0} onClick={() => setPage((p) => Math.max(0, p - 1))}>←</CarouselButton>
                  <span className="text-xs" style={{ color: "var(--text-muted)", fontFamily: "'Fira Code', monospace" }}>
                    {page + 1}/{totalPages}
                  </span>
                  <CarouselButton label="Siguiente" disabled={page >= totalPages - 1} onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}>→</CarouselButton>
                </div>
              </div>

              {topEstudiantes.length === 0 ? (
                <p className="text-sm" style={{ color: "var(--text-muted)" }}>Todavía no hay estudiantes inscritos.</p>
              ) : (
                <div className="grid gap-3 sm:gap-4 mb-5" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))" }}>
                  <AnimatePresence mode="popLayout">
                    {visible.map((s) => (
                      <motion.div
                        key={`${s.estudiante_id}-${s.laboratorio_id}`}
                        layout
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ duration: 0.25 }}
                        className="flex flex-col p-4 sm:p-5 rounded-lg"
                        style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--ui-border-default)" }}
                      >
                        <div
                          className="flex items-center justify-center w-10 h-10 rounded-full mb-3 text-sm font-bold shrink-0"
                          style={{ backgroundColor: "var(--bg-surface-hover)", color: "var(--text-muted)", fontFamily: "'Fira Code', monospace" }}
                        >
                          {s.nombre_completo.charAt(0).toUpperCase()}
                        </div>

                        <span className="text-sm sm:text-base font-medium" style={{ color: "var(--text-heading)" }}>
                          {s.nombre_completo}
                        </span>
                        <span className="text-xs mb-3 truncate" style={{ color: "var(--text-muted)" }}>
                          {labName(s.laboratorio_id)}
                        </span>

                        <div className="flex items-center justify-between mb-2">
                          <span className="text-xs" style={{ color: "var(--text-muted)" }}>Progreso</span>
                          <span
                            className="text-xs font-medium"
                            style={{ color: s.porcentaje_completitud >= 70 ? "#22C55E" : s.porcentaje_completitud >= 40 ? "#3B82F6" : "var(--text-muted)", fontFamily: "'Fira Code', monospace" }}
                          >
                            {Math.round(s.porcentaje_completitud)}%
                          </span>
                        </div>
                        <div className="w-full h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: "var(--bg-surface-hover)" }}>
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${s.porcentaje_completitud}%` }}
                            transition={{ duration: 0.5, ease: "easeOut" }}
                            className="h-full rounded-full"
                            style={{ backgroundColor: s.porcentaje_completitud >= 70 ? "#22C55E" : s.porcentaje_completitud >= 40 ? "#3B82F6" : "var(--text-muted)" }}
                          />
                        </div>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </main>
      <Footer />
    </div>
  )
}

function SkeletonBlock() {
  return (
    <div className="grid gap-3 sm:gap-4" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))" }}>
      {Array.from({ length: 4 }).map((_, i) => (
        <motion.div
          key={i}
          animate={{ opacity: [0.4, 0.8, 0.4] }}
          transition={{ duration: 1.4, repeat: Infinity, delay: i * 0.1 }}
          className="h-28 rounded-lg"
          style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--ui-border-default)" }}
        />
      ))}
    </div>
  )
}

/* ───────── Componente interno: botón de carrusel ───────── */
function CarouselButton({
  label,
  disabled,
  onClick,
  children,
}: {
  label: string
  disabled: boolean
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <button
      type="button"
      aria-label={label}
      disabled={disabled}
      onClick={onClick}
      className="flex items-center justify-center w-8 h-8 rounded text-sm cursor-pointer border transition-colors disabled:opacity-30 disabled:cursor-not-allowed shrink-0"
      style={{ backgroundColor: "transparent", borderColor: "var(--ui-border-default)", color: "var(--text-base)" }}
      onMouseEnter={(e) => {
        if (!disabled) {
          e.currentTarget.style.borderColor = "var(--ui-border-secondary)"
          e.currentTarget.style.backgroundColor = "var(--bg-surface-hover)"
        }
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = "var(--ui-border-default)"
        e.currentTarget.style.backgroundColor = "transparent"
      }}
    >
      {children}
    </button>
  )
}
