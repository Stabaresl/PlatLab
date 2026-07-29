import { useEffect, useMemo, useState } from "react"
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
import SectionHeading from "../components/SectionHeading"
import ProgressRing from "../components/ProgressRing"
import { IconGauge, IconFlask, IconClock, IconRocket } from "../components/icons"

type LabStatus = "completado" | "en_progreso" | "pendiente" | "vencida" | "rechazada"

interface LabRow {
  assignment: Asignacion
  laboratorio: LaboratorioDetalle | null
  status: LabStatus
}

const statusColor: Record<LabStatus, string> = {
  completado: "#22C55E",
  en_progreso: "#3B82F6",
  pendiente: "#94A3B8",
  vencida: "#EF4444",
  rechazada: "#94A3B8",
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
              if (a.estado === "pendiente") {
                status = "pendiente"
              } else if (a.estado === "vencida") {
                status = "vencida"
              } else {
                const historial = await getHistory(a.id).catch(() => [])
                status = historial.length > 0 ? "completado" : "en_progreso"
              }
              return { assignment: a, laboratorio, status }
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

  const proximosVencimientos = useMemo(
    () =>
      rows
        .filter((r) => r.status === "en_progreso" && r.assignment.fecha_vencimiento)
        .sort((a, b) => (a.assignment.fecha_vencimiento || "").localeCompare(b.assignment.fecha_vencimiento || "")),
    [rows],
  )

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
            Panel del Estudiante
          </h1>
          <p className="text-xs sm:text-sm mt-1" style={{ color: "var(--text-muted)" }}>
            Bienvenido de vuelta
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
                PROGRESO — 3 tarjetas + barra
                ══════════════════════════════════ */}
            <section className="mb-8 sm:mb-10">
              <SectionHeading icon={<IconGauge />} title="Mi Progreso" subtitle="Tu avance general en la plataforma" />

              <div
                className="flex flex-col sm:flex-row items-center gap-6 sm:gap-8 p-4 sm:p-6 rounded-lg"
                style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--ui-border-default)" }}
              >
                <ProgressRing percent={pct} size={104} label="completado" />
                <div className="flex-1 w-full grid grid-cols-3 gap-3 sm:gap-4">
                  <StatCard label="Completados" value={completed} color="#22C55E" icon={<IconRocket />} />
                  <StatCard label="En Progreso" value={inProgress} color="#3B82F6" icon={<IconFlask />} />
                  <StatCard label="Pendientes" value={Math.max(0, pendingCount)} color="#94A3B8" icon={<IconClock />} />
                </div>
              </div>
            </section>

            {/* ══════════════════════════════════
                LABORATORIOS ASIGNADOS
                ══════════════════════════════════ */}
            <section className="mb-8 sm:mb-10">
              <SectionHeading icon={<IconFlask />} title="Laboratorios Asignados" />

              {rows.length === 0 ? (
                <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                  Todavía no tenés laboratorios asignados.
                </p>
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
                        className="flex items-center justify-between p-3 sm:p-4 rounded-lg transition-colors"
                        style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--ui-border-default)" }}
                      >
                        <div className="flex flex-col gap-1 min-w-0 pr-2">
                          <span className="text-sm sm:text-base font-medium truncate" style={{ color: "var(--text-heading)" }}>
                            {row.laboratorio?.nombre || `Lab ${row.assignment.laboratorio_id.slice(0, 8)}`}
                          </span>
                          {row.laboratorio && (
                            <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                              Dificultad: {row.laboratorio.nivel_dificultad}
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-2 sm:gap-3 shrink-0">
                          <span
                            className="text-xs font-medium px-2 sm:px-2.5 py-1 rounded-full whitespace-nowrap"
                            style={{
                              backgroundColor: `${statusColor[row.status]}18`,
                              color: statusColor[row.status],
                              border: `1px solid ${statusColor[row.status]}40`,
                            }}
                          >
                            {statusLabel[row.status]}
                          </span>
                          {row.status === "pendiente" && (
                            <>
                              <button
                                type="button"
                                disabled={busyId === row.assignment.id}
                                onClick={() => handleAccept(row.assignment.id)}
                                className="px-3 sm:px-4 py-1.5 rounded text-xs font-semibold cursor-pointer border-none transition-opacity hover:opacity-80 disabled:opacity-50"
                                style={{ backgroundColor: "var(--accent-primary)", color: "#fff", fontFamily: "'Fira Code', monospace" }}
                              >
                                Aceptar
                              </button>
                              <button
                                type="button"
                                disabled={busyId === row.assignment.id}
                                onClick={() => handleReject(row.assignment.id)}
                                className="px-3 sm:px-4 py-1.5 rounded text-xs font-semibold cursor-pointer border transition-opacity hover:opacity-80 disabled:opacity-50"
                                style={{ backgroundColor: "transparent", color: "var(--text-muted)", borderColor: "var(--ui-border-default)" }}
                              >
                                Rechazar
                              </button>
                            </>
                          )}
                        </div>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              )}
            </section>

            {/* ══════════════════════════════════
                PRÓXIMOS VENCIMIENTOS
                ══════════════════════════════════ */}
            <section className="mb-8 sm:mb-10">
              <SectionHeading icon={<IconClock />} title="Próximos Vencimientos" />

              {proximosVencimientos.length === 0 ? (
                <div
                  className="p-6 sm:p-8 rounded-lg text-center"
                  style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--ui-border-default)" }}
                >
                  <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                    No tenés laboratorios por vencer.
                  </p>
                </div>
              ) : (
                <div className="flex flex-col gap-2 sm:gap-3">
                  {proximosVencimientos.map((row) => (
                    <div
                      key={row.assignment.id}
                      className="flex items-center justify-between p-3 sm:p-4 rounded-lg"
                      style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--ui-border-gold)" }}
                    >
                      <div className="flex flex-col gap-1 min-w-0 pr-2">
                        <span className="text-sm sm:text-base font-medium truncate" style={{ color: "var(--text-heading)" }}>
                          {row.laboratorio?.nombre || `Lab ${row.assignment.laboratorio_id.slice(0, 8)}`}
                        </span>
                        <span className="text-xs" style={{ color: "var(--accent-danger)" }}>
                          Vence: {new Date(row.assignment.fecha_vencimiento!).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* ══════════════════════════════════
                CONVERTIRSE EN INSTRUCTOR
                ══════════════════════════════════ */}
            <section>
              <div
                className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-5 sm:p-6 rounded-lg gap-4 sm:gap-6"
                style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--ui-border-secondary)" }}
              >
                <div className="flex flex-col gap-1" style={{ maxWidth: "600px" }}>
                  <h2 className="flex items-center gap-2 text-base sm:text-lg font-semibold m-0" style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}>
                    <IconRocket style={{ color: "var(--ui-border-gold)" }} />
                    ¿Listo para el siguiente nivel?
                  </h2>
                  <p className="text-xs sm:text-sm m-0 leading-relaxed" style={{ color: "var(--text-muted)" }}>
                    Como Instructor podés crear tus propios laboratorios con secciones, flags y exámenes,
                    copiar laboratorios predeterminados para personalizarlos, invitar estudiantes y
                    hacer seguimiento de su progreso. Tu progreso actual como estudiante se conserva.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => setShowInstructorModal(true)}
                  className="w-full sm:w-auto px-5 sm:px-6 py-2.5 rounded text-sm font-semibold cursor-pointer border-none transition-opacity hover:opacity-85"
                  style={{ backgroundColor: "var(--text-heading)", color: "#0F1117", fontFamily: "'Fira Code', monospace" }}
                >
                  Convertirme en Instructor
                </button>
              </div>
            </section>
          </>
        )}

        {showInstructorModal && (
          <InstructorRegistrationModal
            form={instructorForm}
            onChange={setInstructorForm}
            onClose={() => setShowInstructorModal(false)}
          />
        )}
      </div>
    </main>
      <Footer />
    </div>
  )
}

function StatCard({ label, value, color, icon }: { label: string; value: number; color: string; icon?: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      className="flex-1 flex flex-col items-center gap-1.5 sm:gap-2 p-3 sm:p-5 rounded-lg"
      style={{ backgroundColor: "var(--bg-canvas)", border: "1px solid var(--ui-border-default)" }}
    >
      {icon && (
        <div className="flex items-center justify-center w-7 h-7 sm:w-8 sm:h-8 rounded-md" style={{ backgroundColor: `${color}18`, color }}>
          {icon}
        </div>
      )}
      <span className="text-xl sm:text-3xl font-bold" style={{ color, fontFamily: "'Fira Code', monospace" }}>
        {value}
      </span>
      <span className="text-[11px] sm:text-xs font-medium text-center" style={{ color: "var(--text-muted)" }}>{label}</span>
    </motion.div>
  )
}

function SkeletonBlock() {
  return (
    <div className="flex flex-col sm:flex-row gap-3 sm:gap-4">
      {Array.from({ length: 3 }).map((_, i) => (
        <motion.div
          key={i}
          animate={{ opacity: [0.4, 0.8, 0.4] }}
          transition={{ duration: 1.4, repeat: Infinity, delay: i * 0.1 }}
          className="flex-1 h-24 rounded-lg"
          style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--ui-border-default)" }}
        />
      ))}
    </div>
  )
}

/* ───────── MODAL REGISTRO INSTRUCTOR ───────── */
const TIPOS_INSTRUCTOR = [
  { value: "", label: "Seleccioná un tipo" },
  { value: "profesor", label: "Profesor Universitario" },
  { value: "capacitador", label: "Capacitador Corporativo" },
  { value: "investigador", label: "Investigador" },
  { value: "independiente", label: "Independiente / Freelancer" },
]

function InstructorRegistrationModal({
  form,
  onChange,
  onClose,
}: {
  form: { tipo: string; institucion: string; especialidades: string; motivacion: string }
  onChange: (f: typeof form) => void
  onClose: () => void
}) {
  const [sent, setSent] = useState(false)
  const update = (field: keyof typeof form, value: string) => {
    onChange({ ...form, [field]: value })
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-0"
      style={{ backgroundColor: "rgba(0, 0, 0, 0.7)", backdropFilter: "blur(4px)" }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <motion.div
        initial={{ opacity: 0, y: 16, scale: 0.97 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.25 }}
        className="w-full rounded-lg p-6 sm:p-8 shadow-2xl"
        style={{
          maxWidth: "520px",
          backgroundColor: "var(--bg-canvas)",
          border: "1px solid var(--ui-border-default)",
          boxShadow: "0 32px 64px rgba(0,0,0,0.5)",
        }}
      >
        <div className="flex items-center justify-between mb-5 sm:mb-6">
          <h2 className="text-lg sm:text-xl font-semibold m-0" style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}>
            Registro de Instructor
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="flex items-center justify-center w-8 h-8 rounded cursor-pointer border-none transition-colors shrink-0"
            style={{ backgroundColor: "transparent", color: "var(--text-muted)", fontSize: "18px" }}
            onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "var(--bg-surface-hover)" }}
            onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "transparent" }}
            aria-label="Cerrar"
          >
            ✕
          </button>
        </div>

        {sent ? (
          <div className="flex flex-col items-center gap-3 py-6 text-center">
            <p className="text-sm" style={{ color: "var(--text-base)" }}>
              Tu solicitud fue registrada. Un administrador debe aprobar el cambio de rol —
              todavía no existe un flujo automático de autoservicio para esto.
            </p>
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2 rounded text-sm font-semibold cursor-pointer border-none transition-opacity hover:opacity-85"
              style={{ backgroundColor: "var(--text-heading)", color: "#0F1117", fontFamily: "'Fira Code', monospace" }}
            >
              Entendido
            </button>
          </div>
        ) : (
          <>
            <p className="text-sm mb-5 sm:mb-6" style={{ color: "var(--text-muted)" }}>
              Contanos sobre vos para registrarte como instructor. Estos datos ayudarán
              a personalizar tu experiencia.
            </p>

            <div className="mb-4 sm:mb-5">
              <label className="block text-xs font-semibold mb-1.5" style={{ color: "var(--text-heading)", fontFamily: "'Fira Code', monospace" }}>
                Tipo de Instructor <span style={{ color: "var(--accent-danger)" }}>*</span>
              </label>
              <select
                value={form.tipo}
                onChange={(e) => update("tipo", e.target.value)}
                className="w-full px-3.5 py-2.5 rounded text-sm appearance-none cursor-pointer transition-colors"
                style={{ backgroundColor: "var(--bg-surface)", color: form.tipo ? "var(--text-base)" : "var(--text-muted)", border: "1px solid var(--ui-border-default)", fontFamily: "'Fira Sans', sans-serif" }}
                onFocus={(e) => { e.currentTarget.style.borderColor = "var(--accent-primary)" }}
                onBlur={(e) => { e.currentTarget.style.borderColor = "var(--ui-border-default)" }}
              >
                {TIPOS_INSTRUCTOR.map((t) => (
                  <option key={t.value} value={t.value} disabled={t.value === ""}>{t.label}</option>
                ))}
              </select>
            </div>

            <div className="mb-4 sm:mb-5">
              <label className="block text-xs font-semibold mb-1.5" style={{ color: "var(--text-heading)", fontFamily: "'Fira Code', monospace" }}>
                Institución / Afiliación
              </label>
              <input
                type="text"
                value={form.institucion}
                onChange={(e) => update("institucion", e.target.value)}
                placeholder="Ej: Universidad Nacional de Colombia"
                className="w-full px-3.5 py-2.5 rounded text-sm transition-colors"
                style={{ backgroundColor: "var(--bg-surface)", color: "var(--text-base)", border: "1px solid var(--ui-border-default)", fontFamily: "'Fira Sans', sans-serif" }}
                onFocus={(e) => { e.currentTarget.style.borderColor = "var(--accent-primary)" }}
                onBlur={(e) => { e.currentTarget.style.borderColor = "var(--ui-border-default)" }}
              />
            </div>

            <div className="mb-4 sm:mb-5">
              <label className="block text-xs font-semibold mb-1.5" style={{ color: "var(--text-heading)", fontFamily: "'Fira Code', monospace" }}>
                Áreas de Especialización
              </label>
              <input
                type="text"
                value={form.especialidades}
                onChange={(e) => update("especialidades", e.target.value)}
                placeholder="Ej: Seguridad Web, Redes, Forense"
                className="w-full px-3.5 py-2.5 rounded text-sm transition-colors"
                style={{ backgroundColor: "var(--bg-surface)", color: "var(--text-base)", border: "1px solid var(--ui-border-default)", fontFamily: "'Fira Sans', sans-serif" }}
                onFocus={(e) => { e.currentTarget.style.borderColor = "var(--accent-primary)" }}
                onBlur={(e) => { e.currentTarget.style.borderColor = "var(--ui-border-default)" }}
              />
            </div>

            <div className="mb-5 sm:mb-6">
              <label className="block text-xs font-semibold mb-1.5" style={{ color: "var(--text-heading)", fontFamily: "'Fira Code', monospace" }}>
                ¿Por qué querés ser instructor?
              </label>
              <textarea
                value={form.motivacion}
                onChange={(e) => update("motivacion", e.target.value)}
                placeholder="Contanos qué te motiva a crear laboratorios y guiar a otros estudiantes..."
                rows={3}
                className="w-full px-3.5 py-2.5 rounded text-sm resize-none transition-colors"
                style={{ backgroundColor: "var(--bg-surface)", color: "var(--text-base)", border: "1px solid var(--ui-border-default)", fontFamily: "'Fira Sans', sans-serif" }}
                onFocus={(e) => { e.currentTarget.style.borderColor = "var(--accent-primary)" }}
                onBlur={(e) => { e.currentTarget.style.borderColor = "var(--ui-border-default)" }}
              />
            </div>

            <div className="flex flex-col-reverse sm:flex-row items-stretch sm:items-center justify-end gap-2 sm:gap-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded text-sm font-medium cursor-pointer transition-colors"
                style={{ backgroundColor: "transparent", color: "var(--text-muted)", border: "1px solid var(--ui-border-default)", fontFamily: "'Fira Code', monospace" }}
                onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "var(--bg-surface-hover)" }}
                onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "transparent" }}
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={() => setSent(true)}
                disabled={!form.tipo}
                className="px-5 py-2 rounded text-sm font-semibold cursor-pointer border-none transition-opacity hover:opacity-85 disabled:opacity-50"
                style={{ backgroundColor: "var(--text-heading)", color: "#0F1117", fontFamily: "'Fira Code', monospace" }}
              >
                Registrarme como Instructor
              </button>
            </div>
          </>
        )}
      </motion.div>
    </motion.div>
  )
}
