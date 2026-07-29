import { useEffect, useState } from "react"
import { useParams, useNavigate, Link } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import {
  getProgresoOverview,
  getSectionContent,
  submitFlag,
  getHint,
  getExamen,
  submitExam,
  ApiError,
  type ProgresoOverview,
  type SeccionProgreso,
  type PreguntaExamen,
} from "./api"
import Navbar from "../components/Navbar"
import Footer from "../components/Footer"
import { IconFlask, IconExam, IconLock } from "../components/icons"

type Vista = { tipo: "seccion"; id: string } | { tipo: "examen" }

const ESTADO_ICON: Record<SeccionProgreso["estado"], string> = {
  bloqueada: "🔒",
  en_progreso: "▶",
  completada: "✓",
}

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
      <div className="min-h-screen flex flex-col" style={{ backgroundColor: "var(--bg-canvas)" }}>
        <Navbar />
        <main className="flex-1 flex items-center justify-center">
          <p className="text-sm" style={{ color: "var(--text-muted)", fontFamily: "'Fira Code', monospace" }}>
            cargando laboratorio...
          </p>
        </main>
        <Footer />
      </div>
    )
  }

  if (error || !overview || !assignmentId) {
    return (
      <div className="min-h-screen flex flex-col" style={{ backgroundColor: "var(--bg-canvas)", color: "var(--text-base)" }}>
        <Navbar />
        <main className="flex-1 flex flex-col items-center justify-center gap-4 px-4 text-center">
          <p className="text-sm" style={{ color: "var(--accent-danger)" }}>{error || "Laboratorio no encontrado."}</p>
          <Link to="/dashboard" className="text-sm font-semibold no-underline" style={{ color: "var(--accent-primary)" }}>
            ← Volver a mi Dashboard
          </Link>
        </main>
        <Footer />
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: "var(--bg-canvas)", color: "var(--text-base)" }}>
      <Navbar />
      <main className="flex-1">
        <div className="mx-auto px-4 sm:px-6 md:px-8 py-6 sm:py-8" style={{ maxWidth: "1200px" }}>
          <button
            type="button"
            onClick={() => navigate("/dashboard")}
            className="text-xs sm:text-sm mb-4 cursor-pointer border-none bg-transparent px-0"
            style={{ color: "var(--text-muted)", fontFamily: "'Fira Code', monospace" }}
          >
            ← Volver a mi Dashboard
          </button>

          <h1 className="text-xl sm:text-2xl font-semibold mb-6" style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}>
            {overview.laboratorio_nombre}
          </h1>

          <div className="flex flex-col md:flex-row gap-4 sm:gap-6">
            {/* Sidebar de secciones */}
            <aside className="w-full md:w-64 shrink-0">
              <div className="flex flex-col gap-1.5 rounded-lg p-2" style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--ui-border-default)" }}>
                {overview.secciones.map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    disabled={s.estado === "bloqueada"}
                    onClick={() => setVista({ tipo: "seccion", id: s.id })}
                    className="flex items-center gap-2.5 text-left px-3 py-2.5 rounded text-sm transition-colors disabled:cursor-not-allowed disabled:opacity-45"
                    style={{
                      backgroundColor: vista?.tipo === "seccion" && vista.id === s.id ? "var(--bg-surface-hover)" : "transparent",
                      color: s.estado === "completada" ? "#22C55E" : "var(--text-base)",
                    }}
                  >
                    <span style={{ fontFamily: "'Fira Code', monospace" }}>{ESTADO_ICON[s.estado]}</span>
                    <span className="flex-1 truncate">{s.orden}. {s.titulo}</span>
                  </button>
                ))}
                <button
                  type="button"
                  disabled={!overview.secciones_completas || !overview.examen_disponible}
                  onClick={() => setVista({ tipo: "examen" })}
                  className="flex items-center gap-2.5 text-left px-3 py-2.5 rounded text-sm transition-colors disabled:cursor-not-allowed disabled:opacity-45 mt-1"
                  style={{
                    backgroundColor: vista?.tipo === "examen" ? "var(--bg-surface-hover)" : "transparent",
                    color: "var(--ui-border-gold)",
                    borderTop: "1px solid var(--ui-border-default)",
                  }}
                >
                  <IconExam width={16} height={16} />
                  <span className="flex-1">Examen final</span>
                </button>
              </div>
            </aside>

            {/* Contenido principal */}
            <div className="flex-1 min-w-0">
              {vista?.tipo === "examen" ? (
                <ExamenPanel assignmentId={assignmentId} onDone={loadOverview} />
              ) : vista?.tipo === "seccion" ? (
                <SeccionPanel
                  key={vista.id}
                  assignmentId={assignmentId}
                  seccionId={vista.id}
                  seccionMeta={overview.secciones.find((s) => s.id === vista.id)}
                  onCompletada={(desbloqueada) => {
                    loadOverview()
                    if (desbloqueada) setVista({ tipo: "seccion", id: desbloqueada })
                  }}
                />
              ) : (
                <p className="text-sm" style={{ color: "var(--text-muted)" }}>Elegí una sección para empezar.</p>
              )}
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  )
}

function SeccionPanel({
  assignmentId,
  seccionId,
  seccionMeta,
  onCompletada,
}: {
  assignmentId: string
  seccionId: string
  seccionMeta?: SeccionProgreso
  onCompletada: (seccionDesbloqueada?: string | null) => void
}) {
  const [contenido, setContenido] = useState<{ titulo: string; contenido_teorico: string; tiene_practica: boolean; estado: string } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [flagValor, setFlagValor] = useState("")
  const [busy, setBusy] = useState(false)
  const [feedback, setFeedback] = useState<{ ok: boolean; msg: string; pista?: string } | null>(null)

  useEffect(() => {
    setLoading(true)
    setFeedback(null)
    setFlagValor("")
    getSectionContent(assignmentId, seccionId)
      .then(setContenido)
      .catch((err) => setError(err instanceof ApiError ? err.message : "No se pudo cargar la sección."))
      .finally(() => setLoading(false))
  }, [assignmentId, seccionId])

  const handleSubmitFlag = async (e: React.FormEvent) => {
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
          pista: resultado.pista_disponible ? resultado.pista : undefined,
        })
      }
    } catch (err) {
      setFeedback({ ok: false, msg: err instanceof ApiError ? err.message : "No se pudo validar la flag." })
    } finally {
      setBusy(false)
    }
  }

  const handleHint = async () => {
    try {
      const pista = await getHint(assignmentId, seccionId)
      if (pista.pista_disponible) setFeedback({ ok: false, msg: "Pista:", pista: pista.pista })
      else setFeedback({ ok: false, msg: "Todavía no hay pista disponible para esta sección." })
    } catch (err) {
      setFeedback({ ok: false, msg: err instanceof ApiError ? err.message : "No se pudo obtener la pista." })
    }
  }

  if (loading) {
    return <div className="h-40 rounded-lg animate-pulse" style={{ backgroundColor: "var(--bg-surface)" }} />
  }
  if (error || !contenido) {
    return <p className="text-sm" style={{ color: "var(--accent-danger)" }}>{error || "Sección no disponible."}</p>
  }

  const completada = contenido.estado === "completada"

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }} className="rounded-lg p-5 sm:p-6" style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--ui-border-default)" }}>
      <div className="flex items-center gap-2 mb-4">
        <IconFlask style={{ color: "var(--accent-primary)" }} />
        <h2 className="text-lg font-semibold m-0" style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}>
          {seccionMeta?.orden}. {contenido.titulo}
        </h2>
        {completada && (
          <span className="text-xs font-semibold px-2 py-0.5 rounded-full" style={{ backgroundColor: "rgba(34,197,94,0.15)", color: "#22C55E" }}>
            Completada
          </span>
        )}
      </div>

      <div
        className="text-sm leading-relaxed mb-6 [&_p]:mb-3 [&_pre]:p-3 [&_pre]:rounded [&_pre]:overflow-x-auto"
        style={{ color: "var(--text-base)" }}
        dangerouslySetInnerHTML={{ __html: contenido.contenido_teorico }}
      />

      {contenido.tiene_practica && !completada && (
        <form onSubmit={handleSubmitFlag} className="flex flex-col gap-3 pt-4" style={{ borderTop: "1px solid var(--ui-border-default)" }}>
          <label className="text-xs font-semibold" style={{ color: "var(--text-heading)", fontFamily: "'Fira Code', monospace" }}>
            FLAG{"{...}"}
          </label>
          <div className="flex flex-col sm:flex-row gap-2">
            <input
              value={flagValor}
              onChange={(e) => setFlagValor(e.target.value)}
              placeholder="Ingresá la flag capturada"
              className="flex-1 px-3.5 py-2.5 rounded text-sm"
              style={{ backgroundColor: "var(--bg-canvas)", color: "var(--text-base)", border: "1px solid var(--ui-border-default)", fontFamily: "'Fira Code', monospace" }}
            />
            <button
              type="submit"
              disabled={busy || !flagValor}
              className="px-5 py-2.5 rounded text-sm font-semibold cursor-pointer border-none disabled:opacity-50"
              style={{ backgroundColor: "var(--accent-primary)", color: "#fff", fontFamily: "'Fira Code', monospace" }}
            >
              Enviar
            </button>
            <button
              type="button"
              onClick={handleHint}
              className="px-4 py-2.5 rounded text-sm font-medium cursor-pointer border"
              style={{ backgroundColor: "transparent", borderColor: "var(--ui-border-default)", color: "var(--text-muted)" }}
            >
              Pista
            </button>
          </div>
          <AnimatePresence>
            {feedback && (
              <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="text-sm m-0" style={{ color: feedback.ok ? "#22C55E" : "var(--accent-danger)" }}>
                {feedback.msg} {feedback.pista && <span style={{ color: "var(--text-muted)" }}>{feedback.pista}</span>}
              </motion.p>
            )}
          </AnimatePresence>
        </form>
      )}
    </motion.div>
  )
}

function ExamenPanel({ assignmentId, onDone }: { assignmentId: string; onDone: () => void }) {
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

  const handleSubmit = async (e: React.FormEvent) => {
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

  if (loading) return <div className="h-40 rounded-lg animate-pulse" style={{ backgroundColor: "var(--bg-surface)" }} />
  if (error) return <p className="text-sm" style={{ color: "var(--accent-danger)" }}>{error}</p>

  if (resultado) {
    return (
      <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="rounded-lg p-6 text-center" style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--ui-border-gold)" }}>
        <h2 className="text-xl font-semibold mb-2" style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}>
          {Math.round(resultado.puntaje)}%
        </h2>
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>
          {resultado.correctas} de {resultado.total} correctas
        </p>
        <button
          type="button"
          onClick={() => { setResultado(null); setRespuestas({}) }}
          className="mt-4 px-5 py-2 rounded text-sm font-semibold cursor-pointer border-none"
          style={{ backgroundColor: "var(--text-heading)", color: "#0F1117", fontFamily: "'Fira Code', monospace" }}
        >
          Reintentar examen
        </button>
      </motion.div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="rounded-lg p-5 sm:p-6 flex flex-col gap-6" style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--ui-border-gold)" }}>
      <div className="flex items-center gap-2">
        <IconLock style={{ color: "var(--ui-border-gold)" }} />
        <h2 className="text-lg font-semibold m-0" style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}>Examen final</h2>
      </div>
      {(preguntas || []).map((p, i) => (
        <div key={p.id} className="flex flex-col gap-2">
          <label className="text-sm font-medium" style={{ color: "var(--text-heading)" }}>{i + 1}. {p.enunciado}</label>
          {p.tipo === "opcion_multiple" && p.opciones ? (
            <div className="flex flex-col gap-1.5">
              {p.opciones.map((op) => (
                <label key={op} className="flex items-center gap-2 text-sm cursor-pointer" style={{ color: "var(--text-base)" }}>
                  <input
                    type="radio"
                    name={p.id}
                    value={op}
                    checked={respuestas[p.id] === op}
                    onChange={(e) => setRespuestas((r) => ({ ...r, [p.id]: e.target.value }))}
                  />
                  {op}
                </label>
              ))}
            </div>
          ) : (
            <input
              value={respuestas[p.id] || ""}
              onChange={(e) => setRespuestas((r) => ({ ...r, [p.id]: e.target.value }))}
              className="px-3.5 py-2 rounded text-sm"
              style={{ backgroundColor: "var(--bg-canvas)", color: "var(--text-base)", border: "1px solid var(--ui-border-default)" }}
            />
          )}
        </div>
      ))}
      <button
        type="submit"
        disabled={busy}
        className="self-start px-6 py-2.5 rounded text-sm font-semibold cursor-pointer border-none disabled:opacity-50"
        style={{ backgroundColor: "var(--text-heading)", color: "#0F1117", fontFamily: "'Fira Code', monospace" }}
      >
        Enviar examen
      </button>
    </form>
  )
}
