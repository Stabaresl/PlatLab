import { useEffect, useState, type FormEvent } from "react"
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
import Navbar from "../components/Navbar"
import Footer from "../components/Footer"
import HeroBackground from "../components/HeroBackground"
import ReticleFrame from "../components/ReticleFrame"
import ProgressRing from "../components/ProgressRing"
import StatusDot from "../components/StatusDot"
import MatrixRain from "../components/MatrixRain"
import SimulatedTerminal from "../components/SimulatedTerminal"
import RealTerminal from "../components/RealTerminal"
import MouseGlow, { trackGlow, untrackGlow } from "../components/MouseGlow"
import { IconFlask, IconExam, IconLock } from "../components/icons"
import { Button } from "../components/ui/button"
import { Skeleton } from "../components/ui/skeleton"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../components/ui/tabs"

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

  useEffect(() => {
    setLoading(true)
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
          <p className="text-sm px-3 py-2 chamfer-sm" style={{ color: "var(--signal-red)", backgroundColor: "rgba(255,71,87,0.08)", border: "1px solid var(--signal-red-dim)" }}>▲ {error || "Laboratorio no encontrado."}</p>
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
    ? Math.ceil((new Date(overview.fecha_vencimiento).getTime() - Date.now()) / 86_400_000)
    : null

  return (
    <div className="relative min-h-screen overflow-hidden" style={{ backgroundColor: "var(--canvas)", color: "var(--text-base)" }}>
      <HeroBackground image="grim" imageOpacity={0.04} overlayOpacity={0.94} texture="none" />
      <div className="relative z-10 flex flex-col min-h-screen">
        <Navbar />
        <main className="flex-1">
          <div className="mx-auto px-4 sm:px-6 md:px-8 py-6 sm:py-8" style={{ maxWidth: "1280px" }}>
            <button
              type="button"
              onClick={() => navigate("/dashboard")}
              className="text-xs sm:text-sm mb-4 cursor-pointer border-none bg-transparent px-0 uppercase tracking-wide"
              style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
            >
              ← Volver a mi Dashboard
            </button>

            {/* ═══ Header del lab: nombre + progreso global + vencimiento ═══ */}
            <div
              onMouseMove={trackGlow}
              onMouseLeave={untrackGlow}
              className="relative chamfer overflow-hidden flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 sm:p-5 mb-3 sm:mb-4"
              style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}
            >
              <MouseGlow color="255,176,32" size={340} opacity={0.12} />
              <div className="relative z-10">
                <StatusDot variant={overview.secciones_completas ? "online" : "active"} label={overview.secciones_completas ? "Secciones completas" : "Misión en curso"} pulse={!overview.secciones_completas} />
                <h1 className="text-xl sm:text-2xl font-black uppercase mt-1.5 m-0" style={{ color: "var(--text-heading)" }}>
                  {overview.laboratorio_nombre}
                </h1>
              </div>
              <div className="relative z-10 flex flex-col items-end gap-1.5 shrink-0">
                <div className="flex items-center gap-3 sm:gap-4">
                  <div className="flex-1 sm:w-40 h-1.5 overflow-hidden" style={{ backgroundColor: "var(--surface-hover)" }}>
                    <motion.div initial={{ width: 0 }} animate={{ width: `${pctGlobal}%` }} transition={{ duration: 0.5, ease: "easeOut" }} className="h-full" style={{ backgroundColor: "var(--signal-amber)" }} />
                  </div>
                  <span className="text-sm font-bold font-mono shrink-0" style={{ color: "var(--signal-amber)" }}>{pctGlobal}%</span>
                </div>
                {overview.fecha_vencimiento && !vencido && diasRestantes !== null && (
                  <span className="text-[10px] font-mono uppercase tracking-wide" style={{ color: diasRestantes <= 5 ? "var(--signal-red)" : "var(--text-muted)" }}>
                    Vence en {Math.max(diasRestantes, 0)} día{diasRestantes === 1 ? "" : "s"} ({new Date(overview.fecha_vencimiento).toLocaleDateString()})
                  </span>
                )}
              </div>
            </div>

            {vencido && (
              <div className="chamfer flex items-center gap-3 p-4 mb-5 sm:mb-6" style={{ backgroundColor: "rgba(255,71,87,0.08)", border: "1px solid var(--signal-red)" }}>
                <IconLock style={{ color: "var(--signal-red)" }} className="shrink-0" />
                <p className="text-sm m-0" style={{ color: "var(--signal-red)" }}>
                  Este laboratorio venció{overview.fecha_vencimiento ? ` el ${new Date(overview.fecha_vencimiento).toLocaleDateString()}` : ""}. Puedes revisar el contenido, pero ya no se puede enviar flags, continuar secciones ni presentar el examen.
                </p>
              </div>
            )}

            <div className="flex flex-col md:flex-row gap-4 sm:gap-6">
              {/* ═══ Sidebar: stepper de secciones ═══ */}
              <aside className="w-full md:w-72 shrink-0">
                <div className="chamfer flex flex-col p-3" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
                  {overview.secciones.map((s, i) => {
                    const active = vista?.tipo === "seccion" && vista.id === s.id
                    return (
                      <button
                        key={s.id}
                        type="button"
                        disabled={s.estado === "bloqueada"}
                        onClick={() => setVista({ tipo: "seccion", id: s.id })}
                        className="relative flex items-start gap-3 text-left px-2.5 py-2.5 transition-colors disabled:cursor-not-allowed disabled:opacity-45 group"
                        style={{ backgroundColor: active ? "var(--surface-hover)" : "transparent" }}
                      >
                        <div className="flex flex-col items-center shrink-0">
                          <SeccionNode estado={s.estado} orden={s.orden} />
                          {i < overview.secciones.length - 1 && (
                            <span className="w-px flex-1 mt-1" style={{ backgroundColor: s.estado === "completada" ? "var(--signal-green)" : "var(--border-default)", minHeight: 16 }} />
                          )}
                        </div>
                        <span className="flex-1 text-sm pt-1 truncate" style={{ color: active ? "var(--text-heading)" : "var(--text-base)", fontWeight: active ? 700 : 500 }}>
                          {s.titulo}
                        </span>
                      </button>
                    )
                  })}
                  <button
                    type="button"
                    disabled={!overview.secciones_completas || !overview.examen_disponible}
                    onClick={() => setVista({ tipo: "examen" })}
                    className="flex items-center gap-3 text-left px-2.5 py-2.5 transition-colors disabled:cursor-not-allowed disabled:opacity-45 mt-1"
                    style={{ backgroundColor: vista?.tipo === "examen" ? "var(--surface-hover)" : "transparent", borderTop: "1px solid var(--border-default)" }}
                  >
                    <span className="chamfer-sm flex items-center justify-center w-7 h-7 shrink-0" style={{ backgroundColor: "rgba(255,176,32,0.12)", color: "var(--signal-amber)", border: "1px solid var(--border-amber)" }}>
                      <IconExam width={14} height={14} />
                    </span>
                    <span className="flex-1 text-sm font-bold uppercase tracking-wide" style={{ color: "var(--signal-amber)" }}>Examen final</span>
                  </button>
                </div>
              </aside>

              {/* ═══ Panel principal ═══ */}
              <div className="flex-1 min-w-0">
                {vista?.tipo === "examen" ? (
                  <ExamenPanel assignmentId={assignmentId} onDone={loadOverview} vencido={vencido} />
                ) : vista?.tipo === "seccion" ? (
                  <SeccionPanel
                    key={vista.id}
                    assignmentId={assignmentId}
                    seccionId={vista.id}
                    seccionMeta={overview.secciones.find((s) => s.id === vista.id)}
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
      <span className="chamfer-sm flex items-center justify-center w-7 h-7 text-xs font-bold shrink-0" style={{ backgroundColor: "var(--signal-green)", color: "#04140d", fontFamily: "var(--font-mono)" }}>
        ✓
      </span>
    )
  }
  if (estado === "en_progreso") {
    return (
      <span className="chamfer-sm flex items-center justify-center w-7 h-7 text-xs font-bold shrink-0" style={{ backgroundColor: "rgba(255,176,32,0.14)", color: "var(--signal-amber)", border: "1px solid var(--signal-amber)", fontFamily: "var(--font-mono)", animation: "status-blink 1.8s ease-in-out infinite" }}>
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

function AbrirEnPestanaButton({ assignmentId, seccionId, modo }: { assignmentId: string; seccionId: string; modo: "teoria" | "guia" }) {
  return (
    <button
      type="button"
      onClick={() => window.open(`/resolver/${assignmentId}/secciones/${seccionId}/material?modo=${modo}`, "_blank", "noopener,noreferrer")}
      className="chamfer-sm inline-flex items-center gap-1.5 text-[11px] font-mono uppercase tracking-wide px-2.5 py-1 cursor-pointer border transition-colors"
      style={{ backgroundColor: "transparent", borderColor: "var(--border-default)", color: "var(--text-muted)" }}
      onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--signal-cyan)"; e.currentTarget.style.color = "var(--signal-cyan)" }}
      onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--border-default)"; e.currentTarget.style.color = "var(--text-muted)" }}
      title="Abrir en una pestaña aparte — queda disponible mientras trabajas en la práctica"
    >
      ↗ Abrir en pestaña aparte
    </button>
  )
}

function ContenidoHtml({ html }: { html: string }) {
  return (
    <div
      className="text-sm leading-relaxed [&_p]:mb-3 [&_pre]:p-3 [&_pre]:my-3 [&_pre]:overflow-x-auto [&_pre]:font-mono [&_pre]:text-xs [&_code]:font-mono [&_code]:text-[13px] [&_h1]:font-bold [&_h1]:uppercase [&_h1]:mt-4 [&_h1]:mb-2 [&_h2]:font-bold [&_h2]:uppercase [&_h2]:mt-4 [&_h2]:mb-2 [&_h3]:font-bold [&_h3]:mt-3 [&_h3]:mb-1.5 [&_h4]:font-bold [&_h4]:mt-3 [&_h4]:mb-1 [&_a]:underline [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5 [&_blockquote]:pl-3 [&_blockquote]:italic"
      style={{ color: "var(--text-base)" }}
    >
      <style>{`.sec-content pre { background: var(--surface-sunken); border: 1px solid var(--border-default); color: var(--signal-green); }
        .sec-content code { color: var(--signal-amber); }
        .sec-content h1, .sec-content h2, .sec-content h3, .sec-content h4 { color: var(--text-heading); font-family: var(--font-mono); }
        .sec-content a { color: var(--signal-cyan); }
        .sec-content blockquote { border-left: 2px solid var(--signal-amber); color: var(--text-muted); }`}</style>
      <div className="sec-content" dangerouslySetInnerHTML={{ __html: html }} />
    </div>
  )
}

function SeccionPanel({
  assignmentId,
  seccionId,
  seccionMeta,
  vencido,
  onCompletada,
}: {
  assignmentId: string
  seccionId: string
  seccionMeta?: SeccionProgreso
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
  const [tab, setTab] = useState("teoria")
  const [entornoReal, setEntornoReal] = useState<EntornoRealEstado | null>(null)
  const [entornoBusy, setEntornoBusy] = useState(false)
  const [entornoError, setEntornoError] = useState("")

  useEffect(() => {
    setLoading(true)
    setFeedback(null)
    setFlagValor("")
    setAyuda(null)
    setTab("teoria")
    setEntornoReal(null)
    setEntornoError("")
    getSectionContent(assignmentId, seccionId)
      .then((data) => {
        setContenido(data)
        if (data.entorno_real_disponible) {
          getLabEnvironmentStatus(assignmentId, seccionId).then(setEntornoReal).catch(() => {})
        }
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "No se pudo cargar la sección."))
      .finally(() => setLoading(false))
  }, [assignmentId, seccionId])

  const handleIniciarEntorno = async () => {
    setEntornoBusy(true)
    setEntornoError("")
    try {
      const resultado = await startLabEnvironment(assignmentId, seccionId)
      setEntornoReal({ activo: true, ...resultado })
    } catch (err) {
      setEntornoError(err instanceof ApiError ? err.message : "No se pudo iniciar el entorno.")
    } finally {
      setEntornoBusy(false)
    }
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
      const resultado = await submitFlag(assignmentId, seccionId, flagValor)
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
    return <Skeleton className="chamfer h-40" style={{ backgroundColor: "var(--surface)" }} />
  }
  if (error || !contenido) {
    return <p className="text-sm px-3 py-2 chamfer-sm" style={{ color: "var(--signal-red)", backgroundColor: "rgba(255,71,87,0.08)", border: "1px solid var(--signal-red-dim)" }}>▲ {error || "Sección no disponible."}</p>
  }

  const completada = contenido.estado === "completada"
  const tieneGuia = contenido.guia_paso_a_paso.trim().length > 0

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }}>
      <ReticleFrame color="var(--signal-cyan)" size={14}>
        <div className="relative overflow-hidden chamfer" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
          {/* barra de chrome tipo terminal */}
          <div className="flex items-center gap-1.5 px-4 py-2" style={{ borderBottom: "1px solid var(--border-hairline)", backgroundColor: "var(--canvas-raised)" }}>
            <span className="w-2 h-2" style={{ backgroundColor: "var(--signal-red)" }} />
            <span className="w-2 h-2" style={{ backgroundColor: "var(--signal-amber)" }} />
            <span className="w-2 h-2" style={{ backgroundColor: "var(--signal-green)" }} />
            <span className="ml-2 text-[10px] truncate" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
              seccion_{seccionMeta?.orden ?? ""}.md --render
            </span>
          </div>

          <div className="p-5 sm:p-6">
            <div className="flex items-center gap-2 mb-4 flex-wrap">
              <IconFlask style={{ color: "var(--signal-cyan)" }} />
              <h2 className="text-lg font-bold uppercase tracking-wide m-0" style={{ color: "var(--text-heading)" }}>
                {seccionMeta?.orden}. {contenido.titulo}
              </h2>
              {completada && (
                <span className="text-[10px] font-bold px-2 py-0.5 chamfer-sm uppercase tracking-wide" style={{ backgroundColor: "rgba(51,214,159,0.14)", color: "var(--signal-green)", border: "1px solid var(--signal-green-dim)" }}>
                  ✓ Completada
                </span>
              )}
            </div>

            <Tabs value={tab} onValueChange={setTab}>
              <TabsList variant="line" className="mb-4">
                <TabsTrigger value="teoria" className="font-mono text-xs uppercase">Teoría</TabsTrigger>
                {tieneGuia && <TabsTrigger value="guia" className="font-mono text-xs uppercase">Guía paso a paso</TabsTrigger>}
                {contenido.tiene_practica && <TabsTrigger value="practica" className="font-mono text-xs uppercase">Práctica</TabsTrigger>}
              </TabsList>

              <TabsContent value="teoria" className="flex flex-col gap-3">
                <div className="flex justify-end">
                  <AbrirEnPestanaButton assignmentId={assignmentId} seccionId={seccionId} modo="teoria" />
                </div>
                <ContenidoHtml html={contenido.contenido_teorico} />
              </TabsContent>

              {tieneGuia && (
                <TabsContent value="guia" className="flex flex-col gap-3">
                  <div className="flex justify-end">
                    <AbrirEnPestanaButton assignmentId={assignmentId} seccionId={seccionId} modo="guia" />
                  </div>
                  <ContenidoHtml html={contenido.guia_paso_a_paso} />
                </TabsContent>
              )}

              {contenido.tiene_practica && (
                <TabsContent value="practica" className="flex flex-col gap-4">
                  {contenido.entorno_practica && <SimulatedTerminal entorno={contenido.entorno_practica} />}

                  {contenido.entorno_real_disponible && (
                    <div className="flex flex-col gap-2">
                      <div className="flex items-center justify-between gap-3 flex-wrap">
                        <span className="text-xs font-bold uppercase tracking-wide" style={{ color: "var(--signal-cyan)", fontFamily: "var(--font-mono)" }}>
                          Entorno real (contenedor descartable)
                        </span>
                        {entornoReal?.activo ? (
                          <div className="flex items-center gap-2">
                            <StatusDot variant="online" label={`Activo — se apaga tras ${entornoReal.idle_timeout_minutos ?? 20} min sin uso`} pulse />
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
                      {entornoError && (
                        <p className="text-sm m-0 px-3 py-2 chamfer-sm" style={{ color: "var(--signal-red)", backgroundColor: "rgba(255,71,87,0.08)", border: "1px solid var(--signal-red-dim)" }}>
                          ▲ {entornoError}
                        </p>
                      )}
                      {entornoReal?.activo && entornoReal.id && <RealTerminal entornoId={entornoReal.id} />}
                    </div>
                  )}

                  {!completada && (
                    <form onSubmit={handleSubmitFlag} className="flex flex-col gap-3 pt-2" style={{ borderTop: "1px solid var(--border-default)" }}>
                      <label className="text-xs font-bold uppercase tracking-wide" style={{ color: "var(--signal-amber)", fontFamily: "var(--font-mono)" }}>
                        FLAG{"{...}"}
                      </label>
                      <div className="flex flex-col sm:flex-row gap-2">
                        <div className="chamfer-sm flex-1 flex items-center px-3.5" style={{ backgroundColor: "var(--canvas)", border: "1px solid var(--border-default)" }}>
                          <span className="text-xs mr-1.5 shrink-0" style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>$</span>
                          <input
                            value={flagValor}
                            onChange={(e) => setFlagValor(e.target.value)}
                            placeholder="Ingresa la flag capturada"
                            disabled={vencido}
                            className="flex-1 py-2.5 bg-transparent border-none outline-none text-sm disabled:opacity-50"
                            style={{ color: "var(--text-heading)", fontFamily: "var(--font-mono)" }}
                          />
                        </div>
                        <Button type="submit" disabled={busy || !flagValor || vencido} className="chamfer-sm font-mono text-xs uppercase tracking-wide">
                          Enviar
                        </Button>
                        <Button type="button" variant="outline" onClick={handlePedirAyuda} disabled={ayudaBusy || vencido} className="chamfer-sm font-mono text-xs uppercase tracking-wide">
                          {ayudaBusy ? "…" : "Pedir ayuda"}
                        </Button>
                      </div>

                      <AnimatePresence>
                        {feedback && (
                          <motion.p
                            initial={{ opacity: 0, x: feedback.ok ? 0 : -6 }}
                            animate={{ opacity: 1, x: feedback.ok ? 0 : [0, -6, 6, -3, 0] }}
                            exit={{ opacity: 0 }}
                            className="text-sm m-0 px-3 py-2 chamfer-sm flex items-start gap-2"
                            style={{
                              color: feedback.ok ? "var(--signal-green)" : "var(--signal-red)",
                              backgroundColor: feedback.ok ? "rgba(51,214,159,0.08)" : "rgba(255,71,87,0.08)",
                              border: `1px solid ${feedback.ok ? "var(--signal-green-dim)" : "var(--signal-red-dim)"}`,
                            }}
                            role="status"
                          >
                            <span aria-hidden="true">{feedback.ok ? "✓" : "▲"}</span>
                            <span>{feedback.msg}</span>
                          </motion.p>
                        )}
                      </AnimatePresence>

                      {ayuda && (
                        <div className="chamfer-sm px-3 py-2.5 flex flex-col gap-1.5" style={{ backgroundColor: "rgba(255,176,32,0.06)", border: "1px solid var(--border-amber)" }}>
                          {ayuda.pasoAPaso ? (
                            <>
                              <span className="text-[10px] uppercase tracking-wide font-bold" style={{ color: "var(--signal-amber)", fontFamily: "var(--font-mono)" }}>Paso a paso completo</span>
                              <p className="text-sm m-0" style={{ color: "var(--text-base)" }}>{ayuda.pasoAPaso}</p>
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
                              Todavía no hay ayuda disponible — la pista se desbloquea a los {UMBRAL_PISTA} intentos fallidos (llevas {ayuda.intentos}). Prueba con la guía paso a paso mientras tanto.
                            </p>
                          )}
                        </div>
                      )}
                    </form>
                  )}
                </TabsContent>
              )}
            </Tabs>

            {!contenido.tiene_practica && !completada && (
              <div className="flex flex-col gap-3 pt-4 mt-1" style={{ borderTop: "1px solid var(--border-default)" }}>
                <p className="text-xs m-0" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                  Sección teórica — no requiere flag. Cuando termines de leer, continúa al siguiente paso.
                </p>
                <Button type="button" onClick={handleContinuar} disabled={busy || vencido} className="self-start chamfer-sm font-mono text-xs uppercase tracking-wide">
                  {busy ? "Avanzando…" : "Continuar →"}
                </Button>
                <AnimatePresence>
                  {feedback && !feedback.ok && (
                    <motion.p
                      initial={{ opacity: 0, x: -6 }}
                      animate={{ opacity: 1, x: [0, -6, 6, -3, 0] }}
                      exit={{ opacity: 0 }}
                      className="text-sm m-0 px-3 py-2 chamfer-sm flex items-start gap-2"
                      style={{ color: "var(--signal-red)", backgroundColor: "rgba(255,71,87,0.08)", border: "1px solid var(--signal-red-dim)" }}
                      role="status"
                    >
                      <span aria-hidden="true">▲</span>
                      <span>{feedback.msg}</span>
                    </motion.p>
                  )}
                </AnimatePresence>
              </div>
            )}
          </div>
        </div>
      </ReticleFrame>
    </motion.div>
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
    setLoading(true)
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
  if (error) return <p className="text-sm px-3 py-2 chamfer-sm" style={{ color: "var(--signal-red)", backgroundColor: "rgba(255,71,87,0.08)", border: "1px solid var(--signal-red-dim)" }}>▲ {error}</p>

  if (resultado) {
    const aprobado = resultado.puntaje >= 60
    return (
      <ReticleFrame color="var(--signal-amber)" size={16}>
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="relative overflow-hidden chamfer flex flex-col items-center gap-4 p-6 sm:p-10 text-center" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
          <MatrixRain opacity={0.04} />
          <div className="relative z-10 flex flex-col items-center gap-4">
            <StatusDot variant={aprobado ? "online" : "danger"} label={aprobado ? "Examen aprobado" : "Examen no aprobado"} />
            <ProgressRing percent={Math.round(resultado.puntaje)} size={140} stroke={8} color={aprobado ? "var(--signal-green)" : "var(--signal-red)"} />
            <p className="text-sm m-0" style={{ color: "var(--text-muted)" }}>
              {resultado.correctas} de {resultado.total} correctas
            </p>
            <Button onClick={() => { setResultado(null); setRespuestas({}) }} disabled={vencido} className="chamfer-sm font-mono text-xs uppercase tracking-wide">
              Reintentar examen
            </Button>
          </div>
        </motion.div>
      </ReticleFrame>
    )
  }

  return (
    <ReticleFrame color="var(--signal-amber)" size={14}>
      <form onSubmit={handleSubmit} className="chamfer flex flex-col gap-6 p-5 sm:p-6" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
        <div className="flex items-center gap-2">
          <IconLock style={{ color: "var(--signal-amber)" }} />
          <h2 className="text-lg font-bold uppercase tracking-wide m-0" style={{ color: "var(--text-heading)" }}>Examen final</h2>
        </div>
        {(preguntas || []).map((p, i) => (
          <div key={p.id} className="flex flex-col gap-2">
            <label className="text-sm font-medium" style={{ color: "var(--text-heading)" }}>{i + 1}. {p.enunciado}</label>
            {p.tipo === "opcion_multiple" && p.opciones ? (
              <div className="flex flex-col gap-1.5">
                {p.opciones.map((op) => {
                  const checked = respuestas[p.id] === op
                  return (
                    <label
                      key={op}
                      className="chamfer-sm flex items-center gap-2.5 text-sm cursor-pointer px-3 py-2 transition-colors"
                      style={{ backgroundColor: checked ? "rgba(255,176,32,0.08)" : "var(--canvas)", border: `1px solid ${checked ? "var(--signal-amber)" : "var(--border-default)"}`, color: "var(--text-base)" }}
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
              <div className="chamfer-sm px-3.5" style={{ backgroundColor: "var(--canvas)", border: "1px solid var(--border-default)" }}>
                <input
                  value={respuestas[p.id] || ""}
                  onChange={(e) => setRespuestas((r) => ({ ...r, [p.id]: e.target.value }))}
                  disabled={vencido}
                  className="w-full py-2.5 bg-transparent border-none outline-none text-sm disabled:opacity-50"
                  style={{ color: "var(--text-heading)" }}
                />
              </div>
            )}
          </div>
        ))}
        <Button type="submit" disabled={busy || vencido} className="self-start chamfer-sm font-mono text-xs uppercase tracking-wide">
          Enviar examen
        </Button>
      </form>
    </ReticleFrame>
  )
}
