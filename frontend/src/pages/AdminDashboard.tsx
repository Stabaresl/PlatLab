import { useEffect, useState, type ReactNode } from "react"
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
import HeroBackground from "../components/HeroBackground"
import SectionHeading from "../components/SectionHeading"
import ProgressRing from "../components/ProgressRing"
import TerminalHeader from "../components/TerminalHeader"
import StatusDot from "../components/StatusDot"
import { IconChart, IconUsers, IconTrophy } from "../components/icons"
import { Skeleton } from "../components/ui/skeleton"

const ROLE_LABELS: Record<Rol, string> = {
  estudiante: "Estudiante",
  instructor: "Instructor",
  administrador: "Administrador",
}

const ROLE_COLORS: Record<Rol, string> = {
  estudiante: "var(--signal-cyan)",
  instructor: "var(--signal-green)",
  administrador: "var(--signal-amber)",
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
    <div className="relative min-h-screen overflow-hidden" style={{ backgroundColor: "var(--canvas)", color: "var(--text-base)" }}>
      <HeroBackground image="grim" imageOpacity={0.05} overlayOpacity={0.92} texture="none" />
      <div className="relative z-10 flex flex-col min-h-screen">
        <Navbar />
        <main className="flex-1">
          <div className="mx-auto px-4 sm:px-6 md:px-8 py-6 sm:py-8 md:py-10" style={{ maxWidth: "1200px" }}>
            <TerminalHeader title="Panel del Administrador" subtitle="Estado general de la plataforma" prompt="whoami → administrador" />

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
                {/* ═══ ESTADO GENERAL ═══ */}
                <section className="mb-8 sm:mb-10">
                  <SectionHeading icon={<IconChart />} title="Estado General" subtitle="Salud y adopción de la plataforma" />

                  {dashboard && (
                    <div className="chamfer flex flex-col sm:flex-row items-center gap-6 sm:gap-8 p-4 sm:p-6 mb-5" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
                      <ProgressRing percent={Math.round(dashboard.tasa_completitud_promedio * 100)} size={104} color="var(--signal-green)" label="completitud promedio" />
                      <div className="flex-1 w-full grid gap-3 sm:gap-4" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))" }}>
                        <StatCard label="Laboratorios activos" value={dashboard.laboratorios_activos} delay={0} />
                        {Object.entries(dashboard.usuarios_por_rol).map(([rol, cantidad], i) => (
                          <StatCard key={rol} label={ROLE_LABELS[rol as Rol] || rol} value={cantidad} delay={0.1 + i * 0.05} accent={ROLE_COLORS[rol as Rol]} />
                        ))}
                      </div>
                    </div>
                  )}

                  {dashboard && dashboard.labs_mas_populares.length > 0 && (
                    <div>
                      <div className="flex items-center gap-2 mb-2 sm:mb-3">
                        <IconTrophy style={{ color: "var(--signal-amber)" }} />
                        <span className="text-sm font-bold uppercase tracking-wide" style={{ color: "var(--text-heading)" }}>Laboratorios más populares</span>
                      </div>
                      <div className="chamfer overflow-hidden" style={{ border: "1px solid var(--border-default)" }}>
                        <dl className="m-0">
                          {dashboard.labs_mas_populares.map((lab, i) => (
                            <div
                              key={lab.laboratorio_id}
                              className="flex items-center justify-between gap-2 sm:gap-4 px-4 sm:px-5 py-3 sm:py-3.5"
                              style={{
                                backgroundColor: i % 2 === 0 ? "var(--surface)" : "var(--canvas)",
                                borderBottom: i < dashboard.labs_mas_populares.length - 1 ? "1px solid var(--border-default)" : "none",
                              }}
                            >
                              <dt className="text-xs sm:text-sm font-medium truncate" style={{ color: "var(--text-heading)" }}>
                                <span className="mr-2 font-mono" style={{ color: "var(--text-dim)" }}>{String(i + 1).padStart(2, "0")}</span>
                                {lab.nombre}
                              </dt>
                              <dd className="text-xs sm:text-sm m-0 shrink-0 font-mono" style={{ color: "var(--text-muted)" }}>
                                {lab.estudiantes_inscritos} inscritos
                              </dd>
                            </div>
                          ))}
                        </dl>
                      </div>
                    </div>
                  )}
                </section>

                {/* ═══ USUARIOS ═══ */}
                <section>
                  <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3 sm:gap-0 mb-5">
                    <SectionHeading icon={<IconUsers />} title="Usuarios" subtitle={`Total: ${users.length} usuarios registrados`} />

                    <div className="flex items-center gap-2 self-start sm:self-auto">
                      <CarouselButton label="Anterior" disabled={page === 0} onClick={() => setPage((p) => Math.max(0, p - 1))}>←</CarouselButton>
                      <span className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>{page + 1}/{totalPages}</span>
                      <CarouselButton label="Siguiente" disabled={page >= totalPages - 1} onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}>→</CarouselButton>
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
                          className="chamfer flex flex-col p-4 sm:p-5"
                          style={{ backgroundColor: "var(--surface)", border: `1px solid ${user.is_active ? "var(--border-strong)" : "var(--border-default)"}` }}
                        >
                          <div className="flex items-center gap-3 mb-3">
                            <div className="chamfer-sm flex items-center justify-center w-10 h-10 text-sm font-bold shrink-0" style={{ backgroundColor: "var(--surface-hover)", color: ROLE_COLORS[user.rol] || "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                              {user.nombre_completo.charAt(0).toUpperCase()}
                            </div>
                            <div className="flex flex-col min-w-0">
                              <span className="text-sm sm:text-base font-bold truncate" style={{ color: "var(--text-heading)" }}>{user.nombre_completo}</span>
                              <span className="text-xs truncate" style={{ color: "var(--text-muted)" }}>{user.email}</span>
                            </div>
                          </div>

                          <div className="flex items-center gap-2 mt-auto flex-wrap">
                            <span
                              className="text-[10px] font-bold px-2 py-0.5 chamfer-sm uppercase tracking-wide"
                              style={{ backgroundColor: `color-mix(in srgb, ${ROLE_COLORS[user.rol]} 14%, transparent)`, color: ROLE_COLORS[user.rol], border: `1px solid ${ROLE_COLORS[user.rol]}` }}
                            >
                              {ROLE_LABELS[user.rol] || user.rol}
                            </span>
                            <button
                              type="button"
                              disabled={busyUserId === user.id}
                              onClick={() => toggleUser(user)}
                              className="chamfer-sm px-2 py-0.5 cursor-pointer border-none disabled:opacity-50"
                              style={{ backgroundColor: user.is_active ? "rgba(51,214,159,0.12)" : "rgba(255,71,87,0.12)" }}
                            >
                              <StatusDot variant={user.is_active ? "online" : "danger"} label={user.is_active ? "Activo" : "Inactivo"} />
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
    </div>
  )
}

function StatCard({ label, value, delay, accent }: { label: string; value: string | number; delay: number; accent?: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay }}
      className="chamfer-sm p-4"
      style={{ backgroundColor: "var(--canvas)", border: "1px solid var(--border-default)" }}
    >
      <div className="text-2xl font-bold text-display" style={{ color: accent || "var(--text-heading)" }}>
        {value}
      </div>
      <div className="text-xs mt-1 uppercase tracking-wide" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>{label}</div>
    </motion.div>
  )
}

function SkeletonBlock() {
  return (
    <div className="grid gap-3 sm:gap-4" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))" }}>
      {Array.from({ length: 4 }).map((_, i) => (
        <Skeleton key={i} className="chamfer h-20" style={{ backgroundColor: "var(--surface)" }} />
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
