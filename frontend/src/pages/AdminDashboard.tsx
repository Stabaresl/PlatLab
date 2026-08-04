import { useEffect, useMemo, useState, type ReactNode } from "react"
import { Link } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import {
  getAdminDashboard,
  listUsers,
  listReviewQueue,
  listAudit,
  listPublishedCustomLabs,
  setCatalogVisibility,
  ApiError,
  disableUser,
  enableUser,
  type AdminDashboard as AdminDashboardData,
  type UsuarioItem,
  type Rol,
  type LaboratorioEnRevisionItem,
  type RegistroAuditoriaItem,
  type LaboratorioPersonalizadoPublicadoItem,
} from "./api"
import Navbar from "../components/Navbar"
import Footer from "../components/Footer"
import HeroBackground from "../components/HeroBackground"
import SectionHeading from "../components/SectionHeading"
import ProgressRing from "../components/ProgressRing"
import TerminalHeader from "../components/TerminalHeader"
import StatusDot from "../components/StatusDot"
import TiltCard from "../components/TiltCard"
import ActivityTimeline, { type ActivityItem, type ActivityTone } from "../components/ActivityTimeline"
import { IconChart, IconUsers, IconTrophy, IconFlask, IconActivity, IconGlobe, IconClock } from "../components/icons"
import { Skeleton } from "../components/ui/skeleton"

const AUDIT_LABELS: Record<string, { title: string; tone: ActivityTone }> = {
  user_registered: { title: "Nuevo usuario registrado", tone: "info" },
  user_logged_in: { title: "Inicio de sesión", tone: "neutral" },
  password_reset_requested: { title: "Solicitud de restablecer contraseña", tone: "neutral" },
  oauth_account_linked: { title: "Cuenta vinculada con OAuth", tone: "info" },
  laboratory_published: { title: "Laboratorio publicado", tone: "success" },
  laboratory_duplicated: { title: "Laboratorio duplicado", tone: "info" },
  laboratory_review_requested: { title: "Laboratorio enviado a revisión", tone: "info" },
  laboratory_approved: { title: "Laboratorio aprobado", tone: "success" },
  laboratory_rejected: { title: "Laboratorio rechazado", tone: "warning" },
  laboratory_catalog_visibility_enabled: { title: "Laboratorio publicado en el catálogo", tone: "success" },
  laboratory_catalog_visibility_disabled: { title: "Laboratorio retirado del catálogo", tone: "neutral" },
  instructor_verification_requested: { title: "Solicitud de instructor recibida", tone: "info" },
  instructor_verification_approved: { title: "Instructor verificado vía OpenAlex", tone: "success" },
  instructor_verification_rejected: { title: "Verificación de instructor rechazada", tone: "warning" },
  flag_validated: { title: "Flag capturada", tone: "success" },
  section_completed: { title: "Sección completada", tone: "success" },
  lab_completed: { title: "Laboratorio completado", tone: "success" },
  exam_graded: { title: "Examen calificado", tone: "info" },
  assignment_invited: { title: "Estudiante invitado a un laboratorio", tone: "info" },
  assignment_accepted: { title: "Invitación aceptada", tone: "success" },
  assignment_rejected: { title: "Invitación rechazada", tone: "warning" },
  assignment_expired: { title: "Acceso vencido", tone: "warning" },
  report_submitted: { title: "Reporte enviado", tone: "warning" },
  report_resolved: { title: "Reporte resuelto", tone: "success" },
}

function auditToItem(r: RegistroAuditoriaItem): ActivityItem {
  const meta = AUDIT_LABELS[r.accion] || { title: r.accion, tone: "neutral" as const }
  return {
    id: r.id,
    title: meta.title,
    description: r.entidad_tipo ? `${r.entidad_tipo}${r.entidad_id ? " · " + r.entidad_id.slice(0, 8) : ""}` : undefined,
    timestamp: r.timestamp,
    tone: meta.tone,
  }
}

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

// TiltCard/MouseGlow reciben el color como "R,G,B" (para inyectarlo en un
// radial-gradient) — no se puede resolver un var(--signal-*) a RGB desde
// JS sin getComputedStyle, así que este mapa espeja los mismos tonos.
const ROLE_GLOW: Record<Rol, string> = {
  estudiante: "56,214,245",
  instructor: "51,214,159",
  administrador: "255,176,32",
}

export default function AdminDashboard() {
  const [dashboard, setDashboard] = useState<AdminDashboardData | null>(null)
  const [users, setUsers] = useState<UsuarioItem[]>([])
  const [reviewQueue, setReviewQueue] = useState<LaboratorioEnRevisionItem[]>([])
  const [auditLog, setAuditLog] = useState<RegistroAuditoriaItem[]>([])
  const [customLabs, setCustomLabs] = useState<LaboratorioPersonalizadoPublicadoItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [busyUserId, setBusyUserId] = useState<string | null>(null)
  const [visibilityBusyId, setVisibilityBusyId] = useState<string | null>(null)

  const PAGE_SIZE = 4
  const [page, setPage] = useState(0)
  const totalPages = Math.max(1, Math.ceil(users.length / PAGE_SIZE))
  const visible = users.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  // Ordenar+mapear el log completo es lo único realmente caro acá — sin
  // memo, cambiar de página o togglear un usuario (busyUserId,
  // visibilityBusyId) volvía a ordenar todo el historial de auditoría
  // en cada render aunque auditLog no hubiera cambiado.
  const actividadReciente = useMemo(
    () =>
      [...auditLog]
        .sort((a, b) => b.timestamp.localeCompare(a.timestamp))
        .slice(0, 10)
        .map(auditToItem),
    [auditLog],
  )

  useEffect(() => {
    let cancelled = false
    Promise.all([getAdminDashboard(), listUsers(), listReviewQueue(), listAudit(), listPublishedCustomLabs()])
      .then(([dashboardData, usersData, reviewQueueData, auditData, customLabsData]) => {
        if (cancelled) return
        setDashboard(dashboardData)
        setUsers(usersData)
        setReviewQueue(reviewQueueData)
        setAuditLog(auditData)
        setCustomLabs(customLabsData)
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
      setCustomLabs((prev) =>
        prev.map((l) => (l.id === laboratorioId ? { ...l, visible_en_catalogo: next } : l)),
      )
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo actualizar la visibilidad en el catálogo.")
    } finally {
      setVisibilityBusyId(null)
    }
  }

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
                        <TiltCard glowColor="56,214,245" className="chamfer-sm">
                          <StatCard
                            label="Laboratorios activos"
                            value={dashboard.laboratorios_activos}
                            delay={0}
                            accent="var(--signal-cyan)"
                            icon={<IconFlask width={16} height={16} />}
                          />
                        </TiltCard>
                        {Object.entries(dashboard.usuarios_por_rol).map(([rol, cantidad], i) => (
                          <TiltCard key={rol} glowColor={ROLE_GLOW[rol as Rol] || "56,214,245"} className="chamfer-sm">
                            <StatCard
                              label={ROLE_LABELS[rol as Rol] || rol}
                              value={cantidad}
                              delay={0.1 + i * 0.05}
                              accent={ROLE_COLORS[rol as Rol]}
                              icon={<IconUsers width={16} height={16} />}
                            />
                          </TiltCard>
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

                {/* ═══ ACTIVIDAD RECIENTE ═══ */}
                <section className="mb-8 sm:mb-10">
                  <SectionHeading icon={<IconActivity />} title="Actividad Reciente" subtitle="Últimas operaciones registradas en la plataforma" />
                  <div className="chamfer p-4 sm:p-5" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
                    <ActivityTimeline
                      items={actividadReciente}
                      emptyLabel="Todavía no hay actividad registrada"
                    />
                  </div>
                </section>

                {/* ═══ COLA DE REVISIÓN ═══ */}
                <section className="mb-8 sm:mb-10">
                  <SectionHeading icon={<IconFlask />} title="Cola de Revisión" subtitle={`${reviewQueue.length} laboratorio(s) esperando aprobación`} />

                  {reviewQueue.length === 0 ? (
                    <div className="chamfer p-8 text-center" style={{ border: "1px dashed var(--border-strong)" }}>
                      <p className="text-xs uppercase tracking-widest m-0" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                        [ Nada pendiente de revisión ]
                      </p>
                    </div>
                  ) : (
                    <div className="grid gap-3 sm:gap-4" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))" }}>
                      <AnimatePresence mode="popLayout">
                        {reviewQueue.map((lab) => (
                          <motion.div
                            key={lab.id}
                            layout
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            transition={{ duration: 0.25 }}
                          >
                            <TiltCard
                              glowColor="255,176,32"
                              className="chamfer flex flex-col p-4 sm:p-5 h-full"
                              style={{ backgroundColor: "var(--surface)", border: "1px solid var(--signal-amber)" }}
                            >
                              <span
                                className="text-[10px] font-bold px-2 py-0.5 chamfer-sm self-start mb-2.5 uppercase tracking-wide"
                                style={{ backgroundColor: "rgba(255,176,32,0.12)", color: "var(--signal-amber)", border: "1px solid var(--signal-amber)" }}
                              >
                                Pendiente
                              </span>
                              <span className="text-sm sm:text-base font-bold mb-2 leading-snug" style={{ color: "var(--text-heading)" }}>{lab.nombre}</span>
                              <span className="flex items-center gap-1.5 text-xs mb-4" style={{ color: "var(--text-muted)" }}>
                                <IconClock width={12} height={12} />
                                {lab.updated_at ? `Enviado el ${new Date(lab.updated_at).toLocaleDateString()}` : "Fecha no disponible"}
                              </span>
                              <Link
                                to={`/laboratorios/${lab.id}/revision`}
                                className="flex items-center justify-center gap-2 chamfer-sm px-3 py-1.5 text-xs font-mono uppercase tracking-wide text-center mt-auto no-underline transition-colors"
                                style={{ backgroundColor: "rgba(255,176,32,0.12)", color: "var(--signal-amber)", border: "1px solid var(--border-amber)" }}
                              >
                                <IconFlask width={13} height={13} />
                                Revisar
                              </Link>
                            </TiltCard>
                          </motion.div>
                        ))}
                      </AnimatePresence>
                    </div>
                  )}
                </section>

                {/* ═══ CATÁLOGO — LABORATORIOS DE INSTRUCTORES ═══ */}
                <section className="mb-8 sm:mb-10">
                  <SectionHeading
                    icon={<IconGlobe />}
                    title="Catálogo de Instructores"
                    subtitle="Laboratorios personalizados publicados — decide cuáles son autoinscribibles desde el catálogo público"
                  />

                  {customLabs.length === 0 ? (
                    <div className="chamfer p-8 text-center" style={{ border: "1px dashed var(--border-strong)" }}>
                      <p className="text-xs uppercase tracking-widest m-0" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                        [ Ningún instructor tiene laboratorios publicados todavía ]
                      </p>
                    </div>
                  ) : (
                    <div className="chamfer overflow-hidden" style={{ border: "1px solid var(--border-default)" }}>
                      {customLabs.map((lab, i) => (
                        <div
                          key={lab.id}
                          className="flex items-center justify-between gap-3 px-4 sm:px-5 py-3 sm:py-3.5"
                          style={{
                            backgroundColor: i % 2 === 0 ? "var(--surface)" : "var(--canvas)",
                            borderBottom: i < customLabs.length - 1 ? "1px solid var(--border-default)" : "none",
                          }}
                        >
                          <span className="text-xs sm:text-sm font-medium truncate" style={{ color: "var(--text-heading)" }}>
                            {lab.nombre}
                          </span>
                          <button
                            type="button"
                            disabled={visibilityBusyId === lab.id}
                            onClick={() => handleToggleVisibility(lab.id, !lab.visible_en_catalogo)}
                            className="shrink-0 flex items-center gap-2 chamfer-sm px-2.5 py-1.5 text-[11px] font-semibold uppercase tracking-wide cursor-pointer border transition-colors disabled:opacity-50 disabled:cursor-wait"
                            style={{
                              backgroundColor: lab.visible_en_catalogo ? "rgba(51,214,159,0.1)" : "transparent",
                              borderColor: lab.visible_en_catalogo ? "var(--signal-green)" : "var(--border-default)",
                              color: lab.visible_en_catalogo ? "var(--signal-green)" : "var(--text-muted)",
                              fontFamily: "var(--font-mono)",
                            }}
                          >
                            <IconGlobe width={13} height={13} />
                            {visibilityBusyId === lab.id
                              ? "Actualizando…"
                              : lab.visible_en_catalogo
                                ? "En catálogo público"
                                : "Publicar en catálogo"}
                          </button>
                        </div>
                      ))}
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
                        >
                          <TiltCard
                            glowColor={ROLE_GLOW[user.rol] || "56,214,245"}
                            className="chamfer flex flex-col p-4 sm:p-5 h-full"
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
                          </TiltCard>
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

function StatCard({ label, value, delay, accent, icon }: { label: string; value: string | number; delay: number; accent?: string; icon?: ReactNode }) {
  const color = accent || "var(--text-heading)"
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay }}
      className="chamfer-sm flex items-center gap-3 p-4"
      style={{ backgroundColor: "var(--canvas)", border: "1px solid var(--border-default)" }}
    >
      {icon && (
        <div className="chamfer-sm flex items-center justify-center w-9 h-9 shrink-0" style={{ backgroundColor: `color-mix(in srgb, ${color} 14%, transparent)`, color }}>
          {icon}
        </div>
      )}
      <div className="flex flex-col min-w-0">
        <span className="text-xl sm:text-2xl font-bold text-display leading-tight" style={{ color }}>
          {value}
        </span>
        <span className="text-[11px] uppercase tracking-wide truncate" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>{label}</span>
      </div>
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
