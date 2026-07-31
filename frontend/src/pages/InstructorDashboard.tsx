import { useEffect, useMemo, useState, type ReactNode } from "react"
import { Link } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import {
  getInstructorDashboard,
  listStudents,
  listAssignments,
  setCatalogVisibility,
  ApiError,
  type InstructorDashboardItem,
  type EstudianteFiltrado,
  type Asignacion,
  type EstadoAsignacion,
  type EstadoLaboratorio,
} from "./api"
import Navbar from "../components/Navbar"
import Footer from "../components/Footer"
import HeroBackground from "../components/HeroBackground"
import SectionHeading from "../components/SectionHeading"
import TerminalHeader from "../components/TerminalHeader"
import TiltCard from "../components/TiltCard"
import { IconFlask, IconMail, IconTrophy, IconGlobe } from "../components/icons"
import { Skeleton } from "../components/ui/skeleton"
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "../components/ui/table"

const ESTADO_COLORS: Record<EstadoAsignacion, string> = {
  pendiente: "var(--signal-cyan)",
  aceptada: "var(--signal-green)",
  rechazada: "var(--signal-red)",
  activa: "var(--signal-green)",
  vencida: "var(--signal-red)",
}

const ESTADO_LABELS: Record<EstadoAsignacion, string> = {
  pendiente: "Pendiente",
  aceptada: "Aceptada",
  rechazada: "Rechazada",
  activa: "Activa",
  vencida: "Vencida",
}

const LAB_ESTADO_LABELS: Record<EstadoLaboratorio, string> = {
  borrador: "Borrador",
  en_revision: "En revisión",
  publicado: "Publicado",
}

const LAB_ESTADO_COLORS: Record<EstadoLaboratorio, string> = {
  borrador: "var(--text-muted)",
  en_revision: "var(--signal-amber)",
  publicado: "var(--signal-green)",
}

const LAB_ESTADO_GLOW: Record<EstadoLaboratorio, string> = {
  borrador: "136,146,163",
  en_revision: "255,176,32",
  publicado: "51,214,159",
}

export default function InstructorDashboard() {
  const [labs, setLabs] = useState<InstructorDashboardItem[]>([])
  const [students, setStudents] = useState<EstudianteFiltrado[]>([])
  const [assignments, setAssignments] = useState<Asignacion[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [visibilityBusyId, setVisibilityBusyId] = useState<string | null>(null)

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

  const handleToggleVisibility = async (laboratorioId: string, next: boolean) => {
    setVisibilityBusyId(laboratorioId)
    try {
      await setCatalogVisibility(laboratorioId, next)
      setLabs((prev) =>
        prev.map((l) => (l.laboratorio_id === laboratorioId ? { ...l, visible_en_catalogo: next } : l)),
      )
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo actualizar la visibilidad en el catálogo.")
    } finally {
      setVisibilityBusyId(null)
    }
  }

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
    <div className="relative min-h-screen overflow-hidden" style={{ backgroundColor: "var(--canvas)", color: "var(--text-base)" }}>
      <HeroBackground image="term" imageOpacity={0.06} overlayOpacity={0.9} texture="grid" textureOpacity={0.03} />
      <div className="relative z-10 flex flex-col min-h-screen">
        <Navbar />
        <main className="flex-1">
          <div className="mx-auto px-4 sm:px-6 md:px-8 py-6 sm:py-8 md:py-10" style={{ maxWidth: "1200px" }}>
            <TerminalHeader title="Panel del Instructor" subtitle="Gestiona tus laboratorios y estudiantes" prompt="whoami → instructor" />

            <AnimatePresence>
              {error && (
                <motion.p initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="text-sm mb-6 px-3 py-2 chamfer-sm" style={{ color: "var(--signal-red)", backgroundColor: "rgba(255,71,87,0.08)", border: "1px solid var(--signal-red-dim)" }} role="alert">
                  ▲ {error}
                </motion.p>
              )}
            </AnimatePresence>

            {loading ? (
              <SkeletonBlock />
            ) : (
              <>
                {/* ═══ LABORATORIOS CREADOS ═══ */}
                <section className="mb-8 sm:mb-10">
                  <SectionHeading icon={<IconFlask />} title="Laboratorios Creados" />

                  <div className="grid gap-3 sm:gap-4" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))" }}>
                    {labs.map((lab, i) => {
                      const color = LAB_ESTADO_COLORS[lab.estado]
                      return (
                        <motion.div
                          key={lab.laboratorio_id}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ duration: 0.3, delay: i * 0.05 }}
                        >
                          <TiltCard
                            glowColor={LAB_ESTADO_GLOW[lab.estado]}
                            className="chamfer flex flex-col p-4 sm:p-5 h-full"
                            style={{ backgroundColor: "var(--surface)", border: `1px solid ${lab.estado === "publicado" ? "var(--border-strong)" : "var(--border-default)"}` }}
                          >
                            <div className="flex items-start justify-between mb-3">
                              <span className="text-sm sm:text-base font-bold leading-snug" style={{ color: "var(--text-heading)" }}>
                                {lab.nombre}
                              </span>
                              <span
                                className="text-[10px] font-bold px-2 py-0.5 chamfer-sm shrink-0 ml-3 uppercase tracking-wide"
                                style={{
                                  backgroundColor: `color-mix(in srgb, ${color} 12%, transparent)`,
                                  color,
                                  border: `1px solid ${color}`,
                                }}
                              >
                                {LAB_ESTADO_LABELS[lab.estado]}
                              </span>
                            </div>

                            <div className="flex items-center gap-4 mb-3 text-xs font-mono" style={{ color: "var(--text-muted)" }}>
                              <span>Estudiantes: <span style={{ color: "var(--text-base)" }}>{lab.estudiantes_inscritos}</span></span>
                              <span>Completitud: <span style={{ color: "var(--text-base)" }}>{Math.round(lab.porcentaje_completitud_promedio)}%</span></span>
                            </div>

                            {lab.estado === "publicado" && (
                              <button
                                type="button"
                                disabled={visibilityBusyId === lab.laboratorio_id}
                                onClick={() => handleToggleVisibility(lab.laboratorio_id, !lab.visible_en_catalogo)}
                                className="mt-auto flex items-center gap-2 chamfer-sm px-2.5 py-1.5 text-[11px] font-semibold uppercase tracking-wide cursor-pointer border transition-colors disabled:opacity-50 disabled:cursor-wait"
                                style={{
                                  backgroundColor: lab.visible_en_catalogo ? "rgba(51,214,159,0.1)" : "transparent",
                                  borderColor: lab.visible_en_catalogo ? "var(--signal-green)" : "var(--border-default)",
                                  color: lab.visible_en_catalogo ? "var(--signal-green)" : "var(--text-muted)",
                                  fontFamily: "var(--font-mono)",
                                }}
                              >
                                <IconGlobe width={13} height={13} />
                                {visibilityBusyId === lab.laboratorio_id
                                  ? "Actualizando…"
                                  : lab.visible_en_catalogo
                                    ? "En catálogo público"
                                    : "Publicar en catálogo"}
                              </button>
                            )}
                          </TiltCard>
                        </motion.div>
                      )
                    })}

                    <Link
                      to="/laboratorios/nuevo"
                      className="chamfer flex items-center justify-center p-4 sm:p-5 transition-colors no-underline"
                      style={{ backgroundColor: "transparent", border: "2px dashed var(--border-default)", color: "var(--text-muted)", minHeight: "120px" }}
                      onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--signal-amber)"; e.currentTarget.style.color = "var(--signal-amber)" }}
                      onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--border-default)"; e.currentTarget.style.color = "var(--text-muted)" }}
                    >
                      <div className="flex flex-col items-center gap-1">
                        <span className="text-lg font-medium">+</span>
                        <span className="text-xs font-medium uppercase tracking-wide" style={{ fontFamily: "var(--font-mono)" }}>
                          Nuevo Laboratorio
                        </span>
                      </div>
                    </Link>
                  </div>
                </section>

                {/* ═══ INVITACIONES ═══ */}
                <section className="mb-8 sm:mb-10">
                  <SectionHeading icon={<IconMail />} title="Invitaciones" />

                  {invitaciones.length === 0 ? (
                    <div className="chamfer p-8 text-center" style={{ border: "1px dashed var(--border-strong)" }}>
                      <p className="text-xs uppercase tracking-widest m-0" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                        [ Todavía no invitaste estudiantes ]
                      </p>
                    </div>
                  ) : (
                    <div className="chamfer overflow-hidden" style={{ border: "1px solid var(--border-default)", backgroundColor: "var(--surface)" }}>
                      <Table>
                        <TableHeader>
                          <TableRow style={{ backgroundColor: "var(--surface-hover)", borderColor: "var(--border-default)" }}>
                            {["Estudiante", "Laboratorio", "Estado", "Fecha"].map((col) => (
                              <TableHead key={col} className="text-[11px] uppercase tracking-wider" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                                {col}
                              </TableHead>
                            ))}
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {invitaciones.slice(0, 12).map((inv) => (
                            <TableRow key={inv.id} style={{ borderColor: "var(--border-default)" }}>
                              <TableCell className="text-sm" style={{ color: "var(--text-heading)" }}>
                                {studentName(inv.estudiante_id, inv.laboratorio_id)}
                              </TableCell>
                              <TableCell className="text-sm" style={{ color: "var(--text-base)" }}>
                                {labName(inv.laboratorio_id)}
                              </TableCell>
                              <TableCell>
                                <span
                                  className="text-[10px] font-bold px-2 py-0.5 chamfer-sm uppercase tracking-wide"
                                  style={{ backgroundColor: `color-mix(in srgb, ${ESTADO_COLORS[inv.estado]} 14%, transparent)`, color: ESTADO_COLORS[inv.estado], border: `1px solid ${ESTADO_COLORS[inv.estado]}` }}
                                >
                                  {ESTADO_LABELS[inv.estado]}
                                </span>
                              </TableCell>
                              <TableCell className="text-sm font-mono" style={{ color: "var(--text-muted)" }}>
                                {new Date(inv.fecha_invitacion).toLocaleDateString()}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  )}
                </section>

                {/* ═══ TOP ESTUDIANTES ═══ */}
                <section>
                  <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3 sm:gap-0 mb-5">
                    <SectionHeading icon={<IconTrophy />} title="Top Estudiantes" subtitle="Estudiantes ordenados por mayor avance" />

                    <div className="flex items-center gap-2 self-start sm:self-auto">
                      <CarouselButton label="Anterior" disabled={page === 0} onClick={() => setPage((p) => Math.max(0, p - 1))}>←</CarouselButton>
                      <span className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>{page + 1}/{totalPages}</span>
                      <CarouselButton label="Siguiente" disabled={page >= totalPages - 1} onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}>→</CarouselButton>
                    </div>
                  </div>

                  {topEstudiantes.length === 0 ? (
                    <div className="chamfer p-8 text-center" style={{ border: "1px dashed var(--border-strong)" }}>
                      <p className="text-xs uppercase tracking-widest m-0" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                        [ Sin estudiantes inscritos ]
                      </p>
                    </div>
                  ) : (
                    <div className="grid gap-3 sm:gap-4 mb-5" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))" }}>
                      <AnimatePresence mode="popLayout">
                        {visible.map((s) => {
                          const barColor = s.porcentaje_completitud >= 70 ? "var(--signal-green)" : s.porcentaje_completitud >= 40 ? "var(--signal-cyan)" : "var(--text-muted)"
                          return (
                            <motion.div
                              key={`${s.estudiante_id}-${s.laboratorio_id}`}
                              layout
                              initial={{ opacity: 0, y: 10 }}
                              animate={{ opacity: 1, y: 0 }}
                              exit={{ opacity: 0, y: -10 }}
                              transition={{ duration: 0.25 }}
                            >
                              <TiltCard glowColor="255,176,32" className="chamfer flex flex-col p-4 sm:p-5 h-full" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
                                <div className="chamfer-sm flex items-center justify-center w-10 h-10 mb-3 text-sm font-bold shrink-0" style={{ backgroundColor: "var(--surface-hover)", color: "var(--signal-amber)", fontFamily: "var(--font-mono)" }}>
                                  {s.nombre_completo.charAt(0).toUpperCase()}
                                </div>

                                <span className="text-sm sm:text-base font-bold" style={{ color: "var(--text-heading)" }}>{s.nombre_completo}</span>
                                <span className="text-xs mb-3 truncate" style={{ color: "var(--text-muted)" }}>{labName(s.laboratorio_id)}</span>

                                <div className="flex items-center justify-between mb-2">
                                  <span className="text-xs uppercase tracking-wide" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>Progreso</span>
                                  <span className="text-xs font-bold" style={{ color: barColor, fontFamily: "var(--font-mono)" }}>{Math.round(s.porcentaje_completitud)}%</span>
                                </div>
                                <div className="w-full h-1.5 overflow-hidden" style={{ backgroundColor: "var(--surface-hover)" }}>
                                  <motion.div initial={{ width: 0 }} animate={{ width: `${s.porcentaje_completitud}%` }} transition={{ duration: 0.5, ease: "easeOut" }} className="h-full" style={{ backgroundColor: barColor }} />
                                </div>
                              </TiltCard>
                            </motion.div>
                          )
                        })}
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
    </div>
  )
}

function SkeletonBlock() {
  return (
    <div className="grid gap-3 sm:gap-4" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))" }}>
      {Array.from({ length: 4 }).map((_, i) => (
        <Skeleton key={i} className="chamfer h-28" style={{ backgroundColor: "var(--surface)" }} />
      ))}
    </div>
  )
}

function CarouselButton({ label, disabled, onClick, children }: { label: string; disabled: boolean; onClick: () => void; children: ReactNode }) {
  return (
    <button
      type="button"
      aria-label={label}
      disabled={disabled}
      onClick={onClick}
      className="chamfer-sm flex items-center justify-center w-8 h-8 text-sm cursor-pointer border transition-colors disabled:opacity-30 disabled:cursor-not-allowed shrink-0"
      style={{ backgroundColor: "transparent", borderColor: "var(--border-default)", color: "var(--text-base)" }}
      onMouseEnter={(e) => { if (!disabled) { e.currentTarget.style.borderColor = "var(--signal-amber)"; e.currentTarget.style.backgroundColor = "var(--surface-hover)" } }}
      onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--border-default)"; e.currentTarget.style.backgroundColor = "transparent" }}
    >
      {children}
    </button>
  )
}
