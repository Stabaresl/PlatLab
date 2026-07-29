import { useState } from "react"

export default function StudentDashboard() {
  const [showInstructorModal, setShowInstructorModal] = useState(false)
  const [instructorForm, setInstructorForm] = useState({
    tipo: "",
    institucion: "",
    especialidades: "",
    motivacion: "",
  })

  const progress = {
    completed: 3,
    inProgress: 2,
    total: 10,
  }

  const labs = [
    { id: 1, name: "Introducción a SQL Injection", difficulty: "Fácil", status: "completado" },
    { id: 2, name: "Cross-Site Scripting (XSS)", difficulty: "Fácil", status: "en_progreso" },
    { id: 3, name: "Broken Authentication", difficulty: "Media", status: "en_progreso" },
    { id: 4, name: "Path Traversal", difficulty: "Media", status: "pendiente" },
    { id: 5, name: "Server-Side Request Forgery", difficulty: "Difícil", status: "pendiente" },
  ]

  const exams = [
    { id: 1, labName: "Introducción a SQL Injection", dueDate: "2026-08-01" },
    { id: 2, labName: "Broken Authentication", dueDate: "2026-08-15" },
  ]

  const pendingCount = progress.total - progress.completed - progress.inProgress
  const pct = Math.round((progress.completed / progress.total) * 100)

  const statusColor: Record<string, string> = {
    completado: "#22C55E",
    en_progreso: "#3B82F6",
    pendiente: "#94A3B8",
  }
  const statusLabel: Record<string, string> = {
    completado: "Completado",
    en_progreso: "En Progreso",
    pendiente: "Pendiente",
  }

  return (
    <main
      className="min-h-screen"
      style={{ backgroundColor: "var(--bg-canvas)", color: "var(--text-base)" }}
    >
      <div
        className="mx-auto px-4 sm:px-6 md:px-8 py-6 sm:py-8 md:py-10"
        style={{ maxWidth: "1200px" }}
      >
        {/* ══════════════════════════════════
            HEADER
            ══════════════════════════════════ */}
        <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-0 mb-8 sm:mb-10">
          <div>
            <h1
              className="text-2xl sm:text-3xl font-semibold m-0"
              style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}
            >
              Panel del Estudiante
            </h1>
            <p className="text-xs sm:text-sm mt-1" style={{ color: "var(--text-muted)" }}>
              Bienvenido de vuelta
            </p>
          </div>

          <button
            type="button"
            onClick={() => {
              localStorage.clear()
              window.location.href = "/login"
            }}
            className="
              self-start sm:self-auto
              px-4 sm:px-5 py-1.5 sm:py-2
              rounded text-xs sm:text-sm
              font-semibold cursor-pointer border transition-colors
            "
            style={{
              backgroundColor: "transparent",
              borderColor: "var(--ui-border-default)",
              color: "var(--text-muted)",
              fontFamily: "'Fira Code', monospace",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "var(--accent-danger)"
              e.currentTarget.style.color = "var(--accent-danger)"
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = "var(--ui-border-default)"
              e.currentTarget.style.color = "var(--text-muted)"
            }}
          >
            Cerrar Sesión
          </button>
        </header>

        {/* ══════════════════════════════════
            PROGRESO — 3 tarjetas + barra
            ══════════════════════════════════ */}
        <section className="mb-8 sm:mb-10">
          <h2
            className="text-lg sm:text-xl font-semibold mb-4 sm:mb-5"
            style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}
          >
            Mi Progreso
          </h2>

          {/* Stats — apiladas en mobile, en fila en desktop */}
          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 mb-5 sm:mb-6">
            <StatCard label="Completados" value={progress.completed} color="#22C55E" />
            <StatCard label="En Progreso" value={progress.inProgress} color="#3B82F6" />
            <StatCard label="Pendientes" value={pendingCount} color="#94A3B8" />
          </div>

          {/* Barra de progreso */}
          <div
            className="p-4 sm:p-5 rounded-lg"
            style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--ui-border-default)" }}
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium" style={{ color: "var(--text-heading)" }}>
                Progreso general
              </span>
              <span className="text-xs sm:text-sm" style={{ color: "var(--text-muted)", fontFamily: "'Fira Code', monospace" }}>
                {pct}%
              </span>
            </div>
            <div
              className="w-full h-2 rounded-full overflow-hidden"
              style={{ backgroundColor: "var(--bg-surface-hover)" }}
            >
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${pct}%`,
                  background: "linear-gradient(90deg, #3B82F6, #22C55E)",
                }}
              />
            </div>
            <p className="text-xs mt-2" style={{ color: "var(--text-muted)" }}>
              {progress.completed} de {progress.total} laboratorios completados
            </p>
          </div>
        </section>

        {/* ══════════════════════════════════
            LABORATORIOS DISPONIBLES
            ══════════════════════════════════ */}
        <section className="mb-8 sm:mb-10">
          <h2
            className="text-lg sm:text-xl font-semibold mb-4 sm:mb-5"
            style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}
          >
            Laboratorios Disponibles
          </h2>

          <div className="flex flex-col gap-2 sm:gap-3">
            {labs.map((lab) => (
              <div
                key={lab.id}
                className="flex items-center justify-between p-3 sm:p-4 rounded-lg transition-colors"
                style={{
                  backgroundColor: "var(--bg-surface)",
                  border: "1px solid var(--ui-border-default)",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = "var(--ui-border-secondary)"
                  e.currentTarget.style.backgroundColor = "var(--bg-surface-hover)"
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = "var(--ui-border-default)"
                  e.currentTarget.style.backgroundColor = "var(--bg-surface)"
                }}
              >
                <div className="flex flex-col gap-1 min-w-0 pr-2">
                  <span
                    className="text-sm sm:text-base font-medium truncate"
                    style={{ color: "var(--text-heading)" }}
                  >
                    {lab.name}
                  </span>
                  <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                    Dificultad: {lab.difficulty}
                  </span>
                </div>

                <div className="flex items-center gap-2 sm:gap-3 shrink-0">
                  <span
                    className="text-xs font-medium px-2 sm:px-2.5 py-1 rounded-full whitespace-nowrap"
                    style={{
                      backgroundColor: `${statusColor[lab.status]}18`,
                      color: statusColor[lab.status],
                      border: `1px solid ${statusColor[lab.status]}40`,
                    }}
                  >
                    {statusLabel[lab.status]}
                  </span>
                  {lab.status === "pendiente" && (
                    <button
                      type="button"
                      className="px-3 sm:px-4 py-1.5 rounded text-xs font-semibold cursor-pointer border-none transition-opacity hover:opacity-80"
                      style={{
                        backgroundColor: "var(--accent-primary)",
                        color: "#fff",
                        fontFamily: "'Fira Code', monospace",
                      }}
                    >
                      Iniciar
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ══════════════════════════════════
            EXÁMENES PENDIENTES
            ══════════════════════════════════ */}
        <section className="mb-8 sm:mb-10">
          <h2
            className="text-lg sm:text-xl font-semibold mb-4 sm:mb-5"
            style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}
          >
            Exámenes Pendientes
          </h2>

          {exams.length === 0 ? (
            <div
              className="p-6 sm:p-8 rounded-lg text-center"
              style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--ui-border-default)" }}
            >
              <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                No tienes exámenes pendientes.
              </p>
            </div>
          ) : (
            <div className="flex flex-col gap-2 sm:gap-3">
              {exams.map((exam) => (
                <div
                  key={exam.id}
                  className="flex items-center justify-between p-3 sm:p-4 rounded-lg"
                  style={{
                    backgroundColor: "var(--bg-surface)",
                    border: "1px solid var(--ui-border-gold)",
                  }}
                >
                  <div className="flex flex-col gap-1 min-w-0 pr-2">
                    <span className="text-sm sm:text-base font-medium truncate" style={{ color: "var(--text-heading)" }}>
                      {exam.labName}
                    </span>
                    <span className="text-xs" style={{ color: "var(--accent-danger)" }}>
                      Vence: {exam.dueDate}
                    </span>
                  </div>
                  <button
                    type="button"
                    className="px-3 sm:px-4 py-1.5 rounded text-xs font-semibold cursor-pointer border-none transition-opacity hover:opacity-80 shrink-0"
                    style={{
                      backgroundColor: "var(--accent-primary)",
                      color: "#fff",
                      fontFamily: "'Fira Code', monospace",
                    }}
                  >
                    Rendir
                  </button>
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
            style={{
              backgroundColor: "var(--bg-surface)",
              border: "1px solid var(--ui-border-secondary)",
            }}
          >
            <div className="flex flex-col gap-1" style={{ maxWidth: "600px" }}>
              <h2
                className="text-base sm:text-lg font-semibold m-0"
                style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}
              >
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
              className="
                w-full sm:w-auto
                px-5 sm:px-6 py-2.5
                rounded text-sm font-semibold
                cursor-pointer border-none
                transition-opacity hover:opacity-85
              "
              style={{
                backgroundColor: "var(--text-heading)",
                color: "#0F1117",
                fontFamily: "'Fira Code', monospace",
              }}
            >
              Convertirme en Instructor
            </button>
          </div>
        </section>

        {/* ══════════════════════════════════
            MODAL — REGISTRO DE INSTRUCTOR
            ══════════════════════════════════ */}
        {showInstructorModal && (
          <InstructorRegistrationModal
            form={instructorForm}
            onChange={setInstructorForm}
            onClose={() => setShowInstructorModal(false)}
            onSubmit={() => {
              localStorage.setItem("role", "instructor")
              localStorage.setItem("instructor_data", JSON.stringify(instructorForm))
              window.location.href = "/dashboard"
            }}
          />
        )}
      </div>
    </main>
  )
}

/* ───────── componente interno: StatCard ───────── */
function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div
      className="flex-1 flex flex-col items-center gap-2 p-4 sm:p-5 rounded-lg"
      style={{
        backgroundColor: "var(--bg-surface)",
        border: "1px solid var(--ui-border-default)",
      }}
    >
      <span
        className="text-2xl sm:text-3xl font-bold"
        style={{ color, fontFamily: "'Fira Code', monospace" }}
      >
        {value}
      </span>
      <span className="text-xs font-medium" style={{ color: "var(--text-muted)" }}>
        {label}
      </span>
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
  onSubmit,
}: {
  form: { tipo: string; institucion: string; especialidades: string; motivacion: string }
  onChange: (f: typeof form) => void
  onClose: () => void
  onSubmit: () => void
}) {
  const update = (field: keyof typeof form, value: string) => {
    onChange({ ...form, [field]: value })
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-0"
      style={{
        backgroundColor: "rgba(0, 0, 0, 0.7)",
        backdropFilter: "blur(4px)",
      }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div
        className="w-full rounded-lg p-6 sm:p-8 shadow-2xl"
        style={{
          maxWidth: "520px",
          backgroundColor: "var(--bg-canvas)",
          border: "1px solid var(--ui-border-default)",
          boxShadow: "0 32px 64px rgba(0,0,0,0.5)",
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-5 sm:mb-6">
          <h2
            className="text-lg sm:text-xl font-semibold m-0"
            style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}
          >
            Registro de Instructor
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="flex items-center justify-center w-8 h-8 rounded cursor-pointer border-none transition-colors shrink-0"
            style={{
              backgroundColor: "transparent",
              color: "var(--text-muted)",
              fontSize: "18px",
            }}
            onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "var(--bg-surface-hover)" }}
            onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "transparent" }}
            aria-label="Cerrar"
          >
            ✕
          </button>
        </div>

        <p className="text-sm mb-5 sm:mb-6" style={{ color: "var(--text-muted)" }}>
          Contanos sobre vos para registrarte como instructor. Estos datos ayudarán
          a personalizar tu experiencia.
        </p>

        {/* Tipo de instructor */}
        <div className="mb-4 sm:mb-5">
          <label
            className="block text-xs font-semibold mb-1.5"
            style={{ color: "var(--text-heading)", fontFamily: "'Fira Code', monospace" }}
          >
            Tipo de Instructor <span style={{ color: "var(--accent-danger)" }}>*</span>
          </label>
          <select
            value={form.tipo}
            onChange={(e) => update("tipo", e.target.value)}
            className="w-full px-3.5 py-2.5 rounded text-sm appearance-none cursor-pointer transition-colors"
            style={{
              backgroundColor: "var(--bg-surface)",
              color: form.tipo ? "var(--text-base)" : "var(--text-muted)",
              border: "1px solid var(--ui-border-default)",
              fontFamily: "'Fira Sans', sans-serif",
            }}
            onFocus={(e) => { e.currentTarget.style.borderColor = "var(--accent-primary)" }}
            onBlur={(e) => { e.currentTarget.style.borderColor = "var(--ui-border-default)" }}
          >
            {TIPOS_INSTRUCTOR.map((t) => (
              <option key={t.value} value={t.value} disabled={t.value === ""}>
                {t.label}
              </option>
            ))}
          </select>
        </div>

        {/* Institución */}
        <div className="mb-4 sm:mb-5">
          <label
            className="block text-xs font-semibold mb-1.5"
            style={{ color: "var(--text-heading)", fontFamily: "'Fira Code', monospace" }}
          >
            Institución / Afiliación
          </label>
          <input
            type="text"
            value={form.institucion}
            onChange={(e) => update("institucion", e.target.value)}
            placeholder="Ej: Universidad Nacional de Colombia"
            className="w-full px-3.5 py-2.5 rounded text-sm transition-colors"
            style={{
              backgroundColor: "var(--bg-surface)",
              color: "var(--text-base)",
              border: "1px solid var(--ui-border-default)",
              fontFamily: "'Fira Sans', sans-serif",
            }}
            onFocus={(e) => { e.currentTarget.style.borderColor = "var(--accent-primary)" }}
            onBlur={(e) => { e.currentTarget.style.borderColor = "var(--ui-border-default)" }}
          />
        </div>

        {/* Áreas de especialización */}
        <div className="mb-4 sm:mb-5">
          <label
            className="block text-xs font-semibold mb-1.5"
            style={{ color: "var(--text-heading)", fontFamily: "'Fira Code', monospace" }}
          >
            Áreas de Especialización
          </label>
          <input
            type="text"
            value={form.especialidades}
            onChange={(e) => update("especialidades", e.target.value)}
            placeholder="Ej: Seguridad Web, Redes, Forense"
            className="w-full px-3.5 py-2.5 rounded text-sm transition-colors"
            style={{
              backgroundColor: "var(--bg-surface)",
              color: "var(--text-base)",
              border: "1px solid var(--ui-border-default)",
              fontFamily: "'Fira Sans', sans-serif",
            }}
            onFocus={(e) => { e.currentTarget.style.borderColor = "var(--accent-primary)" }}
            onBlur={(e) => { e.currentTarget.style.borderColor = "var(--ui-border-default)" }}
          />
        </div>

        {/* Motivación */}
        <div className="mb-5 sm:mb-6">
          <label
            className="block text-xs font-semibold mb-1.5"
            style={{ color: "var(--text-heading)", fontFamily: "'Fira Code', monospace" }}
          >
            ¿Por qué querés ser instructor?
          </label>
          <textarea
            value={form.motivacion}
            onChange={(e) => update("motivacion", e.target.value)}
            placeholder="Contanos qué te motiva a crear laboratorios y guiar a otros estudiantes..."
            rows={3}
            className="w-full px-3.5 py-2.5 rounded text-sm resize-none transition-colors"
            style={{
              backgroundColor: "var(--bg-surface)",
              color: "var(--text-base)",
              border: "1px solid var(--ui-border-default)",
              fontFamily: "'Fira Sans', sans-serif",
            }}
            onFocus={(e) => { e.currentTarget.style.borderColor = "var(--accent-primary)" }}
            onBlur={(e) => { e.currentTarget.style.borderColor = "var(--ui-border-default)" }}
          />
        </div>

        {/* Acciones */}
        <div className="flex flex-col-reverse sm:flex-row items-stretch sm:items-center justify-end gap-2 sm:gap-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded text-sm font-medium cursor-pointer transition-colors"
            style={{
              backgroundColor: "transparent",
              color: "var(--text-muted)",
              border: "1px solid var(--ui-border-default)",
              fontFamily: "'Fira Code', monospace",
            }}
            onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "var(--bg-surface-hover)" }}
            onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = "transparent" }}
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={onSubmit}
            className="px-5 py-2 rounded text-sm font-semibold cursor-pointer border-none transition-opacity hover:opacity-85"
            style={{
              backgroundColor: "var(--text-heading)",
              color: "#0F1117",
              fontFamily: "'Fira Code', monospace",
            }}
          >
            Registrarme como Instructor
          </button>
        </div>
      </div>
    </div>
  )
}
