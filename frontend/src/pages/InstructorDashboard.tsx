import { useState } from "react"

export default function InstructorDashboard() {
  const labs = [
    { id: 1, name: "SQL Injection Avanzado", difficulty: "Media", status: "publicado", students: 12 },
    { id: 2, name: "XSS en Aplicaciones Modernas", difficulty: "Difícil", status: "publicado", students: 8 },
    { id: 3, name: "Autenticación con JWT", difficulty: "Fácil", status: "borrador", students: 0 },
    { id: 4, name: "Server Side Template Injection", difficulty: "Difícil", status: "borrador", students: 0 },
  ]

  const invitations = [
    { id: 1, student: "Carlos García", lab: "SQL Injection Avanzado", status: "pendiente", date: "2026-07-20" },
    { id: 2, student: "María López", lab: "SQL Injection Avanzado", status: "aceptada", date: "2026-07-18" },
    { id: 3, student: "Ana Martínez", lab: "XSS en Aplicaciones Modernas", status: "pendiente", date: "2026-07-22" },
    { id: 4, student: "Pedro Ramírez", lab: "SQL Injection Avanzado", status: "vencida", date: "2026-07-15" },
  ]

  const students = [
    { id: 1, name: "María López", email: "maria@example.com", progress: 85 },
    { id: 2, name: "Carlos García", email: "carlos@example.com", progress: 72 },
    { id: 3, name: "Ana Martínez", email: "ana@example.com", progress: 68 },
    { id: 4, name: "Pedro Ramírez", email: "pedro@example.com", progress: 55 },
    { id: 5, name: "Lucía Fernández", email: "lucia@example.com", progress: 50 },
    { id: 6, name: "Diego Torres", email: "diego@example.com", progress: 42 },
    { id: 7, name: "Valentina Ríos", email: "valentina@example.com", progress: 38 },
    { id: 8, name: "Santiago Vega", email: "santiago@example.com", progress: 30 },
    { id: 9, name: "Camila Ortiz", email: "camila@example.com", progress: 25 },
    { id: 10, name: "Felipe Muñoz", email: "felipe@example.com", progress: 15 },
  ]

  const PAGE_SIZE = 4
  const totalPages = Math.ceil(students.length / PAGE_SIZE)
  const [page, setPage] = useState(0)
  const visible = students.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

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
              Panel del Instructor
            </h1>
            <p className="text-xs sm:text-sm mt-1" style={{ color: "var(--text-muted)" }}>
              Gestioná tus laboratorios y estudiantes
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
            LABORATORIOS CREADOS — card-based
            ══════════════════════════════════ */}
        <section className="mb-8 sm:mb-10">
          <h2
            className="text-lg sm:text-xl font-semibold mb-4 sm:mb-5"
            style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}
          >
            Laboratorios Creados
          </h2>

          <div className="grid gap-3 sm:gap-4" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))" }}>
            {labs.map((lab) => {
              const isPublished = lab.status === "publicado"
              return (
                <div
                  key={lab.id}
                  className="flex flex-col p-4 sm:p-5 rounded-lg transition-colors"
                  style={{
                    backgroundColor: "var(--bg-surface)",
                    border: `1px solid ${isPublished ? "var(--ui-border-secondary)" : "var(--ui-border-default)"}`,
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = "var(--bg-surface-hover)"
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = "var(--bg-surface)"
                  }}
                >
                  <div className="flex items-start justify-between mb-3">
                    <span
                      className="text-sm sm:text-base font-medium leading-snug"
                      style={{ color: "var(--text-heading)" }}
                    >
                      {lab.name}
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
                      Dificultad:{" "}
                      <span style={{ color: "var(--text-base)" }}>{lab.difficulty}</span>
                    </span>
                    {isPublished && (
                      <span>
                        Estudiantes:{" "}
                        <span style={{ color: "var(--text-base)" }}>{lab.students}</span>
                      </span>
                    )}
                  </div>
                </div>
              )
            })}

            {/* Card para crear nuevo */}
            <button
              type="button"
              className="flex items-center justify-center p-4 sm:p-5 rounded-lg border-2 border-dashed cursor-pointer transition-colors"
              style={{
                backgroundColor: "transparent",
                borderColor: "var(--ui-border-default)",
                color: "var(--text-muted)",
                minHeight: "120px",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "var(--accent-primary)"
                e.currentTarget.style.color = "var(--accent-primary)"
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "var(--ui-border-default)"
                e.currentTarget.style.color = "var(--text-muted)"
              }}
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
            INVITACIONES — tabla con scroll horizontal en mobile
            ══════════════════════════════════ */}
        <section className="mb-8 sm:mb-10">
          <h2
            className="text-lg sm:text-xl font-semibold mb-4 sm:mb-5"
            style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}
          >
            Invitaciones
          </h2>

          <div
            className="rounded-lg overflow-x-auto"
            style={{ border: "1px solid var(--ui-border-default)" }}
          >
            <table className="w-full border-collapse">
              <thead>
                <tr style={{ backgroundColor: "var(--bg-surface)" }}>
                  {["Estudiante", "Laboratorio", "Estado", "Fecha"].map((col) => (
                    <th
                      key={col}
                      className="text-left text-xs font-semibold px-3 sm:px-4 py-2.5 sm:py-3 whitespace-nowrap"
                      style={{
                        color: "var(--text-muted)",
                        borderBottom: "1px solid var(--ui-border-default)",
                        fontFamily: "'Fira Code', monospace",
                      }}
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {invitations.map((inv) => {
                  const invColors: Record<string, string> = {
                    pendiente: "#3B82F6",
                    aceptada: "#22C55E",
                    vencida: "#EF4444",
                  }
                  const invLabels: Record<string, string> = {
                    pendiente: "Pendiente",
                    aceptada: "Aceptada",
                    vencida: "Vencida",
                  }
                  return (
                    <tr
                      key={inv.id}
                      style={{
                        borderBottom: "1px solid var(--ui-border-default)",
                        backgroundColor: "var(--bg-canvas)",
                      }}
                      className="transition-colors"
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = "var(--bg-surface-hover)"
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = "var(--bg-canvas)"
                      }}
                    >
                      <td className="px-3 sm:px-4 py-2.5 sm:py-3 text-sm whitespace-nowrap" style={{ color: "var(--text-heading)" }}>
                        {inv.student}
                      </td>
                      <td className="px-3 sm:px-4 py-2.5 sm:py-3 text-sm whitespace-nowrap" style={{ color: "var(--text-base)" }}>
                        {inv.lab}
                      </td>
                      <td className="px-3 sm:px-4 py-2.5 sm:py-3 whitespace-nowrap">
                        <span
                          className="text-xs font-medium px-2 py-0.5 rounded-full"
                          style={{
                            backgroundColor: `${invColors[inv.status]}18`,
                            color: invColors[inv.status],
                            border: `1px solid ${invColors[inv.status]}40`,
                          }}
                        >
                          {invLabels[inv.status]}
                        </span>
                      </td>
                      <td className="px-3 sm:px-4 py-2.5 sm:py-3 text-sm whitespace-nowrap" style={{ color: "var(--text-muted)", fontFamily: "'Fira Code', monospace" }}>
                        {inv.date}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </section>

        {/* ══════════════════════════════════
            TOP ESTUDIANTES — carrusel funcional
            ══════════════════════════════════ */}
        <section>
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3 sm:gap-0 mb-5">
            <div>
              <h2
                className="text-lg sm:text-xl font-semibold"
                style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}
              >
                Top Estudiantes
              </h2>
              <p className="text-xs sm:text-sm mt-1" style={{ color: "var(--text-muted)" }}>
                Estudiantes ordenados por mayor avance
              </p>
            </div>

            <div className="flex items-center gap-2 self-start sm:self-auto">
              <CarouselButton
                label="Anterior"
                disabled={page === 0}
                onClick={() => setPage((p) => Math.max(0, p - 1))}
              >
                ←
              </CarouselButton>
              <span className="text-xs" style={{ color: "var(--text-muted)", fontFamily: "'Fira Code', monospace" }}>
                {page + 1}/{totalPages}
              </span>
              <CarouselButton
                label="Siguiente"
                disabled={page >= totalPages - 1}
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              >
                →
              </CarouselButton>
            </div>
          </div>

          <div className="grid gap-3 sm:gap-4 mb-5" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))" }}>
            {visible.map((student) => (
              <div
                key={student.id}
                className="flex flex-col p-4 sm:p-5 rounded-lg"
                style={{
                  backgroundColor: "var(--bg-surface)",
                  border: "1px solid var(--ui-border-default)",
                }}
              >
                <div
                  className="flex items-center justify-center w-10 h-10 rounded-full mb-3 text-sm font-bold shrink-0"
                  style={{
                    backgroundColor: "var(--bg-surface-hover)",
                    color: "var(--text-muted)",
                    fontFamily: "'Fira Code', monospace",
                  }}
                >
                  {student.name.charAt(0)}
                </div>

                <span className="text-sm sm:text-base font-medium" style={{ color: "var(--text-heading)" }}>
                  {student.name}
                </span>
                <span className="text-xs mb-3 truncate" style={{ color: "var(--text-muted)" }}>
                  {student.email}
                </span>

                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                    Progreso
                  </span>
                  <span
                    className="text-xs font-medium"
                    style={{ color: student.progress >= 70 ? "#22C55E" : student.progress >= 40 ? "#3B82F6" : "var(--text-muted)", fontFamily: "'Fira Code', monospace" }}
                  >
                    {student.progress}%
                  </span>
                </div>
                <div
                  className="w-full h-1.5 rounded-full overflow-hidden"
                  style={{ backgroundColor: "var(--bg-surface-hover)" }}
                >
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${student.progress}%`,
                      backgroundColor: student.progress >= 70 ? "#22C55E" : student.progress >= 40 ? "#3B82F6" : "var(--text-muted)",
                    }}
                  />
                </div>
              </div>
            ))}
          </div>

          <button
            type="button"
            className="text-sm font-medium cursor-pointer border-none bg-transparent transition-colors hover:underline"
            style={{ color: "var(--text-muted)" }}
            onMouseEnter={(e) => { e.currentTarget.style.color = "var(--text-heading)" }}
            onMouseLeave={(e) => { e.currentTarget.style.color = "var(--text-muted)" }}
          >
            Ver todos los estudiantes →
          </button>
        </section>
      </div>
    </main>
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
      style={{
        backgroundColor: "transparent",
        borderColor: "var(--ui-border-default)",
        color: "var(--text-base)",
      }}
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
