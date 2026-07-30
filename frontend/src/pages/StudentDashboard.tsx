import { useEffect, useMemo, useState, type ReactNode } from "react"
import { Link } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import {
  listAssignments,
  getLaboratorio,
  getHistory,
  acceptInvitation,
  rejectInvitation,
  ApiError,
  type Asignacion,
  type LaboratorioDetalle,
} from "./api"
import Navbar from "../components/Navbar"
import Footer from "../components/Footer"
import HeroBackground from "../components/HeroBackground"
import SectionHeading from "../components/SectionHeading"
import ProgressRing from "../components/ProgressRing"
import TerminalHeader from "../components/TerminalHeader"
import { IconGauge, IconFlask, IconClock, IconRocket, IconTrophy } from "../components/icons"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Label } from "../components/ui/label"
import { Textarea } from "../components/ui/textarea"
import { Skeleton } from "../components/ui/skeleton"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "../components/ui/dialog"
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "../components/ui/select"

type LabStatus = "completado" | "en_progreso" | "pendiente" | "vencida" | "rechazada"

interface LabRow {
  assignment: Asignacion
  laboratorio: LaboratorioDetalle | null
  status: LabStatus
  puntaje: number | null
}

const statusColor: Record<LabStatus, string> = {
  completado: "var(--signal-green)",
  en_progreso: "var(--signal-cyan)",
  pendiente: "var(--text-muted)",
  vencida: "var(--signal-red)",
  rechazada: "var(--text-muted)",
}
const statusLabel: Record<LabStatus, string> = {
  completado: "Completado",
  en_progreso: "En Progreso",
  pendiente: "Invitación pendiente",
  vencida: "Vencido",
  rechazada: "Rechazado",
}

export default function StudentDashboard() {
  const [rows, setRows] = useState<LabRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [busyId, setBusyId] = useState<string | null>(null)
  const [showInstructorModal, setShowInstructorModal] = useState(false)
  const [instructorForm, setInstructorForm] = useState({
    tipo: "",
    institucion: "",
    especialidades: "",
    motivacion: "",
  })

  const loadData = () => {
    setLoading(true)
    listAssignments()
      .then(async (assignments) => {
        const rowsData = await Promise.all(
          assignments
            .filter((a) => a.estado !== "rechazada")
            .map(async (a): Promise<LabRow> => {
              const laboratorio = await getLaboratorio(a.laboratorio_id).catch(() => null)
              let status: LabStatus
              let puntaje: number | null = null
              if (a.estado === "pendiente") {
                status = "pendiente"
              } else if (a.estado === "vencida") {
                status = "vencida"
              } else {
                const historial = await getHistory(a.id).catch(() => [])
                status = historial.length > 0 ? "completado" : "en_progreso"
                const puntajes = historial.map((h) => h.puntaje).filter((p): p is number => p != null)
                puntaje = puntajes.length > 0 ? Math.max(...puntajes) : null
              }
              return { assignment: a, laboratorio, status, puntaje }
            }),
        )
        setRows(rowsData)
      })
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "No se pudo cargar tu progreso.")
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => { loadData() }, [])

  const handleAccept = async (assignmentId: string) => {
    setBusyId(assignmentId)
    try {
      await acceptInvitation(assignmentId)
      loadData()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo aceptar la invitación.")
      setBusyId(null)
    }
  }

  const handleReject = async (assignmentId: string) => {
    setBusyId(assignmentId)
    try {
      await rejectInvitation(assignmentId)
      loadData()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo rechazar la invitación.")
      setBusyId(null)
    }
  }

  const completed = rows.filter((r) => r.status === "completado").length
  const inProgress = rows.filter((r) => r.status === "en_progreso").length
  const total = rows.length
  const pendingCount = total - completed - inProgress
  const pct = total > 0 ? Math.round((completed / total) * 100) : 0

  const calificaciones = useMemo(
    () =>
      rows
        .filter((r) => r.status === "completado")
        .sort((a, b) => (b.puntaje ?? -1) - (a.puntaje ?? -1)),
    [rows],
  )

  const proximosVencimientos = useMemo(
    () =>
      rows
        .filter((r) => r.status === "en_progreso" && r.assignment.fecha_vencimiento)
        .sort((a, b) => (a.assignment.fecha_vencimiento || "").localeCompare(b.assignment.fecha_vencimiento || "")),
    [rows],
  )

  return (
    <div className="relative min-h-screen overflow-hidden" style={{ backgroundColor: "var(--canvas)", color: "var(--text-base)" }}>
      <HeroBackground image="grim" imageOpacity={0.06} overlayOpacity={0.9} texture="grid" textureOpacity={0.03} />
      <div className="relative z-10 flex flex-col min-h-screen">
        <Navbar />
        <main className="flex-1">
          <div className="mx-auto px-4 sm:px-6 md:px-8 py-6 sm:py-8 md:py-10" style={{ maxWidth: "1200px" }}>
            <TerminalHeader title="Panel del Estudiante" subtitle="Bienvenido de vuelta" prompt="whoami → estudiante" />

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
                {/* ═══ PROGRESO ═══ */}
                <section className="mb-8 sm:mb-10">
                  <SectionHeading icon={<IconGauge />} title="Mi Progreso" subtitle="Tu avance general en la plataforma" />

                  <div className="chamfer flex flex-col sm:flex-row items-center gap-6 sm:gap-8 p-4 sm:p-6" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
                    <ProgressRing percent={pct} size={104} label="completado" />
                    <div className="flex-1 w-full grid grid-cols-3 gap-3 sm:gap-4">
                      <StatCard label="Completados" value={completed} color="var(--signal-green)" icon={<IconRocket />} />
                      <StatCard label="En Progreso" value={inProgress} color="var(--signal-cyan)" icon={<IconFlask />} />
                      <StatCard label="Pendientes" value={Math.max(0, pendingCount)} color="var(--text-muted)" icon={<IconClock />} />
                    </div>
                  </div>
                </section>

                {/* ═══ LABORATORIOS ASIGNADOS ═══ */}
                <section className="mb-8 sm:mb-10">
                  <div className="flex items-start justify-between gap-3 flex-wrap">
                    <SectionHeading icon={<IconFlask />} title="Laboratorios Asignados" />
                    <Link to="/laboratorios" className="text-xs sm:text-sm font-semibold no-underline uppercase tracking-wide transition-opacity hover:opacity-80" style={{ color: "var(--signal-amber)", fontFamily: "var(--font-mono)" }}>
                      Ver catálogo completo →
                    </Link>
                  </div>

                  {rows.length === 0 ? (
                    <div className="chamfer p-8 text-center" style={{ border: "1px dashed var(--border-strong)" }}>
                      <p className="text-xs uppercase tracking-widest m-0" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                        [ Sin laboratorios asignados ]
                      </p>
                    </div>
                  ) : (
                    <div className="flex flex-col gap-2 sm:gap-3">
                      <AnimatePresence>
                        {rows.map((row) => (
                          <motion.div
                            key={row.assignment.id}
                            layout
                            initial={{ opacity: 0, y: 8 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, height: 0 }}
                            className="chamfer flex items-center justify-between p-3 sm:p-4 transition-colors"
                            style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}
                          >
                            <div className="flex flex-col gap-1 min-w-0 pr-2">
                              <span className="text-sm sm:text-base font-bold truncate" style={{ color: "var(--text-heading)" }}>
                                {row.laboratorio?.nombre || `Lab ${row.assignment.laboratorio_id.slice(0, 8)}`}
                              </span>
                              {row.laboratorio && (
                                <span className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>
                                  Dificultad: {row.laboratorio.nivel_dificultad}
                                </span>
                              )}
                            </div>

                            <div className="flex items-center gap-2 sm:gap-3 shrink-0">
                              {row.status === "completado" && row.puntaje != null && (
                                <span className="text-[10px] font-bold px-2 py-1 chamfer-sm font-mono" style={{ backgroundColor: "rgba(255,176,32,0.1)", color: "var(--signal-amber)", border: "1px solid var(--border-amber)" }}>
                                  {Math.round(row.puntaje)}%
                                </span>
                              )}
                              <span
                                className="text-[10px] font-bold px-2 sm:px-2.5 py-1 chamfer-sm whitespace-nowrap uppercase tracking-wide"
                                style={{ backgroundColor: `color-mix(in srgb, ${statusColor[row.status]} 14%, transparent)`, color: statusColor[row.status], border: `1px solid ${statusColor[row.status]}` }}
                              >
                                {statusLabel[row.status]}
                              </span>
                              {row.status === "pendiente" && (
                                <>
                                  <Button size="sm" disabled={busyId === row.assignment.id} onClick={() => handleAccept(row.assignment.id)} className="chamfer-sm font-mono text-xs uppercase">
                                    Aceptar
                                  </Button>
                                  <Button size="sm" variant="outline" disabled={busyId === row.assignment.id} onClick={() => handleReject(row.assignment.id)} className="chamfer-sm font-mono text-xs uppercase">
                                    Rechazar
                                  </Button>
                                </>
                              )}
                              {(row.status === "en_progreso" || row.status === "completado") && (
                                <Button asChild size="sm" className="chamfer-sm font-mono text-xs uppercase">
                                  <Link to={`/resolver/${row.assignment.id}`}>{row.status === "completado" ? "Ver" : "Continuar"}</Link>
                                </Button>
                              )}
                            </div>
                          </motion.div>
                        ))}
                      </AnimatePresence>
                    </div>
                  )}
                </section>

                {/* ═══ CALIFICACIONES ═══ */}
                <section className="mb-8 sm:mb-10">
                  <SectionHeading icon={<IconTrophy />} title="Mis Calificaciones" subtitle="Mejor puntaje obtenido en cada laboratorio completado" />

                  {calificaciones.length === 0 ? (
                    <div className="chamfer p-6 sm:p-8 text-center" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
                      <p className="text-sm m-0" style={{ color: "var(--text-muted)" }}>Todavía no completaste ningún laboratorio.</p>
                    </div>
                  ) : (
                    <div className="flex flex-col gap-2 sm:gap-3">
                      {calificaciones.map((row) => {
                        const puntaje = row.puntaje
                        const color = puntaje == null ? "var(--text-muted)" : puntaje >= 70 ? "var(--signal-green)" : puntaje >= 40 ? "var(--signal-cyan)" : "var(--signal-red)"
                        return (
                          <div key={row.assignment.id} className="chamfer flex items-center justify-between gap-3 p-3 sm:p-4" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
                            <div className="flex flex-col gap-1 min-w-0 pr-2">
                              <span className="text-sm sm:text-base font-bold truncate" style={{ color: "var(--text-heading)" }}>
                                {row.laboratorio?.nombre || `Lab ${row.assignment.laboratorio_id.slice(0, 8)}`}
                              </span>
                              {row.laboratorio && (
                                <span className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>Dificultad: {row.laboratorio.nivel_dificultad}</span>
                              )}
                            </div>
                            <div className="flex items-center gap-3 shrink-0">
                              <span className="text-xl sm:text-2xl font-bold text-display" style={{ color }}>
                                {puntaje != null ? `${Math.round(puntaje)}%` : "—"}
                              </span>
                              <Link to={`/resolver/${row.assignment.id}`} className="text-xs font-semibold no-underline uppercase tracking-wide" style={{ color: "var(--signal-cyan)", fontFamily: "var(--font-mono)" }}>
                                Ver →
                              </Link>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </section>

                {/* ═══ VENCIMIENTOS ═══ */}
                <section className="mb-8 sm:mb-10">
                  <SectionHeading icon={<IconClock />} title="Próximos Vencimientos" />

                  {proximosVencimientos.length === 0 ? (
                    <div className="chamfer p-6 sm:p-8 text-center" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
                      <p className="text-sm m-0" style={{ color: "var(--text-muted)" }}>No tienes laboratorios por vencer.</p>
                    </div>
                  ) : (
                    <div className="flex flex-col gap-2 sm:gap-3">
                      {proximosVencimientos.map((row) => (
                        <div key={row.assignment.id} className="chamfer flex items-center justify-between p-3 sm:p-4" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-amber)" }}>
                          <div className="flex flex-col gap-1 min-w-0 pr-2">
                            <span className="text-sm sm:text-base font-bold truncate" style={{ color: "var(--text-heading)" }}>
                              {row.laboratorio?.nombre || `Lab ${row.assignment.laboratorio_id.slice(0, 8)}`}
                            </span>
                            <span className="text-xs font-mono" style={{ color: "var(--signal-red)" }}>
                              Vence: {new Date(row.assignment.fecha_vencimiento!).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </section>

                {/* ═══ INSTRUCTOR CTA ═══ */}
                <section>
                  <div className="chamfer flex flex-col sm:flex-row items-start sm:items-center justify-between p-5 sm:p-6 gap-4 sm:gap-6" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-strong)" }}>
                    <div className="flex flex-col gap-1" style={{ maxWidth: "600px" }}>
                      <h2 className="flex items-center gap-2 text-base sm:text-lg font-bold uppercase tracking-wide m-0" style={{ color: "var(--text-heading)" }}>
                        <IconRocket style={{ color: "var(--signal-amber)" }} />
                        ¿Listo para el siguiente nivel?
                      </h2>
                      <p className="text-xs sm:text-sm m-0 leading-relaxed" style={{ color: "var(--text-muted)" }}>
                        Como Instructor puedes crear tus propios laboratorios con secciones, flags y exámenes,
                        copiar laboratorios predeterminados para personalizarlos, invitar estudiantes y
                        hacer seguimiento de su progreso. Tu progreso actual como estudiante se conserva.
                      </p>
                    </div>

                    <Button onClick={() => setShowInstructorModal(true)} className="w-full sm:w-auto chamfer-sm font-mono text-xs uppercase tracking-wide">
                      Convertirme en Instructor
                    </Button>
                  </div>
                </section>
              </>
            )}
          </div>
        </main>
        <Footer />
      </div>

      <InstructorRegistrationModal
        open={showInstructorModal}
        form={instructorForm}
        onChange={setInstructorForm}
        onClose={() => setShowInstructorModal(false)}
      />
    </div>
  )
}

function StatCard({ label, value, color, icon }: { label: string; value: number; color: string; icon?: ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className="chamfer-sm flex-1 flex flex-col items-center gap-1.5 sm:gap-2 p-3 sm:p-5"
      style={{ backgroundColor: "var(--canvas)", border: "1px solid var(--border-default)" }}
    >
      {icon && (
        <div className="chamfer-sm flex items-center justify-center w-7 h-7 sm:w-8 sm:h-8" style={{ backgroundColor: `color-mix(in srgb, ${color} 14%, transparent)`, color }}>
          {icon}
        </div>
      )}
      <span className="text-xl sm:text-3xl font-bold text-display" style={{ color }}>
        {value}
      </span>
      <span className="text-[11px] sm:text-xs font-medium text-center uppercase tracking-wide" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>{label}</span>
    </motion.div>
  )
}

function SkeletonBlock() {
  return (
    <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
      {Array.from({ length: 3 }).map((_, i) => (
        <Skeleton key={i} className="chamfer flex-1 h-24" style={{ backgroundColor: "var(--surface)" }} />
      ))}
    </div>
  )
}

/* ───────── MODAL REGISTRO INSTRUCTOR ───────── */
const TIPOS_INSTRUCTOR = [
  { value: "profesor", label: "Profesor Universitario" },
  { value: "capacitador", label: "Capacitador Corporativo" },
  { value: "investigador", label: "Investigador" },
  { value: "independiente", label: "Independiente / Freelancer" },
]

function InstructorRegistrationModal({
  open,
  form,
  onChange,
  onClose,
}: {
  open: boolean
  form: { tipo: string; institucion: string; especialidades: string; motivacion: string }
  onChange: (f: typeof form) => void
  onClose: () => void
}) {
  const [sent, setSent] = useState(false)
  const update = (field: keyof typeof form, value: string) => onChange({ ...form, [field]: value })

  return (
    <Dialog open={open} onOpenChange={(next) => { if (!next) { onClose(); setSent(false) } }}>
      <DialogContent className="chamfer sm:max-w-lg" style={{ backgroundColor: "var(--canvas-raised)", border: "1px solid var(--border-default)" }}>
        <DialogHeader>
          <DialogTitle className="text-lg font-bold uppercase tracking-wide" style={{ color: "var(--text-heading)" }}>
            Registro de Instructor
          </DialogTitle>
          {!sent && (
            <DialogDescription>
              Cuéntanos sobre ti para registrarte como instructor. Estos datos ayudarán a personalizar tu experiencia.
            </DialogDescription>
          )}
        </DialogHeader>

        {sent ? (
          <div className="flex flex-col items-center gap-3 py-6 text-center">
            <p className="text-sm" style={{ color: "var(--text-base)" }}>
              Tu solicitud fue registrada. Un administrador debe aprobar el cambio de rol —
              todavía no existe un flujo automático de autoservicio para esto.
            </p>
            <Button onClick={onClose} className="chamfer-sm font-mono text-xs uppercase">Entendido</Button>
          </div>
        ) : (
          <>
            <div className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <Label className="text-xs uppercase tracking-wide" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                  Tipo de Instructor <span style={{ color: "var(--signal-red)" }}>*</span>
                </Label>
                <Select value={form.tipo} onValueChange={(v) => update("tipo", v)}>
                  <SelectTrigger className="chamfer-sm w-full h-10">
                    <SelectValue placeholder="Selecciona un tipo" />
                  </SelectTrigger>
                  <SelectContent>
                    {TIPOS_INSTRUCTOR.map((t) => (
                      <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="flex flex-col gap-1.5">
                <Label className="text-xs uppercase tracking-wide" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>Institución / Afiliación</Label>
                <Input value={form.institucion} onChange={(e) => update("institucion", e.target.value)} placeholder="Ej: Universidad Nacional de Colombia" className="chamfer-sm h-10" />
              </div>

              <div className="flex flex-col gap-1.5">
                <Label className="text-xs uppercase tracking-wide" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>Áreas de Especialización</Label>
                <Input value={form.especialidades} onChange={(e) => update("especialidades", e.target.value)} placeholder="Ej: Seguridad Web, Redes, Forense" className="chamfer-sm h-10" />
              </div>

              <div className="flex flex-col gap-1.5">
                <Label className="text-xs uppercase tracking-wide" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>¿Por qué quieres ser instructor?</Label>
                <Textarea value={form.motivacion} onChange={(e) => update("motivacion", e.target.value)} placeholder="Cuéntanos qué te motiva a crear laboratorios y guiar a otros estudiantes…" rows={3} className="chamfer-sm resize-none" />
              </div>
            </div>

            <DialogFooter className="chamfer-t" style={{ backgroundColor: "var(--surface)" }}>
              <Button variant="outline" onClick={onClose} className="chamfer-sm font-mono text-xs uppercase">Cancelar</Button>
              <Button onClick={() => setSent(true)} disabled={!form.tipo} className="chamfer-sm font-mono text-xs uppercase">
                Registrarme como Instructor
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
