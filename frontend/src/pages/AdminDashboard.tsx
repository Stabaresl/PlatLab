import { useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  getAdminDashboard,
  listUsers,
  disableUser,
  enableUser,
  ApiError,
  type AdminDashboard as AdminDashboardData,
  type UsuarioItem,
  type Rol,
} from "./api"
import Navbar from "../components/Navbar"
import Footer from "../components/Footer"

const ROLE_LABELS: Record<Rol, string> = {
  estudiante: "Estudiante",
  instructor: "Instructor",
  administrador: "Administrador",
}

const ROLE_COLORS: Record<Rol, string> = {
  estudiante: "#3B82F6",
  instructor: "#22C55E",
  administrador: "#F3DFB8",
}

export default function AdminDashboard() {
  const [dashboard, setDashboard] = useState<AdminDashboardData | null>(null)
  const [users, setUsers] = useState<UsuarioItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [busyUserId, setBusyUserId] = useState<string | null>(null)

  const PAGE_SIZE = 4
  const [page, setPage] = useState(0)
  const totalPages = Math.max(1, Math.ceil(users.length / PAGE_SIZE))
  const visible = users.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  useEffect(() => {
    let cancelled = false
    Promise.all([getAdminDashboard(), listUsers()])
      .then(([dashboardData, usersData]) => {
        if (cancelled) return
        setDashboard(dashboardData)
        setUsers(usersData)
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

  const toggleUser = async (user: UsuarioItem) => {
    setBusyUserId(user.id)
    try {
      const updated = user.is_active ? await disableUser(user.id) : await enableUser(user.id)
      setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo actualizar el usuario.")
    } finally {
      setBusyUserId(null)
    }
  }

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
            Panel del Administrador
          </h1>
          <p className="text-xs sm:text-sm mt-1" style={{ color: "var(--text-muted)" }}>
            Estado general de la plataforma
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
                ESTADO GENERAL — /users/dashboard/
                ══════════════════════════════════ */}
            <section className="mb-8 sm:mb-10">
              <h2
                className="text-lg sm:text-xl font-semibold mb-4 sm:mb-5"
                style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}
              >
                Estado General
              </h2>

              <div className="grid gap-3 sm:gap-4 mb-5" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))" }}>
                {dashboard && (
                  <>
                    <StatCard label="Laboratorios activos" value={dashboard.laboratorios_activos} delay={0} />
                    <StatCard
                      label="Tasa de completitud"
                      value={`${Math.round(dashboard.tasa_completitud_promedio * 100)}%`}
                      delay={0.05}
                    />
                    {Object.entries(dashboard.usuarios_por_rol).map(([rol, cantidad], i) => (
                      <StatCard
                        key={rol}
                        label={ROLE_LABELS[rol as Rol] || rol}
                        value={cantidad}
                        delay={0.1 + i * 0.05}
                        accent={ROLE_COLORS[rol as Rol]}
                      />
                    ))}
                  </>
                )}
              </div>

              {dashboard && dashboard.labs_mas_populares.length > 0 && (
                <div
                  className="rounded-lg overflow-hidden"
                  style={{ border: "1px solid var(--ui-border-default)" }}
                >
                  <dl className="m-0">
                    {dashboard.labs_mas_populares.map((lab, i) => (
                      <div
                        key={lab.laboratorio_id}
                        className="flex items-center justify-between gap-2 sm:gap-4 px-4 sm:px-5 py-3 sm:py-3.5"
                        style={{
                          backgroundColor: i % 2 === 0 ? "var(--bg-surface)" : "var(--bg-canvas)",
                          borderBottom: i < dashboard.labs_mas_populares.length - 1 ? "1px solid var(--ui-border-default)" : "none",
                        }}
                      >
                        <dt className="text-xs sm:text-sm font-medium truncate" style={{ color: "var(--text-heading)" }}>
                          {lab.nombre}
                        </dt>
                        <dd className="text-xs sm:text-sm m-0 shrink-0" style={{ color: "var(--text-muted)" }}>
                          {lab.estudiantes_inscritos} inscritos
                        </dd>
                      </div>
                    ))}
                  </dl>
                </div>
              )}
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
                    Total: {users.length} usuarios registrados
                  </p>
                </div>

                <div className="flex items-center gap-2 self-start sm:self-auto">
                  <CarouselButton label="Anterior" disabled={page === 0} onClick={() => setPage((p) => Math.max(0, p - 1))}>
                    ←
                  </CarouselButton>
                  <span className="text-xs" style={{ color: "var(--text-muted)", fontFamily: "'Fira Code', monospace" }}>
                    {page + 1}/{totalPages}
                  </span>
                  <CarouselButton label="Siguiente" disabled={page >= totalPages - 1} onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}>
                    →
                  </CarouselButton>
                </div>
              </div>

              <div className="grid gap-3 sm:gap-4 mb-5" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))" }}>
                <AnimatePresence mode="popLayout">
                  {visible.map((user) => (
                    <motion.div
                      key={user.id}
                      layout
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      transition={{ duration: 0.25 }}
                      className="flex flex-col p-4 sm:p-5 rounded-lg"
                      style={{
                        backgroundColor: "var(--bg-surface)",
                        border: `1px solid ${user.is_active ? "var(--ui-border-secondary)" : "var(--ui-border-default)"}`,
                      }}
                    >
                      <div className="flex items-center gap-3 mb-3">
                        <div
                          className="flex items-center justify-center w-10 h-10 rounded-full text-sm font-bold shrink-0"
                          style={{
                            backgroundColor: "var(--bg-surface-hover)",
                            color: ROLE_COLORS[user.rol] || "var(--text-muted)",
                            fontFamily: "'Fira Code', monospace",
                          }}
                        >
                          {user.nombre_completo.charAt(0).toUpperCase()}
                        </div>
                        <div className="flex flex-col min-w-0">
                          <span className="text-sm sm:text-base font-medium truncate" style={{ color: "var(--text-heading)" }}>
                            {user.nombre_completo}
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
                            backgroundColor: `${ROLE_COLORS[user.rol]}18`,
                            color: ROLE_COLORS[user.rol],
                            border: `1px solid ${ROLE_COLORS[user.rol]}35`,
                          }}
                        >
                          {ROLE_LABELS[user.rol] || user.rol}
                        </span>
                        <button
                          type="button"
                          disabled={busyUserId === user.id}
                          onClick={() => toggleUser(user)}
                          className="text-xs font-medium px-2 py-0.5 rounded-full cursor-pointer border-none disabled:opacity-50"
                          style={{
                            backgroundColor: user.is_active ? "rgba(34,197,94,0.12)" : "rgba(239,68,68,0.12)",
                            color: user.is_active ? "#22C55E" : "#EF4444",
                            border: `1px solid ${user.is_active ? "rgba(34,197,94,0.3)" : "rgba(239,68,68,0.3)"}`,
                          }}
                        >
                          {user.is_active ? "Activo" : "Inactivo"}
                        </button>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            </section>
          </>
        )}
      </div>
    </main>
      <Footer />
    </div>
  )
}

function StatCard({ label, value, delay, accent }: { label: string; value: string | number; delay: number; accent?: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay }}
      className="p-4 rounded-lg"
      style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--ui-border-default)" }}
    >
      <div
        className="text-2xl font-bold"
        style={{ color: accent || "var(--text-heading)", fontFamily: "'Fira Code', monospace" }}
      >
        {value}
      </div>
      <div className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>{label}</div>
    </motion.div>
  )
}

function SkeletonBlock() {
  return (
    <div className="grid gap-3 sm:gap-4" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))" }}>
      {Array.from({ length: 4 }).map((_, i) => (
        <motion.div
          key={i}
          animate={{ opacity: [0.4, 0.8, 0.4] }}
          transition={{ duration: 1.4, repeat: Infinity, delay: i * 0.1 }}
          className="h-20 rounded-lg"
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
