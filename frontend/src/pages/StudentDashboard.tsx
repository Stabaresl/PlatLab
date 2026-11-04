import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react"
import { Link } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import {
  listAssignments,
  getLaboratorio,
  getHistory,
  getProgresoOverview,
  getCurrentUser,
  acceptInvitation,
  rejectInvitation,
  solicitarConvertirseEnInstructor,
  getMiSolicitudInstructor,
  ApiError,
  type Asignacion,
  type LaboratorioDetalle,
  type SolicitudInstructor,
  type NivelDificultad,
} from "./api"
import Navbar from "../components/Navbar"
import AccesoSalas from "../components/salas/AccesoSalas"
import Footer from "../components/Footer"
import HeroBackground from "../components/HeroBackground"
import SectionHeading from "../components/SectionHeading"
import ProgressRing from "../components/ProgressRing"
import TerminalHeader from "../components/TerminalHeader"
import TiltCard from "../components/TiltCard"
import Revelar from "../components/movimiento/Revelar"
import BarraLlenado from "../components/movimiento/BarraLlenado"
import NumeroAnimado from "../components/movimiento/NumeroAnimado"
import { webglDisponible } from "../lib/webgl"
import type { EsferaProgreso } from "../components/three/NucleoProgreso"
import { IconGauge, IconFlask, IconClock, IconRocket, IconTrophy } from "../components/icons"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Label } from "../components/ui/label"
import { Textarea } from "../components/ui/textarea"
import { Skeleton } from "../components/ui/skeleton"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "../components/ui/dialog"
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "../components/ui/select"

type LabStatus = "completado" | "en_progreso" | "pendiente" | "vencida" | "rechazada"

const NucleoProgreso = lazy(() => import("../components/three/NucleoProgreso"))

interface LabRow {
  assignment: Asignacion
  laboratorio: LaboratorioDetalle | null
  status: LabStatus
  puntaje: number | null
  // null si no se pudo consultar (p. ej. una invitación sin aceptar).
  secciones: { total: number; completadas: number } | null
}

const ESTADO_ESFERA: Record<LabStatus, EsferaProgreso["estado"]> = {
  completado: "integrado",
  en_progreso: "en_curso",
  pendiente: "pendiente",
  vencida: "vencido",
  rechazada: "pendiente",
}

// Qué laboratorios terminados ya vio integrarse este estudiante en este
// navegador: los que falten se animan llegando al núcleo en la próxima visita.
function claveIntegradas() {
  return `platlab.nucleo.${getCurrentUser()?.id ?? "anon"}`
}
function leerIntegradas(): string[] | null {
  try {
    const crudo = localStorage.getItem(claveIntegradas())
    return crudo ? (JSON.parse(crudo) as string[]) : null
  } catch {
    return null
  }
}
function guardarIntegradas(ids: string[]) {
  try {
    localStorage.setItem(claveIntegradas(), JSON.stringify(ids))
  } catch {
    // Sin almacenamiento (modo privado): la próxima visita repite la animación, nada más.
  }
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

// Mismo mapeo que CatalogPage/RoadmapNode — la dificultad siempre se lee
// con el mismo color en toda la plataforma.
const DIFICULTAD_LABEL: Record<NivelDificultad, string> = {
  basico: "Básico",
  intermedio: "Intermedio",
  avanzado: "Avanzado",
}
const DIFICULTAD_COLOR: Record<NivelDificultad, string> = {
  basico: "var(--signal-green)",
  intermedio: "var(--signal-amber)",
  avanzado: "var(--signal-red)",
}

export default function StudentDashboard() {
  const [rows, setRows] = useState<LabRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [busyId, setBusyId] = useState<string | null>(null)
  const [showInstructorModal, setShowInstructorModal] = useState(false)
  const [aperturasModal, setAperturasModal] = useState(0)
  const [instructorForm, setInstructorForm] = useState({
    tipo: "",
    orcid: "",
    institucion: "",
    especialidades: "",
    motivacion: "",
  })

  const [nuevas, setNuevas] = useState<string[]>([])
  const nuevasCalculadas = useRef(false)
  const [conWebgl] = useState(webglDisponible)
  const [ahora] = useState(() => Date.now())

  const loadData = useCallback(() => {
    return listAssignments()
      .then(async (assignments) => {
        const rowsData = await Promise.all(
          assignments
            .filter((a) => a.estado !== "rechazada")
            .map(async (a): Promise<LabRow> => {
              const laboratorio = await getLaboratorio(a.laboratorio_id).catch(() => null)
              let status: LabStatus
              let puntaje: number | null = null
              let secciones: LabRow["secciones"] = null
              if (a.estado === "pendiente") {
                status = "pendiente"
              } else {
                const [historial, progreso] = await Promise.all([
                  a.estado === "vencida" ? Promise.resolve([]) : getHistory(a.id).catch(() => []),
                  getProgresoOverview(a.id).catch(() => null),
                ])
                // Terminado = aprobó el examen (≥60) o el laboratorio no tiene examen (puntaje null).
                // Presentarlo y reprobar deja historial, pero el laboratorio sigue en curso.
                const aprobado = historial.some((h) => h.puntaje == null || h.puntaje >= 60)
                status = a.estado === "vencida" ? "vencida" : aprobado ? "completado" : "en_progreso"
                const puntajes = historial.map((h) => h.puntaje).filter((p): p is number => p != null)
                puntaje = puntajes.length > 0 ? Math.max(...puntajes) : null
                if (progreso) {
                  secciones = {
                    total: progreso.secciones.length,
                    completadas: progreso.secciones.filter((s) => s.estado === "completada").length,
                  }
                }
              }
              return { assignment: a, laboratorio, status, puntaje, secciones }
            }),
        )
        setRows(rowsData)

        // Una sola vez por visita (StrictMode corre el efecto dos veces en desarrollo).
        const terminados = rowsData.filter((r) => r.status === "completado").map((r) => r.assignment.id)
        if (!nuevasCalculadas.current) {
          nuevasCalculadas.current = true
          const vistas = leerIntegradas()
          setNuevas(vistas === null ? terminados : terminados.filter((id) => !vistas.includes(id)))
        }
        guardarIntegradas(terminados)
      })
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "No se pudo cargar tu progreso.")
      })
      .finally(() => {
        setLoading(false)
        setBusyId(null)
      })
  }, [])

  useEffect(() => { loadData() }, [loadData])

  const handleAccept = async (assignmentId: string) => {
    setBusyId(assignmentId)
    try {
      await acceptInvitation(assignmentId)
      await loadData()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo aceptar la invitación.")
      setBusyId(null)
    }
  }

  const handleReject = async (assignmentId: string) => {
    setBusyId(assignmentId)
    try {
      await rejectInvitation(assignmentId)
      await loadData()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo rechazar la invitación.")
      setBusyId(null)
    }
  }

  const completed = rows.filter((r) => r.status === "completado").length
  const inProgress = rows.filter((r) => r.status === "en_progreso").length
  const pendientes = rows.filter((r) => r.status === "pendiente").length
  const vencidos = rows.filter((r) => r.status === "vencida").length
  const total = rows.length
  const pct = total > 0 ? Math.round((completed / total) * 100) : 0

  const esferas = useMemo<EsferaProgreso[]>(
    () =>
      rows.map((r) => ({
        id: r.assignment.id,
        estado: ESTADO_ESFERA[r.status],
        seccionesTotal: r.secciones?.total ?? 0,
        seccionesCompletadas: r.secciones?.completadas ?? 0,
      })),
    [rows],
  )
  const nombresNuevas = rows
    .filter((r) => nuevas.includes(r.assignment.id))
    .map((r) => r.laboratorio?.nombre ?? "un laboratorio")

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
      <HeroBackground image="grim" imageOpacity={0.06} overlayOpacity={0.9} texture="ascii" />
      <div className="relative z-10 flex flex-col min-h-screen">
        <Navbar />
        <main className="flex-1">
          <div className="mx-auto px-4 sm:px-6 md:px-8 py-6 sm:py-8 md:py-10" style={{ maxWidth: "1200px" }}>
            <TerminalHeader title="Panel del Estudiante" subtitle="Bienvenido de vuelta" prompt="whoami → estudiante" />
            <div className="mb-6 sm:mb-8"><AccesoSalas rol="estudiante" /></div>

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
                <Revelar como="section" className="mb-8 sm:mb-10">
                  <SectionHeading icon={<IconGauge />} title="Mi Progreso" subtitle="Cada laboratorio es una esfera en órbita; cuando lo terminas, se suma a tu núcleo" />

                  <div
                    className="chamfer grid lg:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)] overflow-hidden"
                    style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}
                  >
                    <div className="relative" style={{ backgroundColor: "var(--surface-sunken)" }}>
                      {conWebgl ? (
                        <Suspense fallback={<div style={{ height: 320 }} />}>
                          <NucleoProgreso esferas={esferas} nuevas={nuevas} alto={320} />
                        </Suspense>
                      ) : (
                        <div className="flex items-center justify-center" style={{ height: 320 }}>
                          <ProgressRing percent={pct} size={120} label="completado" />
                        </div>
                      )}
                      <span
                        className="absolute left-4 top-3 text-[10px] uppercase tracking-widest pointer-events-none"
                        style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}
                      >
                        núcleo · {completed} de {total} integrados
                      </span>
                    </div>

                    <div className="flex flex-col gap-5 p-4 sm:p-6 border-t lg:border-t-0 lg:border-l" style={{ borderColor: "var(--border-default)" }}>
                      <div className="flex items-end justify-between gap-3">
                        <div className="flex flex-col">
                          <NumeroAnimado
                            valor={pct}
                            sufijo="%"
                            className="text-4xl sm:text-5xl font-bold text-display leading-none"
                            style={{ color: "var(--text-heading)" }}
                          />
                          <span className="mt-2 text-[11px] uppercase tracking-widest" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                            de tus laboratorios terminados
                          </span>
                        </div>
                        <Link
                          to="/roadmap"
                          className="text-[11px] font-semibold no-underline uppercase tracking-wide shrink-0"
                          style={{ color: "var(--signal-amber)", fontFamily: "var(--font-mono)" }}
                        >
                          Roadmap →
                        </Link>
                      </div>

                      {total > 0 && (
                        <BarraLlenado valor={completed} max={total} segmentos color="var(--signal-green)" alto={6} etiqueta={`${completed} de ${total} laboratorios terminados`} />
                      )}

                      <ul className="grid grid-cols-2 gap-x-4 gap-y-3 m-0 p-0 list-none">
                        <FilaLeyenda color="var(--signal-green)" etiqueta="Integrados" valor={completed} relleno />
                        <FilaLeyenda color="var(--signal-cyan)" etiqueta="En curso" valor={inProgress} relleno />
                        <FilaLeyenda color="var(--text-dim)" etiqueta="Invitaciones" valor={pendientes} />
                        <FilaLeyenda color="var(--signal-red)" etiqueta="Vencidos" valor={vencidos} />
                      </ul>

                      <AnimatePresence>
                        {nombresNuevas.length > 0 && (
                          <motion.p
                            initial={{ opacity: 0, y: 6 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 1.2, duration: 0.4 }}
                            className="m-0 text-xs leading-relaxed chamfer-sm px-3 py-2"
                            style={{
                              color: "var(--text-base)",
                              backgroundColor: "color-mix(in srgb, var(--signal-green) 10%, transparent)",
                              border: "1px solid color-mix(in srgb, var(--signal-green) 45%, transparent)",
                            }}
                          >
                            <span style={{ color: "var(--signal-green)", fontFamily: "var(--font-mono)" }}>+{nombresNuevas.length} </span>
                            Se {nombresNuevas.length === 1 ? "sumó" : "sumaron"} a tu núcleo: {nombresNuevas.join(", ")}
                          </motion.p>
                        )}
                      </AnimatePresence>

                      {total === 0 ? (
                        <p className="m-0 text-sm leading-relaxed" style={{ color: "var(--text-muted)" }}>
                          Tu núcleo está solo. Inscríbete en un laboratorio del roadmap y aparecerá en órbita; al terminarlo, se le suma.
                        </p>
                      ) : (
                        <p className="m-0 text-xs leading-relaxed" style={{ color: "var(--text-dim)" }}>
                          Las lunas de cada esfera son sus secciones: se encienden al completarlas y la esfera se acerca al núcleo.
                        </p>
                      )}
                    </div>
                  </div>
                </Revelar>

                {/* ═══ LABORATORIOS ASIGNADOS ═══ */}
                <Revelar como="section" className="mb-8 sm:mb-10">
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
                          >
                            <TiltCard glowColor="56,214,245" intensity={3} className="chamfer flex items-center justify-between p-3 sm:p-4 transition-colors" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
                              <div className="flex flex-col gap-1.5 min-w-0 pr-2">
                                <span className="text-sm sm:text-base font-bold truncate" style={{ color: "var(--text-heading)" }}>
                                  {row.laboratorio?.nombre || `Lab ${row.assignment.laboratorio_id.slice(0, 8)}`}
                                </span>
                                {row.laboratorio && (
                                  <span
                                    className="text-[9px] font-bold px-1.5 py-0.5 chamfer-sm self-start uppercase tracking-wide"
                                    style={{
                                      backgroundColor: `color-mix(in srgb, ${DIFICULTAD_COLOR[row.laboratorio.nivel_dificultad]} 12%, transparent)`,
                                      color: DIFICULTAD_COLOR[row.laboratorio.nivel_dificultad],
                                      border: `1px solid ${DIFICULTAD_COLOR[row.laboratorio.nivel_dificultad]}`,
                                    }}
                                  >
                                    {DIFICULTAD_LABEL[row.laboratorio.nivel_dificultad]}
                                  </span>
                                )}
                                {row.assignment.instructor_nombre && (
                                  <span className="text-[11px] truncate" style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
                                    Invitado por {row.assignment.instructor_nombre}
                                  </span>
                                )}
                                {row.status === "en_progreso" && row.secciones && row.secciones.total > 0 && (
                                  <div className="flex items-center gap-2 mt-0.5" style={{ width: "min(220px, 100%)" }}>
                                    <BarraLlenado
                                      valor={row.secciones.completadas}
                                      max={row.secciones.total}
                                      segmentos
                                      alto={3}
                                      etiqueta={`${row.secciones.completadas} de ${row.secciones.total} secciones`}
                                    />
                                    <span className="text-[10px] shrink-0" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                                      {row.secciones.completadas}/{row.secciones.total}
                                    </span>
                                  </div>
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
                            </TiltCard>
                          </motion.div>
                        ))}
                      </AnimatePresence>
                    </div>
                  )}
                </Revelar>

                {/* ═══ CALIFICACIONES ═══ */}
                <Revelar como="section" className="mb-8 sm:mb-10">
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
                          <TiltCard key={row.assignment.id} glowColor="51,214,159" intensity={3} className="chamfer flex items-center justify-between gap-3 p-3 sm:p-4" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
                            <div className="flex flex-col gap-1.5 min-w-0 pr-2">
                              <span className="text-sm sm:text-base font-bold truncate" style={{ color: "var(--text-heading)" }}>
                                {row.laboratorio?.nombre || `Lab ${row.assignment.laboratorio_id.slice(0, 8)}`}
                              </span>
                              {row.laboratorio && (
                                <span
                                  className="text-[9px] font-bold px-1.5 py-0.5 chamfer-sm self-start uppercase tracking-wide"
                                  style={{
                                    backgroundColor: `color-mix(in srgb, ${DIFICULTAD_COLOR[row.laboratorio.nivel_dificultad]} 12%, transparent)`,
                                    color: DIFICULTAD_COLOR[row.laboratorio.nivel_dificultad],
                                    border: `1px solid ${DIFICULTAD_COLOR[row.laboratorio.nivel_dificultad]}`,
                                  }}
                                >
                                  {DIFICULTAD_LABEL[row.laboratorio.nivel_dificultad]}
                                </span>
                              )}
                              {puntaje != null && (
                                <div className="mt-1" style={{ width: "min(240px, 100%)" }}>
                                  <BarraLlenado valor={puntaje} color={color} alto={3} etiqueta={`Puntaje ${Math.round(puntaje)} de 100`} />
                                </div>
                              )}
                            </div>
                            <div className="flex flex-col items-end gap-1 shrink-0">
                              <span className="text-xl sm:text-2xl font-bold text-display leading-none" style={{ color }}>
                                {puntaje != null ? `${Math.round(puntaje)}%` : "—"}
                              </span>
                              <Link to={`/resolver/${row.assignment.id}`} className="text-xs font-semibold no-underline uppercase tracking-wide" style={{ color: "var(--signal-cyan)", fontFamily: "var(--font-mono)" }}>
                                Ver →
                              </Link>
                            </div>
                          </TiltCard>
                        )
                      })}
                    </div>
                  )}
                </Revelar>

                {/* ═══ VENCIMIENTOS ═══ */}
                <Revelar como="section" className="mb-8 sm:mb-10">
                  <SectionHeading icon={<IconClock />} title="Próximos Vencimientos" />

                  {proximosVencimientos.length === 0 ? (
                    <div className="chamfer p-6 sm:p-8 text-center" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
                      <p className="text-sm m-0" style={{ color: "var(--text-muted)" }}>No tienes laboratorios por vencer.</p>
                    </div>
                  ) : (
                    <div className="flex flex-col gap-2 sm:gap-3">
                      {proximosVencimientos.map((row) => {
                        const diasRestantes = Math.ceil(
                          (new Date(row.assignment.fecha_vencimiento!).getTime() - ahora) / 86_400_000,
                        )
                        return (
                          <TiltCard key={row.assignment.id} glowColor="255,71,87" intensity={3} className="chamfer flex items-center justify-between gap-3 p-3 sm:p-4" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-amber)" }}>
                            <div className="flex flex-col gap-1.5 min-w-0 pr-2">
                              <span className="text-sm sm:text-base font-bold truncate" style={{ color: "var(--text-heading)" }}>
                                {row.laboratorio?.nombre || `Lab ${row.assignment.laboratorio_id.slice(0, 8)}`}
                              </span>
                              <span className="flex items-center gap-1.5 text-xs font-mono" style={{ color: "var(--text-muted)" }}>
                                <IconClock width={12} height={12} style={{ color: "var(--signal-red)" }} />
                                Vence el {new Date(row.assignment.fecha_vencimiento!).toLocaleDateString()}
                              </span>
                            </div>
                            <div className="flex items-center gap-3 shrink-0">
                              <span
                                className={`text-[10px] font-bold px-2 py-1 chamfer-sm whitespace-nowrap uppercase tracking-wide${diasRestantes <= 2 ? " pulso-alerta" : ""}`}
                                style={{ backgroundColor: "color-mix(in srgb, var(--signal-red) 12%, transparent)", color: "var(--signal-red)", border: "1px solid var(--signal-red)" }}
                              >
                                {diasRestantes <= 0 ? "Vence hoy" : `${diasRestantes} día${diasRestantes === 1 ? "" : "s"}`}
                              </span>
                              <Link to={`/resolver/${row.assignment.id}`} className="hidden sm:inline text-xs font-semibold no-underline uppercase tracking-wide" style={{ color: "var(--signal-cyan)", fontFamily: "var(--font-mono)" }}>
                                Continuar →
                              </Link>
                            </div>
                          </TiltCard>
                        )
                      })}
                    </div>
                  )}
                </Revelar>

                {/* ═══ INSTRUCTOR CTA ═══ */}
                <Revelar como="section">
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

                    <Button
                      onClick={() => {
                        setAperturasModal((n) => n + 1)
                        setShowInstructorModal(true)
                      }}
                      className="w-full sm:w-auto chamfer-sm font-mono text-xs uppercase tracking-wide"
                    >
                      Convertirme en Instructor
                    </Button>
                  </div>
                </Revelar>
              </>
            )}
          </div>
        </main>
        <Footer />
      </div>

      {/* La key cambia en cada apertura: el modal arranca con su estado limpio (cargando, sin error). */}
      <InstructorRegistrationModal
        key={aperturasModal}
        open={showInstructorModal}
        form={instructorForm}
        onChange={setInstructorForm}
        onClose={() => setShowInstructorModal(false)}
      />
    </div>
  )
}

/** Una entrada de la leyenda del núcleo: el punto repite el color de la esfera en la escena. */
function FilaLeyenda({ color, etiqueta, valor, relleno = false }: { color: string; etiqueta: string; valor: number; relleno?: boolean }) {
  return (
    <li className="flex items-center gap-2.5 min-w-0">
      <span
        aria-hidden="true"
        className="shrink-0 rounded-full"
        style={{
          width: 10,
          height: 10,
          backgroundColor: relleno ? color : "transparent",
          border: `2px solid ${color}`,
          boxShadow: relleno ? `0 0 8px color-mix(in srgb, ${color} 70%, transparent)` : undefined,
        }}
      />
      <span className="text-[11px] uppercase tracking-wide truncate" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
        {etiqueta}
      </span>
      <NumeroAnimado valor={valor} className="ml-auto text-lg font-bold text-display leading-none" style={{ color: valor > 0 ? color : "var(--text-dim)" }} />
    </li>
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

const ORCID_REGEX = /^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$/

const ESTADO_COPY: Record<SolicitudInstructor["estado"], { titulo: string; texto: (motivo: string | null) => string }> = {
  pendiente: {
    titulo: "Tu solicitud está en revisión",
    texto: () => "Un administrador va a revisar tus datos junto con tu perfil ORCID y te avisaremos por notificación cuando tome una decisión.",
  },
  aprobada: {
    titulo: "¡Ya eres instructor!",
    texto: () => "Un administrador aprobó tu solicitud. Ya puedes crear y publicar laboratorios.",
  },
  rechazada: {
    titulo: "Solicitud no aprobada",
    texto: (motivo) => motivo || "Un administrador revisó tu solicitud y no la aprobó.",
  },
}

function InstructorRegistrationModal({
  open,
  form,
  onChange,
  onClose,
}: {
  open: boolean
  form: { tipo: string; orcid: string; institucion: string; especialidades: string; motivacion: string }
  onChange: (f: typeof form) => void
  onClose: () => void
}) {
  const [estadoActual, setEstadoActual] = useState<SolicitudInstructor | null>(null)
  const [cargando, setCargando] = useState(open)
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState("")
  const update = (field: keyof typeof form, value: string) => onChange({ ...form, [field]: value })

  useEffect(() => {
    if (!open) return
    getMiSolicitudInstructor()
      .then((solicitud) => setEstadoActual(solicitud ?? null))
      .catch(() => setEstadoActual(null))
      .finally(() => setCargando(false))
  }, [open])

  const handleSubmit = async () => {
    setEnviando(true)
    setError("")
    try {
      const resultado = await solicitarConvertirseEnInstructor({
        orcid: form.orcid,
        tipo: form.tipo,
        institucion: form.institucion,
        especialidades: form.especialidades,
        motivacion: form.motivacion,
      })
      setEstadoActual(resultado)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo enviar la solicitud.")
    } finally {
      setEnviando(false)
    }
  }

  const orcidValido = ORCID_REGEX.test(form.orcid)
  const mostrarFormulario = !cargando && (estadoActual === null || estadoActual.estado === "rechazada")

  return (
    <Dialog open={open} onOpenChange={(next) => { if (!next) onClose() }}>
      <DialogContent className="chamfer sm:max-w-lg" style={{ backgroundColor: "var(--canvas-raised)", border: "1px solid var(--border-default)" }}>
        <DialogHeader>
          <DialogTitle className="text-lg font-bold uppercase tracking-wide" style={{ color: "var(--text-heading)" }}>
            Registro de Instructor
          </DialogTitle>
          {mostrarFormulario && (
            <DialogDescription>
              Cuéntanos sobre ti para registrarte como instructor. Verificamos tu ORCID contra
              OpenAlex: el nombre debe coincidir y debes tener al menos un trabajo de
              investigación registrado.
            </DialogDescription>
          )}
        </DialogHeader>

        {cargando ? (
          <div className="py-6 text-center text-sm" style={{ color: "var(--text-muted)" }}>Cargando…</div>
        ) : estadoActual && estadoActual.estado !== "rechazada" ? (
          <div className="flex flex-col items-center gap-3 py-6 text-center">
            <p className="text-sm font-bold uppercase tracking-wide" style={{ color: "var(--text-heading)" }}>
              {ESTADO_COPY[estadoActual.estado].titulo}
            </p>
            <p className="text-sm" style={{ color: "var(--text-base)" }}>
              {ESTADO_COPY[estadoActual.estado].texto(estadoActual.motivo_rechazo)}
            </p>
            <Button onClick={onClose} className="chamfer-sm font-mono text-xs uppercase">Entendido</Button>
          </div>
        ) : (
          <>
            {estadoActual?.estado === "rechazada" && (
              <div className="chamfer-sm px-3 py-2 text-sm" style={{ backgroundColor: "rgba(255,71,87,0.1)", border: "1px solid var(--signal-red)", color: "var(--text-base)" }}>
                {ESTADO_COPY.rechazada.texto(estadoActual.motivo_rechazo)} Puedes intentarlo de nuevo.
              </div>
            )}

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
                <Label className="text-xs uppercase tracking-wide" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                  ORCID <span style={{ color: "var(--signal-red)" }}>*</span>
                </Label>
                <Input
                  value={form.orcid}
                  onChange={(e) => update("orcid", e.target.value)}
                  placeholder="0000-0000-0000-0000"
                  className="chamfer-sm h-10 font-mono"
                />
                {form.orcid.length > 0 && !orcidValido && (
                  <span className="text-xs" style={{ color: "var(--signal-red)" }}>Formato esperado: 0000-0000-0000-0000</span>
                )}
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

              {error && <p className="text-sm" style={{ color: "var(--signal-red)" }}>{error}</p>}
            </div>

            <DialogFooter className="chamfer-t" style={{ backgroundColor: "var(--surface)" }}>
              <Button variant="outline" onClick={onClose} className="chamfer-sm font-mono text-xs uppercase">Cancelar</Button>
              <Button onClick={handleSubmit} disabled={!form.tipo || !orcidValido || enviando} className="chamfer-sm font-mono text-xs uppercase">
                {enviando ? "Enviando…" : "Registrarme como Instructor"}
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
