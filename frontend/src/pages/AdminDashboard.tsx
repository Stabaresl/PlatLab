import { useMemo, useState } from "react"

export default function AdminDashboard() {
  const settings = [
    { label: "Nombre del sitio", value: "GAIA - PlatLAB", type: "text" },
    { label: "Registro de usuarios", value: "Abierto", type: "toggle" },
    { label: "Rol por defecto", value: "Estudiante", type: "select" },
    { label: "Intentos máximos de login", value: "5", type: "number" },
    { label: "Bloqueo temporal (minutos)", value: "15", type: "number" },
    { label: "Duración de sesión (horas)", value: "24", type: "number" },
    { label: "Rate limit por minuto", value: "30 requests", type: "text" },
  ]

  const allUsers = [
    { id: 1, name: "María López", email: "maria@example.com", role: "Estudiante", status: "activo" },
    { id: 2, name: "Carlos García", email: "carlos@example.com", role: "Estudiante", status: "activo" },
    { id: 3, name: "Ana Martínez", email: "ana@example.com", role: "Estudiante", status: "inactivo" },
    { id: 4, name: "Pedro Ramírez", email: "pedro@example.com", role: "Instructor", status: "activo" },
    { id: 5, name: "Lucía Fernández", email: "lucia@example.com", role: "Estudiante", status: "activo" },
    { id: 6, name: "Diego Torres", email: "diego@example.com", role: "Instructor", status: "activo" },
    { id: 7, name: "Valentina Ríos", email: "valentina@example.com", role: "Administrador", status: "activo" },
    { id: 8, name: "Santiago Vega", email: "santiago@example.com", role: "Estudiante", status: "inactivo" },
    { id: 9, name: "Camila Ortiz", email: "camila@example.com", role: "Estudiante", status: "activo" },
    { id: 10, name: "Felipe Muñoz", email: "felipe@example.com", role: "Instructor", status: "activo" },
    { id: 11, name: "Laura Mendoza", email: "laura@example.com", role: "Estudiante", status: "activo" },
    { id: 12, name: "Jorge Castillo", email: "jorge@example.com", role: "Estudiante", status: "inactivo" },
  ]

  /* Shuffle estable — una sola vez por mount */
  const shuffled = useMemo(
    () => [...allUsers].sort(() => Math.random() - 0.5),
    [],
  )

  const PAGE_SIZE = 4
  const totalPages = Math.ceil(shuffled.length / PAGE_SIZE)
  const [page, setPage] = useState(0)
  const visible = shuffled.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  const roleColors: Record<string, string> = {
    Estudiante: "#3B82F6",
    Instructor: "#22C55E",
    Administrador: "#F3DFB8",
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
              Panel del Administrador
            </h1>
            <p className="text-xs sm:text-sm mt-1" style={{ color: "var(--text-muted)" }}>
              Configuración global del sistema
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
            CONFIGURACIONES DEL SISTEMA
            ══════════════════════════════════ */}
        <section className="mb-8 sm:mb-10">
          <h2
            className="text-lg sm:text-xl font-semibold mb-4 sm:mb-5"
            style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}
          >
            Configuraciones del Sistema
          </h2>

          <div
            className="rounded-lg overflow-hidden"
            style={{ border: "1px solid var(--ui-border-default)" }}
          >
            <dl className="m-0">
              {settings.map((s, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between gap-2 sm:gap-4 px-4 sm:px-5 py-3 sm:py-3.5 transition-colors"
                  style={{
                    backgroundColor: i % 2 === 0 ? "var(--bg-surface)" : "var(--bg-canvas)",
                    borderBottom: i < settings.length - 1 ? "1px solid var(--ui-border-default)" : "none",
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = "var(--bg-surface-hover)" }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = i % 2 === 0 ? "var(--bg-surface)" : "var(--bg-canvas)"
                  }}
                >
                  <dt
                    className="text-xs sm:text-sm font-medium truncate"
                    style={{ color: "var(--text-heading)" }}
                  >
                    {s.label}
                  </dt>
                  <dd
                    className="text-xs sm:text-sm m-0 shrink-0 text-right"
                    style={{
                      color: "var(--text-base)",
                      fontFamily: s.type === "number" ? "'Fira Code', monospace" : "inherit",
                    }}
                  >
                    {s.type === "toggle" ? (
                      <span
                        className="text-xs font-medium px-2 sm:px-2.5 py-1 rounded-full whitespace-nowrap"
                        style={{
                          backgroundColor: "rgba(34,197,94,0.12)",
                          color: "#22C55E",
                          border: "1px solid rgba(34,197,94,0.3)",
                        }}
                      >
                        {s.value}
                      </span>
                    ) : s.type === "select" ? (
                      <span
                        className="text-xs font-medium px-2 sm:px-2.5 py-1 rounded-full whitespace-nowrap"
                        style={{
                          backgroundColor: "rgba(59,130,246,0.12)",
                          color: "#3B82F6",
                          border: "1px solid rgba(59,130,246,0.3)",
                        }}
                      >
                        {s.value}
                      </span>
                    ) : (
                      <span className="whitespace-nowrap">{s.value}</span>
                    )}
                  </dd>
                </div>
              ))}
            </dl>
          </div>
        </section>

        {/* ══════════════════════════════════
            USUARIOS — carrusel funcional
            ══════════════════════════════════ */}
        <section>
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3 sm:gap-0 mb-5">
            <div>
              <h2
                className="text-lg sm:text-xl font-semibold"
                style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}
              >
                Usuarios
              </h2>
              <p className="text-xs sm:text-sm mt-1" style={{ color: "var(--text-muted)" }}>
                Total: {allUsers.length} usuarios registrados
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
            {visible.map((user) => (
              <div
                key={user.id}
                className="flex flex-col p-4 sm:p-5 rounded-lg"
                style={{
                  backgroundColor: "var(--bg-surface)",
                  border: `1px solid ${user.status === "activo" ? "var(--ui-border-secondary)" : "var(--ui-border-default)"}`,
                }}
              >
                <div className="flex items-center gap-3 mb-3">
                  <div
                    className="flex items-center justify-center w-10 h-10 rounded-full text-sm font-bold shrink-0"
                    style={{
                      backgroundColor: "var(--bg-surface-hover)",
                      color: roleColors[user.role] || "var(--text-muted)",
                      fontFamily: "'Fira Code', monospace",
                    }}
                  >
                    {user.name.charAt(0)}
                  </div>
                  <div className="flex flex-col min-w-0">
                    <span className="text-sm sm:text-base font-medium truncate" style={{ color: "var(--text-heading)" }}>
                      {user.name}
                    </span>
                    <span className="text-xs truncate" style={{ color: "var(--text-muted)" }}>
                      {user.email}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2 mt-auto flex-wrap">
                  <span
                    className="text-xs font-medium px-2 py-0.5 rounded-full"
                    style={{
                      backgroundColor: `${roleColors[user.role]}18`,
                      color: roleColors[user.role],
                      border: `1px solid ${roleColors[user.role]}35`,
                    }}
                  >
                    {user.role}
                  </span>
                  <span
                    className="text-xs font-medium px-2 py-0.5 rounded-full"
                    style={{
                      backgroundColor: user.status === "activo" ? "rgba(34,197,94,0.12)" : "rgba(239,68,68,0.12)",
                      color: user.status === "activo" ? "#22C55E" : "#EF4444",
                      border: `1px solid ${user.status === "activo" ? "rgba(34,197,94,0.3)" : "rgba(239,68,68,0.3)"}`,
                    }}
                  >
                    {user.status === "activo" ? "Activo" : "Inactivo"}
                  </span>
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
            Gestionar usuarios →
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
