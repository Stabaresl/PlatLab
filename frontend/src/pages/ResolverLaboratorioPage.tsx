import { useEffect, useRef, useState, type FormEvent } from "react"
import { useParams, useNavigate, Link } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import {
  getProgresoOverview,
  getSectionContent,
  submitFlag,
  completeTheorySection,
  getHint,
  getExamen,
  submitExam,
  startLabEnvironment,
  stopLabEnvironment,
  getLabEnvironmentStatus,
  ApiError,
  type ProgresoOverview,
  type SeccionProgreso,
  type PreguntaExamen,
  type ContenidoSeccion,
  type EntornoRealEstado,
} from "./api"
import { ContenidoHtml, PasosGuia } from "../components/ContenidoSeccion"
import Navbar from "../components/Navbar"
import Footer from "../components/Footer"
import ProgressRing from "../components/ProgressRing"
import StatusDot from "../components/StatusDot"
import SimulatedTerminal, { type ConsolaHandle } from "../components/SimulatedTerminal"
import RealTerminal from "../components/RealTerminal"
import { IconExam, IconLock, IconClock } from "../components/icons"
import { Button } from "../components/ui/button"
import { Skeleton } from "../components/ui/skeleton"

type Vista = { tipo: "seccion"; id: string } | { tipo: "examen" }

const UMBRAL_PISTA = 5
const UMBRAL_PASO_A_PASO = 15

export default function ResolverLaboratorioPage() {
  const { assignmentId } = useParams<{ assignmentId: string }>()
  const navigate = useNavigate()

  const [overview, setOverview] = useState<ProgresoOverview | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [vista, setVista] = useState<Vista | null>(null)

  const loadOverview = () => {
    if (!assignmentId) return
    return getProgresoOverview(assignmentId)
      .then((data) => {
        setOverview(data)
        const activa = data.secciones.find((s) => s.estado === "en_progreso")
        const primera = data.secciones[0]
        setVista((prev) => prev || { tipo: "seccion", id: (activa || primera)?.id })
        return data
      })
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "No se pudo cargar el laboratorio.")
      })
  }

  const [ahora] = useState(() => Date.now())

  useEffect(() => {
    Promise.resolve(loadOverview()).finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [assignmentId])

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col" style={{ backgroundColor: "var(--canvas)" }}>
        <Navbar />
        <main className="flex-1 flex items-center justify-center">
          <p className="text-sm animate-pulse" style={{ color: "var(--signal-amber)", fontFamily: "var(--font-mono)" }}>
            &gt; cargando laboratorio<span className="inline-block" style={{ animation: "blink 1s step-start infinite" }}>▌</span>
          </p>
        </main>
        <Footer />
      </div>
    )
  }

  if (error || !overview || !assignmentId) {
    return (
      <div className="min-h-screen flex flex-col" style={{ backgroundColor: "var(--canvas)", color: "var(--text-base)" }}>
        <Navbar />
        <main className="flex-1 flex flex-col items-center justify-center gap-4 px-4 text-center">
          <p className="text-sm px-3 py-2 chamfer-sm" style={{ color: "var(--signal-red)", backgroundColor: "color-mix(in srgb, var(--signal-red) 8%, transparent)", border: "1px solid var(--signal-red-dim)" }}>▲ {error || "Laboratorio no encontrado."}</p>
          <Link to="/dashboard" className="text-sm font-semibold no-underline uppercase tracking-wide" style={{ color: "var(--signal-cyan)", fontFamily: "var(--font-mono)" }}>
            ← Volver a mi Dashboard
          </Link>
        </main>
        <Footer />
      </div>
    )
  }

  const totalSecciones = overview.secciones.length
  const completadas = overview.secciones.filter((s) => s.estado === "completada").length
  const pctGlobal = totalSecciones > 0 ? Math.round((completadas / totalSecciones) * 100) : 0
  const vencido = overview.vencido
  const diasRestantes = overview.fecha_vencimiento
    ? Math.ceil((new Date(overview.fecha_vencimiento).getTime() - ahora) / 86_400_000)
    : null

  return (
    <div className="relative min-h-screen" style={{ backgroundColor: "var(--canvas)", color: "var(--text-base)" }}>
      <div className="relative z-10 flex flex-col min-h-screen">
        <Navbar />
        <main className="flex-1">
          <div className="mx-auto px-4 sm:px-6 md:px-8 py-6 sm:py-8" style={{ maxWidth: "1480px" }}>
            <button
              type="button"
              onClick={() => navigate("/dashboard")}
              className="text-xs sm:text-sm mb-4 cursor-pointer border-none bg-transparent px-0 uppercase tracking-wide"
              style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
            >
              ← Volver a mi Dashboard
            </button>

            {/* ═══ Encabezado del laboratorio ═══ */}
            <header className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 pb-5 mb-6" style={{ borderBottom: "1px solid var(--border-default)" }}>
              <div className="min-w-0">
                <StatusDot variant={overview.secciones_completas ? "online" : "active"} label={overview.secciones_completas ? "Secciones completas" : "Laboratorio en curso"} pulse={!overview.secciones_completas} />
                <h1 className="text-xl sm:text-2xl md:text-3xl font-black uppercase mt-2 mb-0 leading-tight" style={{ color: "var(--text-heading)", fontFamily: "var(--font-display)", overflowWrap: "anywhere" }}>
                  {overview.laboratorio_nombre}
                </h1>
              </div>
              <div className="flex flex-col sm:items-end gap-1.5 shrink-0">
                <div className="flex items-center gap-3">
                  <span className="text-xs" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                    {completadas}/{totalSecciones} secciones
                  </span>
                  <div className="w-36 sm:w-44 h-1.5 overflow-hidden" style={{ backgroundColor: "var(--surface-hover)" }}>
                    <motion.div initial={{ scaleX: 0 }} animate={{ scaleX: pctGlobal / 100 }} transition={{ duration: 0.5, ease: [0.19, 1, 0.22, 1] }} className="h-full origin-left" style={{ backgroundColor: "var(--signal-amber)" }} />
                  </div>
                  <span className="text-sm font-bold shrink-0" style={{ color: "var(--signal-amber)", fontFamily: "var(--font-mono)" }}>{pctGlobal}%</span>
                </div>
                {overview.fecha_vencimiento && !vencido && diasRestantes !== null && (
                  <span className="text-[11px] uppercase tracking-wide" style={{ color: diasRestantes <= 5 ? "var(--signal-red)" : "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                    Vence en {Math.max(diasRestantes, 0)} día{diasRestantes === 1 ? "" : "s"} ({new Date(overview.fecha_vencimiento).toLocaleDateString()})
                  </span>
                )}
              </div>
            </header>

            {vencido && (
              <div className="chamfer flex items-center gap-3 p-4 mb-6" style={{ backgroundColor: "color-mix(in srgb, var(--signal-red) 8%, transparent)", border: "1px solid var(--signal-red)" }}>
                <IconLock style={{ color: "var(--signal-red)" }} className="shrink-0" />
                <p className="text-sm m-0" style={{ color: "var(--signal-red)" }}>
                  Este laboratorio venció{overview.fecha_vencimiento ? ` el ${new Date(overview.fecha_vencimiento).toLocaleDateString()}` : ""}. Puedes revisar el contenido, pero ya no se puede enviar flags, continuar secciones ni presentar el examen.
                </p>
              </div>
            )}

            {overview.secciones_completas && overview.resumen_cierre && (
              <section className="chamfer p-5 mb-6" style={{ backgroundColor: "color-mix(in srgb, var(--signal-green) 6%, transparent)", border: "1px solid var(--signal-green-dim)" }}>
                <h2 className="text-xs font-bold uppercase tracking-wider m-0 mb-3" style={{ color: "var(--signal-green)", fontFamily: "var(--font-mono)" }}>Conclusión del laboratorio</h2>
                <ContenidoHtml html={overview.resumen_cierre} />
              </section>
            )}

            <div className="flex flex-col lg:flex-row gap-6">
              {/* ═══ Índice de secciones ═══ */}
              <nav aria-label="Secciones del laboratorio" className="w-full lg:w-60 shrink-0 lg:sticky lg:top-20 self-start">
                <ol className="m-0 p-0 list-none flex flex-col">
                  {overview.secciones.map((s, i) => {
                    const active = vista?.tipo === "seccion" && vista.id === s.id
                    return (
                      <li key={s.id}>
                        <button
                          type="button"
                          disabled={s.estado === "bloqueada"}
                          onClick={() => setVista({ tipo: "seccion", id: s.id })}
                          aria-current={active ? "step" : undefined}
                          className="w-full relative flex items-start gap-3 text-left px-2.5 py-2.5 transition-colors disabled:cursor-not-allowed disabled:opacity-45 cursor-pointer border-none"
                          style={{ backgroundColor: active ? "var(--surface)" : "transparent", borderLeft: `2px solid ${active ? "var(--signal-amber)" : "transparent"}` }}
                        >
                          <div className="flex flex-col items-center shrink-0">
                            <SeccionNode estado={s.estado} orden={s.orden} />
                            {i < overview.secciones.length - 1 && (
                              <span className="w-px flex-1 mt-1" style={{ backgroundColor: s.estado === "completada" ? "var(--signal-green)" : "var(--border-default)", minHeight: 14 }} />
                            )}
                          </div>
                          <span className="flex-1 text-sm pt-1 leading-snug" style={{ color: active ? "var(--text-heading)" : "var(--text-base)", fontWeight: active ? 600 : 400 }}>
                            {s.titulo}
                          </span>
                        </button>
                      </li>
                    )
                  })}
                  <li>
                    <button
                      type="button"
                      disabled={!overview.secciones_completas || !overview.examen_disponible}
                      onClick={() => setVista({ tipo: "examen" })}
                      className="w-full flex items-center gap-3 text-left px-2.5 py-2.5 mt-1 transition-colors disabled:cursor-not-allowed disabled:opacity-45 cursor-pointer border-none"
                      style={{ backgroundColor: vista?.tipo === "examen" ? "var(--surface)" : "transparent", borderTop: "1px solid var(--border-default)" }}
                    >
                      <span className="chamfer-sm flex items-center justify-center w-7 h-7 shrink-0" style={{ backgroundColor: "color-mix(in srgb, var(--signal-amber) 12%, transparent)", color: "var(--signal-amber)", border: "1px solid var(--border-amber)" }}>
                        <IconExam width={14} height={14} />
                      </span>
                      <span className="flex-1 text-sm font-semibold" style={{ color: "var(--signal-amber)" }}>Examen final</span>
                    </button>
                  </li>
                </ol>
              </nav>

              {/* ═══ Área de trabajo ═══ */}
              <div className="flex-1 min-w-0">
                {vista?.tipo === "examen" ? (
                  <ExamenPanel assignmentId={assignmentId} onDone={loadOverview} vencido={vencido} />
                ) : vista?.tipo === "seccion" ? (
                  <SeccionPanel
                    key={vista.id}
                    assignmentId={assignmentId}
                    seccionId={vista.id}
                    seccionMeta={overview.secciones.find((s) => s.id === vista.id)}
                    totalSecciones={totalSecciones}
                    vencido={vencido}
                    onCompletada={(desbloqueada) => {
                      loadOverview()
                      if (desbloqueada) setVista({ tipo: "seccion", id: desbloqueada })
                    }}
                  />
                ) : (
                  <p className="text-sm" style={{ color: "var(--text-muted)" }}>Elige una sección para empezar.</p>
                )}
              </div>
            </div>
          </div>
        </main>
        <Footer />
      </div>
    </div>
  )
}

function SeccionNode({ estado, orden }: { estado: SeccionProgreso["estado"]; orden: number }) {
  if (estado === "completada") {
    return (
      <span className="chamfer-sm flex items-center justify-center w-7 h-7 text-xs font-bold shrink-0" style={{ backgroundColor: "var(--signal-green)", color: "var(--canvas)", fontFamily: "var(--font-mono)" }}>
        ✓
      </span>
    )
  }
  if (estado === "en_progreso") {
    return (
      <span className="chamfer-sm flex items-center justify-center w-7 h-7 text-xs font-bold shrink-0" style={{ backgroundColor: "color-mix(in srgb, var(--signal-amber) 14%, transparent)", color: "var(--signal-amber)", border: "1px solid var(--signal-amber)", fontFamily: "var(--font-mono)" }}>
        {orden}
      </span>
    )
  }
  return (
    <span className="chamfer-sm flex items-center justify-center w-7 h-7 text-xs shrink-0" style={{ backgroundColor: "var(--surface-hover)", color: "var(--text-dim)", border: "1px solid var(--border-default)" }}>
      <IconLock width={12} height={12} />
    </span>
  )
}

function Chip({ children, color }: { children: React.ReactNode; color: string }) {
  return (
    <span className="chamfer-sm inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 uppercase tracking-wider" style={{ backgroundColor: `color-mix(in srgb, ${color} 12%, transparent)`, color, border: `1px solid color-mix(in srgb, ${color} 45%, transparent)`, fontFamily: "var(--font-mono)" }}>
      {children}
    </span>
  )
}

function SeccionPanel({
  assignmentId,
  seccionId,
  seccionMeta,
  totalSecciones,
  vencido,
  onCompletada,
}: {
  assignmentId: string
  seccionId: string
  seccionMeta?: SeccionProgreso
  totalSecciones: number
  vencido: boolean
  onCompletada: (seccionDesbloqueada?: string | null) => void
}) {
  const [contenido, setContenido] = useState<ContenidoSeccion | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [flagValor, setFlagValor] = useState("")
  const [busy, setBusy] = useState(false)
  const [feedback, setFeedback] = useState<{ ok: boolean; msg: string } | null>(null)
  const [ayuda, setAyuda] = useState<{ intentos: number; pista?: string; pasoAPaso?: string } | null>(null)
  const [ayudaBusy, setAyudaBusy] = useState(false)
  const [consola, setConsola] = useState<"simulada" | "real">("simulada")
  const [entornoReal, setEntornoReal] = useState<EntornoRealEstado | null>(null)
  const [entornoBusy, setEntornoBusy] = useState(false)
  const [entornoError, setEntornoError] = useState("")
  const consolaRef = useRef<ConsolaHandle>(null)
  const zonaConsolaRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    getSectionContent(assignmentId, seccionId)
      .then((data) => {
        setContenido(data)
        if (!data.entorno_practica && data.entorno_real_disponible) setConsola("real")
        if (data.entorno_real_disponible) {
          getLabEnvironmentStatus(assignmentId, seccionId).then(setEntornoReal).catch(() => {})
        }
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "No se pudo cargar la sección."))
      .finally(() => setLoading(false))
  }, [assignmentId, seccionId])

  const ejecutarEnConsola = (comando: string) => {
    setConsola("simulada")
    // En pantallas angostas la consola queda debajo de la guía: se lleva a la vista.
    if (window.matchMedia("(max-width: 1279px)").matches) zonaConsolaRef.current?.scrollIntoView({ behavior: "smooth", block: "start" })
    setTimeout(() => consolaRef.current?.ejecutar(comando), 60)
  }

  const handleIniciarEntorno = async () => {
    setEntornoBusy(true)
    setEntornoError("")
    try {
      const resultado = await startLabEnvironment(assignmentId, seccionId)
      if (resultado.estado === "activo") {
        setEntornoReal({ activo: true, ...resultado })
        return
      }
      // El contenedor arranca en segundo plano (Celery): se espera a que /status/ diga "activo".
      await pollHastaActivoOError()
    } catch (err) {
      setEntornoError(err instanceof ApiError ? err.message : "No se pudo iniciar el entorno.")
    } finally {
      setEntornoBusy(false)
    }
  }

  const pollHastaActivoOError = async () => {
    for (let intento = 0; intento < 30; intento++) {
      await new Promise((resolve) => setTimeout(resolve, 1500))
      const estado = await getLabEnvironmentStatus(assignmentId, seccionId)
      if (estado.activo && estado.estado === "activo") {
        setEntornoReal(estado)
        return
      }
      if (!estado.activo) {
        setEntornoError("No se pudo iniciar el entorno de práctica. Inténtalo de nuevo en unos minutos.")
        return
      }
    }
    setEntornoError("El entorno está tardando más de lo esperado. Inténtalo de nuevo en unos minutos.")
  }

  const handleDetenerEntorno = async () => {
    if (!entornoReal?.id) return
    setEntornoBusy(true)
    try {
      await stopLabEnvironment(entornoReal.id)
      setEntornoReal({ activo: false })
    } catch (err) {
      setEntornoError(err instanceof ApiError ? err.message : "No se pudo detener el entorno.")
    } finally {
      setEntornoBusy(false)
    }
  }

  const handleSubmitFlag = async (e: FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setFeedback(null)
    try {
      const resultado = await submitFlag(assignmentId, seccionId, flagValor.trim())
      if (resultado.correcto) {
        setFeedback({ ok: true, msg: "¡Correcto! Sección completada." })
        setTimeout(() => onCompletada(resultado.seccion_desbloqueada), 900)
      } else {
        setFeedback({
          ok: false,
          msg: `Incorrecto (${resultado.intentos_fallidos} intento${resultado.intentos_fallidos === 1 ? "" : "s"} fallido${resultado.intentos_fallidos === 1 ? "" : "s"}).`,
        })
        setAyuda({
          intentos: resultado.intentos_fallidos ?? 0,
          pista: resultado.pista_disponible ? resultado.pista : undefined,
          pasoAPaso: resultado.paso_a_paso_disponible ? resultado.paso_a_paso : undefined,
        })
      }
    } catch (err) {
      setFeedback({ ok: false, msg: err instanceof ApiError ? err.message : "No se pudo validar la flag." })
    } finally {
      setBusy(false)
    }
  }

  const handleContinuar = async () => {
    setBusy(true)
    setFeedback(null)
    try {
      const resultado = await completeTheorySection(assignmentId, seccionId)
      onCompletada(resultado.seccion_desbloqueada)
    } catch (err) {
      setFeedback({ ok: false, msg: err instanceof ApiError ? err.message : "No se pudo continuar." })
      setBusy(false)
    }
  }

  const handlePedirAyuda = async () => {
    setAyudaBusy(true)
    try {
      const pista = await getHint(assignmentId, seccionId)
      setAyuda({
        intentos: pista.intentos_fallidos,
        pista: pista.pista_disponible ? pista.pista : undefined,
        pasoAPaso: pista.paso_a_paso_disponible ? pista.paso_a_paso : undefined,
      })
    } catch (err) {
      setFeedback({ ok: false, msg: err instanceof ApiError ? err.message : "No se pudo obtener la ayuda." })
    } finally {
      setAyudaBusy(false)
    }
  }

  if (loading) {
    return <Skeleton className="chamfer h-64" style={{ backgroundColor: "var(--surface)" }} />
  }
  if (error || !contenido) {
    return <p className="text-sm px-3 py-2 chamfer-sm" style={{ color: "var(--signal-red)", backgroundColor: "color-mix(in srgb, var(--signal-red) 8%, transparent)", border: "1px solid var(--signal-red-dim)" }}>▲ {error || "Sección no disponible."}</p>
  }

  const completada = contenido.estado === "completada"
  const tieneGuia = contenido.pasos_guia.length > 0
  const progresoKey = `platlab:tareas:${assignmentId}:${seccionId}`
  const tieneSimulada = Boolean(contenido.entorno_practica)
  const tieneReal = contenido.entorno_real_disponible

  const encabezado = (
    <header className="flex flex-col gap-3 mb-5">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-[11px] uppercase tracking-wider" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
          Sección {seccionMeta?.orden} de {totalSecciones}
        </span>
        <Chip color={contenido.tiene_practica ? "var(--signal-cyan)" : "var(--text-muted)"}>{contenido.tiene_practica ? "Práctica" : "Lectura"}</Chip>
        {contenido.duracion_estimada_minutos > 0 && (
          <Chip color="var(--text-muted)">
            <IconClock width={11} height={11} /> {contenido.duracion_estimada_minutos} min
          </Chip>
        )}
        {completada && <Chip color="var(--signal-green)">✓ Completada</Chip>}
        <button
          type="button"
          onClick={() => window.open(`/resolver/${assignmentId}/secciones/${seccionId}/material?modo=${tieneGuia ? "guia" : "teoria"}`, "_blank", "noopener,noreferrer")}
          className="consola-btn ml-auto"
          title="Abre la guía en otra pestaña para tenerla al lado mientras practicas"
        >
          ↗ Guía en otra pestaña
        </button>
      </div>
      <h2 className="text-xl sm:text-2xl font-bold m-0 leading-tight" style={{ color: "var(--text-heading)", fontFamily: "var(--font-body)", overflowWrap: "anywhere" }}>
        {contenido.titulo}
      </h2>
      {contenido.objetivos.length > 0 && (
        <div className="chamfer-sm p-4" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
          <h3 className="text-[11px] font-bold uppercase tracking-wider m-0 mb-2" style={{ color: "var(--signal-cyan)", fontFamily: "var(--font-mono)" }}>Al terminar esta sección podrás</h3>
          <ul className="m-0 p-0 list-none flex flex-col gap-1.5">
            {contenido.objetivos.map((o, i) => (
              <li key={i} className="flex items-start gap-2 text-sm" style={{ color: "var(--text-base)" }}>
                <span aria-hidden="true" style={{ color: "var(--signal-cyan)" }}>▸</span>
                {o}
              </li>
            ))}
          </ul>
        </div>
      )}
    </header>
  )

  if (!contenido.tiene_practica) {
    return (
      <motion.article initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.2 }} className="max-w-[78ch]">
        {encabezado}
        <ContenidoHtml html={contenido.contenido_teorico} />
        {tieneGuia && (
          <section className="mt-8">
            <h3 className="text-sm font-bold uppercase tracking-wider m-0 mb-3" style={{ color: "var(--text-heading)", fontFamily: "var(--font-mono)" }}>Repaso guiado</h3>
            <PasosGuia pasos={contenido.pasos_guia} progresoKey={progresoKey} />
          </section>
        )}
        {!completada && (
          <div className="flex flex-col gap-3 pt-5 mt-8" style={{ borderTop: "1px solid var(--border-default)" }}>
            <p className="text-sm m-0" style={{ color: "var(--text-muted)" }}>Cuando termines de leer, continúa: la siguiente sección se desbloquea.</p>
            <Button type="button" onClick={handleContinuar} disabled={busy || vencido} className="self-start chamfer-sm font-mono text-xs uppercase tracking-wide">
              {busy ? "Avanzando…" : "Continuar →"}
            </Button>
            <AnimatePresence>{feedback && !feedback.ok && <Aviso ok={false} msg={feedback.msg} />}</AnimatePresence>
          </div>
        )}
      </motion.article>
    )
  }

  return (
    <motion.article initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.2 }}>
      {encabezado}
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(0,1.08fr)] items-start">
        {/* Guía */}
        <div className="flex flex-col gap-6 min-w-0">
          <ContenidoHtml html={contenido.contenido_teorico} />
          {tieneGuia && (
            <section>
              <h3 className="text-sm font-bold uppercase tracking-wider m-0 mb-3" style={{ color: "var(--text-heading)", fontFamily: "var(--font-mono)" }}>Tareas</h3>
              <PasosGuia pasos={contenido.pasos_guia} onEjecutar={tieneSimulada ? ejecutarEnConsola : undefined} progresoKey={progresoKey} />
            </section>
          )}
        </div>

        {/* Consola + flag */}
        <div ref={zonaConsolaRef} className="flex flex-col gap-4 min-w-0 xl:sticky xl:top-20 scroll-mt-20">
          {tieneSimulada && tieneReal && (
            <div role="tablist" aria-label="Tipo de consola" className="flex gap-1.5">
              {(["simulada", "real"] as const).map((tipo) => (
                <button
                  key={tipo}
                  type="button"
                  role="tab"
                  aria-selected={consola === tipo}
                  onClick={() => setConsola(tipo)}
                  className="chamfer-sm px-3 py-1.5 text-[11px] uppercase tracking-wider cursor-pointer border transition-colors"
                  style={{
                    fontFamily: "var(--font-mono)",
                    backgroundColor: consola === tipo ? "color-mix(in srgb, var(--signal-cyan) 12%, transparent)" : "transparent",
                    borderColor: consola === tipo ? "var(--signal-cyan)" : "var(--border-default)",
                    color: consola === tipo ? "var(--signal-cyan)" : "var(--text-muted)",
                  }}
                >
                  {tipo === "simulada" ? "Consola simulada" : "Entorno real (contenedor)"}
                </button>
              ))}
            </div>
          )}

          {tieneSimulada && consola === "simulada" && contenido.entorno_practica && (
            <SimulatedTerminal ref={consolaRef} entorno={contenido.entorno_practica} alto="min(56vh, 520px)" />
          )}

          {tieneReal && consola === "real" && (
            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between gap-3 flex-wrap">
                <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                  Contenedor propio y aislado para ti. Se apaga solo tras {entornoReal?.idle_timeout_minutos ?? 20} min sin uso.
                </span>
                {entornoReal?.activo ? (
                  <div className="flex items-center gap-2">
                    <StatusDot variant="online" label="Activo" pulse />
                    <Button type="button" variant="outline" size="sm" onClick={handleDetenerEntorno} disabled={entornoBusy || vencido} className="chamfer-sm font-mono text-xs uppercase">
                      Detener
                    </Button>
                  </div>
                ) : (
                  <Button type="button" size="sm" onClick={handleIniciarEntorno} disabled={entornoBusy || vencido} className="chamfer-sm font-mono text-xs uppercase">
                    {entornoBusy ? "Iniciando…" : "Iniciar entorno real"}
                  </Button>
                )}
              </div>
              {entornoError && <Aviso ok={false} msg={entornoError} />}
              {entornoReal?.activo && entornoReal.id && <RealTerminal entornoId={entornoReal.id} />}
            </div>
          )}

          {!completada ? (
            <form onSubmit={handleSubmitFlag} className="chamfer flex flex-col gap-3 p-4" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-amber)" }}>
              <label htmlFor={`flag-${seccionId}`} className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--signal-amber)", fontFamily: "var(--font-mono)" }}>
                Entrega la flag
              </label>
              <div className="flex flex-col sm:flex-row gap-2">
                <input
                  id={`flag-${seccionId}`}
                  value={flagValor}
                  onChange={(e) => setFlagValor(e.target.value)}
                  placeholder="FLAG{...}"
                  disabled={vencido}
                  spellCheck={false}
                  autoComplete="off"
                  className="chamfer-sm flex-1 min-w-0 px-3 py-2.5 text-sm outline-none disabled:opacity-50 focus-visible:ring-2"
                  style={{ color: "var(--text-heading)", fontFamily: "var(--font-mono)", backgroundColor: "var(--surface-sunken)", border: "1px solid var(--border-default)" }}
                />
                <Button type="submit" disabled={busy || !flagValor.trim() || vencido} className="chamfer-sm font-mono text-xs uppercase tracking-wide">
                  {busy ? "Validando…" : "Enviar"}
                </Button>
                <Button type="button" variant="outline" onClick={handlePedirAyuda} disabled={ayudaBusy || vencido} className="chamfer-sm font-mono text-xs uppercase tracking-wide">
                  {ayudaBusy ? "…" : "Pedir ayuda"}
                </Button>
              </div>

              <AnimatePresence>{feedback && <Aviso ok={feedback.ok} msg={feedback.msg} />}</AnimatePresence>

              {ayuda && (
                <div className="chamfer-sm px-3 py-2.5 flex flex-col gap-1.5" style={{ backgroundColor: "color-mix(in srgb, var(--signal-amber) 6%, transparent)", border: "1px solid var(--border-amber)" }}>
                  {ayuda.pasoAPaso ? (
                    <>
                      <span className="text-[10px] uppercase tracking-wide font-bold" style={{ color: "var(--signal-amber)", fontFamily: "var(--font-mono)" }}>Paso a paso completo</span>
                      <p className="text-sm m-0 whitespace-pre-wrap" style={{ color: "var(--text-base)" }}>{ayuda.pasoAPaso}</p>
                    </>
                  ) : ayuda.pista ? (
                    <>
                      <span className="text-[10px] uppercase tracking-wide font-bold" style={{ color: "var(--signal-amber)", fontFamily: "var(--font-mono)" }}>Pista</span>
                      <p className="text-sm m-0" style={{ color: "var(--text-base)" }}>{ayuda.pista}</p>
                      <p className="text-[11px] m-0" style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
                        El paso a paso completo se desbloquea a los {UMBRAL_PASO_A_PASO} intentos fallidos (llevas {ayuda.intentos}).
                      </p>
                    </>
                  ) : (
                    <p className="text-sm m-0" style={{ color: "var(--text-muted)" }}>
                      Todavía no hay ayuda: la pista se desbloquea a los {UMBRAL_PISTA} intentos fallidos (llevas {ayuda.intentos}). Mientras tanto, revisa el resultado esperado de cada tarea.
                    </p>
                  )}
                </div>
              )}
            </form>
          ) : (
            <p className="chamfer-sm text-sm m-0 px-3 py-2.5" style={{ color: "var(--signal-green)", backgroundColor: "color-mix(in srgb, var(--signal-green) 8%, transparent)", border: "1px solid var(--signal-green-dim)" }}>
              ✓ Ya entregaste la flag de esta sección. Puedes seguir practicando en la consola.
            </p>
          )}
        </div>
      </div>
    </motion.article>
  )
}

function Aviso({ ok, msg }: { ok: boolean; msg: string }) {
  return (
    <motion.p
      initial={{ opacity: 0 }}
      animate={{ opacity: 1, x: ok ? 0 : [0, -6, 6, -3, 0] }}
      exit={{ opacity: 0 }}
      className="text-sm m-0 px-3 py-2 chamfer-sm flex items-start gap-2"
      style={{
        color: ok ? "var(--signal-green)" : "var(--signal-red)",
        backgroundColor: `color-mix(in srgb, ${ok ? "var(--signal-green)" : "var(--signal-red)"} 8%, transparent)`,
        border: `1px solid ${ok ? "var(--signal-green-dim)" : "var(--signal-red-dim)"}`,
      }}
      role="status"
    >
      <span aria-hidden="true">{ok ? "✓" : "▲"}</span>
      <span>{msg}</span>
    </motion.p>
  )
}

function ExamenPanel({ assignmentId, onDone, vencido }: { assignmentId: string; onDone: () => void; vencido: boolean }) {
  const [preguntas, setPreguntas] = useState<PreguntaExamen[] | null>(null)
  const [respuestas, setRespuestas] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [resultado, setResultado] = useState<{ puntaje: number; correctas: number; total: number } | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    getExamen(assignmentId)
      .then((data) => setPreguntas(data.preguntas))
      .catch((err) => setError(err instanceof ApiError ? err.message : "No se pudo cargar el examen."))
      .finally(() => setLoading(false))
  }, [assignmentId])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setBusy(true)
    try {
      const r = await submitExam(assignmentId, respuestas)
      setResultado(r)
      onDone()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo enviar el examen.")
    } finally {
      setBusy(false)
    }
  }

  if (loading) return <Skeleton className="chamfer h-40" style={{ backgroundColor: "var(--surface)" }} />
  if (error) return <p className="text-sm px-3 py-2 chamfer-sm" style={{ color: "var(--signal-red)", backgroundColor: "color-mix(in srgb, var(--signal-red) 8%, transparent)", border: "1px solid var(--signal-red-dim)" }}>▲ {error}</p>

  const respondidas = Object.values(respuestas).filter((r) => r.trim()).length
  const total = preguntas?.length ?? 0

  if (resultado) {
    const aprobado = resultado.puntaje >= 60
    return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="chamfer flex flex-col items-center gap-4 p-6 sm:p-10 text-center max-w-[78ch]" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
        <StatusDot variant={aprobado ? "online" : "danger"} label={aprobado ? "Examen aprobado" : "Examen no aprobado"} />
        <ProgressRing percent={Math.round(resultado.puntaje)} size={140} stroke={8} color={aprobado ? "var(--signal-green)" : "var(--signal-red)"} />
        <p className="text-sm m-0" style={{ color: "var(--text-muted)" }}>
          {resultado.correctas} de {resultado.total} correctas{aprobado ? "" : " · necesitas 60 % para aprobar"}
        </p>
        <Button onClick={() => { setResultado(null); setRespuestas({}) }} disabled={vencido} className="chamfer-sm font-mono text-xs uppercase tracking-wide">
          Reintentar examen
        </Button>
      </motion.div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-6 max-w-[78ch]">
      <header className="flex flex-col gap-2 pb-4" style={{ borderBottom: "1px solid var(--border-default)" }}>
        <h2 className="text-xl sm:text-2xl font-bold m-0" style={{ color: "var(--text-heading)" }}>Examen final</h2>
        <p className="text-sm m-0" style={{ color: "var(--text-muted)" }}>
          {total} preguntas · apruebas con 60 % · puedes reintentarlo. Llevas {respondidas} de {total} respondidas.
        </p>
      </header>
      {(preguntas || []).map((p, i) => (
        <fieldset key={p.id} className="flex flex-col gap-2 border-none p-0 m-0">
          <legend className="text-sm font-semibold mb-2" style={{ color: "var(--text-heading)" }}>
            <span style={{ color: "var(--signal-amber)", fontFamily: "var(--font-mono)" }}>{i + 1}.</span> {p.enunciado}
          </legend>
          {p.tipo === "opcion_multiple" && p.opciones ? (
            <div className="flex flex-col gap-1.5">
              {p.opciones.map((op) => {
                const checked = respuestas[p.id] === op
                return (
                  <label
                    key={op}
                    className="chamfer-sm flex items-center gap-2.5 text-sm cursor-pointer px-3 py-2 transition-colors"
                    style={{ backgroundColor: checked ? "color-mix(in srgb, var(--signal-amber) 8%, transparent)" : "var(--surface)", border: `1px solid ${checked ? "var(--signal-amber)" : "var(--border-default)"}`, color: "var(--text-base)" }}
                  >
                    <input
                      type="radio"
                      name={p.id}
                      value={op}
                      checked={checked}
                      disabled={vencido}
                      onChange={(e) => setRespuestas((r) => ({ ...r, [p.id]: e.target.value }))}
                      style={{ accentColor: "var(--signal-amber)" }}
                    />
                    {op}
                  </label>
                )
              })}
            </div>
          ) : (
            <input
              value={respuestas[p.id] || ""}
              onChange={(e) => setRespuestas((r) => ({ ...r, [p.id]: e.target.value }))}
              disabled={vencido}
              aria-label={`Respuesta a la pregunta ${i + 1}`}
              className="chamfer-sm w-full px-3 py-2.5 text-sm outline-none disabled:opacity-50 focus-visible:ring-2"
              style={{ color: "var(--text-heading)", backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}
            />
          )}
        </fieldset>
      ))}
      <Button type="submit" disabled={busy || vencido || respondidas === 0} className="self-start chamfer-sm font-mono text-xs uppercase tracking-wide">
        {busy ? "Calificando…" : "Enviar examen"}
      </Button>
    </form>
  )
}
