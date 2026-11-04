import { useCallback, useEffect, useRef, useState } from "react"
import { createPortal } from "react-dom"
import { AnimatePresence, motion } from "framer-motion"
import {
  ApiError,
  entregarExamenAlSalir,
  getExamen,
  iniciarExamen,
  submitExam,
  type EstadoExamen,
  type PreguntaExamen,
  type ResultadoExamen,
} from "../../pages/api"
import ProgressRing from "../ProgressRing"
import StatusDot from "../StatusDot"
import { IconClock, IconExam, IconLock } from "../icons"
import { Button } from "../ui/button"
import { Skeleton } from "../ui/skeleton"

type Fase = "cargando" | "portada" | "en_curso" | "resultado"

/**
 * Examen final del laboratorio.
 *
 * Reglas (las aplica el backend; aquí se explican y se hacen cumplir en la UI):
 * - 3 intentos; si se reprueban los 3, hay que esperar 24 h.
 * - Al empezar, el examen ocupa toda la pantalla y no se puede navegar fuera.
 * - Recargar, cerrar la pestaña o volver atrás entrega el intento con lo que
 *   haya; si esa entrega no alcanza a llegar, el backend lo cuenta como 0.
 */
export default function ExamenFinal({
  assignmentId,
  vencido,
  onDone,
}: {
  assignmentId: string
  vencido: boolean
  onDone: () => void
}) {
  const [fase, setFase] = useState<Fase>("cargando")
  const [estado, setEstado] = useState<EstadoExamen | null>(null)
  const [preguntas, setPreguntas] = useState<PreguntaExamen[]>([])
  const [iniciadoEn, setIniciadoEn] = useState<number>(0)
  const [resultado, setResultado] = useState<ResultadoExamen | null>(null)
  const [aviso, setAviso] = useState("")
  const [error, setError] = useState("")
  const [confirmando, setConfirmando] = useState(false)
  const [busy, setBusy] = useState(false)

  const cargar = useCallback(() => {
    return getExamen(assignmentId)
      .then((e) => {
        setEstado(e)
        setFase((f) => (f === "cargando" ? "portada" : f))
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "No se pudo cargar el examen."))
  }, [assignmentId])

  useEffect(() => {
    cargar()
  }, [cargar])

  const empezar = async () => {
    setConfirmando(false)
    setBusy(true)
    setError("")
    // La pantalla completa necesita el clic del usuario: se pide antes de esperar al backend.
    document.documentElement.requestFullscreen?.().catch(() => undefined)
    try {
      const r = await iniciarExamen(assignmentId)
      setEstado(r.estado)
      if (!r.iniciado) {
        salirDePantallaCompleta()
        setAviso(r.abandono_cerrado ? "Tu intento anterior quedó abierto y se contó como reprobado." : "")
        return
      }
      setAviso(r.abandono_cerrado ? "Tu intento anterior quedó abierto y se contó como reprobado." : "")
      setPreguntas(r.preguntas)
      setIniciadoEn(r.iniciado_en ? new Date(r.iniciado_en).getTime() : Date.now())
      setFase("en_curso")
    } catch (err) {
      salirDePantallaCompleta()
      setError(err instanceof ApiError ? err.message : "No se pudo iniciar el examen.")
    } finally {
      setBusy(false)
    }
  }

  const alEntregar = (r: ResultadoExamen) => {
    salirDePantallaCompleta()
    setResultado(r)
    if (r.estado) setEstado(r.estado)
    setFase("resultado")
    onDone()
  }

  if (fase === "cargando") {
    return error ? <MensajeError texto={error} /> : <Skeleton className="chamfer h-48" style={{ backgroundColor: "var(--surface)" }} />
  }

  return (
    <>
      {fase === "resultado" && resultado && estado ? (
        <PantallaResultado resultado={resultado} estado={estado} vencido={vencido} onOtraVez={() => { setResultado(null); setFase("portada"); cargar() }} onDesbloqueo={cargar} />
      ) : estado ? (
        <Portada
          estado={estado}
          vencido={vencido}
          busy={busy}
          aviso={aviso}
          error={error}
          onEmpezar={() => setConfirmando(true)}
          onDesbloqueo={cargar}
        />
      ) : (
        <MensajeError texto={error || "No se pudo cargar el examen."} />
      )}

      <AnimatePresence>
        {confirmando && estado && (
          <ConfirmarInicio estado={estado} onCancelar={() => setConfirmando(false)} onEmpezar={empezar} />
        )}
      </AnimatePresence>

      {fase === "en_curso" && estado && (
        <ModoExamen
          assignmentId={assignmentId}
          preguntas={preguntas}
          estado={estado}
          iniciadoEn={iniciadoEn}
          onEntregado={alEntregar}
        />
      )}
    </>
  )
}

function salirDePantallaCompleta() {
  if (document.fullscreenElement) document.exitFullscreen?.().catch(() => undefined)
}

/* ───────── Antes de empezar ───────── */
function Portada({
  estado,
  vencido,
  busy,
  aviso,
  error,
  onEmpezar,
  onDesbloqueo,
}: {
  estado: EstadoExamen
  vencido: boolean
  busy: boolean
  aviso: string
  error: string
  onEmpezar: () => void
  onDesbloqueo: () => void
}) {
  const bloqueado = !!estado.bloqueado_hasta
  const numeroIntento = estado.max_intentos - estado.intentos_restantes + 1
  return (
    <section className="flex flex-col gap-6 max-w-[78ch]">
      <header className="flex flex-col gap-2 pb-4" style={{ borderBottom: "1px solid var(--border-default)" }}>
        <span className="flex items-center gap-2 text-[11px] uppercase tracking-widest" style={{ color: "var(--signal-amber)", fontFamily: "var(--font-mono)" }}>
          <IconExam width={14} height={14} /> Examen final
        </span>
        <h2 className="text-xl sm:text-2xl font-bold m-0" style={{ color: "var(--text-heading)" }}>
          {estado.total_preguntas} preguntas · apruebas con {estado.puntaje_aprobacion} %
        </h2>
        <Intentos estado={estado} />
      </header>

      {aviso && <Nota tono="var(--signal-red)" texto={aviso} />}
      {estado.intento_abierto && !aviso && (
        <Nota tono="var(--signal-red)" texto="Saliste del intento anterior sin entregarlo: cuando vuelvas a empezar, ese intento cuenta como reprobado." />
      )}
      {estado.aprobado && !bloqueado && (
        <Nota
          tono="var(--signal-green)"
          texto={`Ya aprobaste este examen${estado.mejor_puntaje != null ? ` (mejor puntaje: ${Math.round(estado.mejor_puntaje)} %)` : ""}. Puedes volver a presentarlo para mejorar tu nota; la regla de intentos es la misma.`}
        />
      )}

      <ol className="m-0 pl-5 list-decimal flex flex-col gap-2 text-sm leading-relaxed" style={{ color: "var(--text-base)" }}>
        <li>Al empezar, el examen ocupa toda la pantalla y <strong>no puedes salir hasta entregarlo</strong>.</li>
        <li>Si recargas, cierras la pestaña o vuelves atrás, el intento <strong>se entrega con lo que lleves</strong>. Si esa entrega no alcanza a llegar, cuenta como 0.</li>
        <li>Tienes <strong>{estado.max_intentos} intentos</strong>. Si repruebas los {estado.max_intentos}, debes esperar <strong>24 horas</strong> para intentarlo otra vez.</li>
        <li>Las preguntas abiertas no distinguen mayúsculas; escribe solo la respuesta, sin explicaciones.</li>
      </ol>

      {bloqueado && estado.bloqueado_hasta ? (
        <Bloqueo hasta={estado.bloqueado_hasta} onFin={onDesbloqueo} />
      ) : (
        <Button
          onClick={onEmpezar}
          disabled={busy || vencido}
          className="self-start chamfer-sm font-mono text-xs uppercase tracking-wide"
        >
          {busy ? "Abriendo examen…" : `Empezar intento ${numeroIntento} de ${estado.max_intentos}`}
        </Button>
      )}
      {error && <MensajeError texto={error} />}
    </section>
  )
}

function Intentos({ estado }: { estado: EstadoExamen }) {
  const usados = estado.max_intentos - estado.intentos_restantes
  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="flex gap-1.5" aria-hidden="true">
        {Array.from({ length: estado.max_intentos }).map((_, i) => (
          <span
            key={i}
            className="chamfer-sm"
            style={{
              width: 22,
              height: 8,
              backgroundColor: i < usados ? "var(--signal-red)" : "var(--surface-hover)",
              border: `1px solid ${i < usados ? "var(--signal-red)" : "var(--border-strong)"}`,
            }}
          />
        ))}
      </div>
      <span className="text-xs" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
        {estado.bloqueado_hasta
          ? "Sin intentos: examen bloqueado"
          : `Te ${estado.intentos_restantes === 1 ? "queda 1 intento" : `quedan ${estado.intentos_restantes} intentos`} de ${estado.max_intentos}`}
      </span>
    </div>
  )
}

function Bloqueo({ hasta, onFin }: { hasta: string; onFin: () => void }) {
  const fin = new Date(hasta).getTime()
  const ahora = useAhora(1000)
  const restante = Math.max(0, fin - ahora)
  const terminado = restante === 0

  useEffect(() => {
    if (terminado) onFin()
  }, [terminado, onFin])

  return (
    <div className="chamfer flex flex-col sm:flex-row sm:items-center gap-4 p-4 sm:p-5" style={{ backgroundColor: "color-mix(in srgb, var(--signal-red) 7%, var(--surface))", border: "1px solid var(--signal-red-dim)" }}>
      <span className="chamfer-sm flex items-center justify-center shrink-0" style={{ width: 44, height: 44, backgroundColor: "color-mix(in srgb, var(--signal-red) 14%, transparent)", color: "var(--signal-red)" }}>
        <IconLock width={22} height={22} />
      </span>
      <div className="flex flex-col gap-1">
        <span className="text-sm font-semibold" style={{ color: "var(--text-heading)" }}>Reprobaste los 3 intentos</span>
        <span className="text-xs" style={{ color: "var(--text-muted)" }}>
          Podrás volver a presentarlo el {new Date(fin).toLocaleString()}. Mientras tanto, repasa la teoría y la práctica del laboratorio.
        </span>
      </div>
      <span className="sm:ml-auto text-2xl font-bold tabular-nums" style={{ color: "var(--signal-red)", fontFamily: "var(--font-mono)" }} aria-live="off">
        {formatoDuracion(restante)}
      </span>
    </div>
  )
}

function ConfirmarInicio({ estado, onCancelar, onEmpezar }: { estado: EstadoExamen; onCancelar: () => void; onEmpezar: () => void }) {
  const numero = estado.max_intentos - estado.intentos_restantes + 1
  return createPortal(
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 flex items-center justify-center p-4"
      style={{ zIndex: 1200, backgroundColor: "color-mix(in srgb, var(--canvas) 82%, transparent)", backdropFilter: "blur(4px)" }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirmar-examen-titulo"
    >
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="chamfer flex flex-col gap-4 p-6 w-full max-w-md"
        style={{ backgroundColor: "var(--canvas-raised)", border: "1px solid var(--signal-amber)" }}
      >
        <h3 id="confirmar-examen-titulo" className="text-lg font-bold m-0" style={{ color: "var(--text-heading)" }}>
          ¿Empezar el intento {numero} de {estado.max_intentos}?
        </h3>
        <p className="text-sm m-0 leading-relaxed" style={{ color: "var(--text-base)" }}>
          Desde que empieces, <strong>salir cuenta como entregar</strong>. Ten a mano lo que necesites y no recargues la página.
          {estado.intentos_restantes === 1 && " Es tu último intento: si lo repruebas, el examen se bloquea 24 horas."}
        </p>
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onCancelar} className="chamfer-sm font-mono text-xs uppercase">Todavía no</Button>
          <Button onClick={onEmpezar} autoFocus className="chamfer-sm font-mono text-xs uppercase">Empezar examen</Button>
        </div>
      </motion.div>
    </motion.div>,
    document.body,
  )
}

/* ───────── Durante el examen: pantalla completa y sin salida ───────── */
function ModoExamen({
  assignmentId,
  preguntas,
  estado,
  iniciadoEn,
  onEntregado,
}: {
  assignmentId: string
  preguntas: PreguntaExamen[]
  estado: EstadoExamen
  iniciadoEn: number
  onEntregado: (r: ResultadoExamen) => void
}) {
  const [respuestas, setRespuestas] = useState<Record<string, string>>({})
  const respuestasRef = useRef(respuestas)
  const entregadoRef = useRef(false)
  const [salidas, setSalidas] = useState(0)
  const [pidiendoSalir, setPidiendoSalir] = useState(false)
  const [confirmarEntrega, setConfirmarEntrega] = useState(false)
  const [enPantallaCompleta, setEnPantallaCompleta] = useState(true)
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState("")
  const ahora = useAhora(1000)

  useEffect(() => {
    respuestasRef.current = respuestas
  }, [respuestas])

  const entregar = useCallback(async () => {
    if (entregadoRef.current) return
    entregadoRef.current = true
    setEnviando(true)
    setError("")
    try {
      onEntregado(await submitExam(assignmentId, respuestasRef.current))
    } catch (err) {
      entregadoRef.current = false
      setError(err instanceof ApiError ? err.message : "No se pudo entregar el examen. Revisa tu conexión e inténtalo de nuevo.")
    } finally {
      setEnviando(false)
    }
  }, [assignmentId, onEntregado])

  // Candados mientras el examen está abierto.
  useEffect(() => {
    const avisarAntesDeSalir = (e: BeforeUnloadEvent) => {
      e.preventDefault()
      e.returnValue = ""
    }
    // Si igual se va (recarga o cierra), se entrega lo que lleve.
    const alOcultarPagina = () => {
      if (!entregadoRef.current) {
        entregadoRef.current = true
        entregarExamenAlSalir(assignmentId, respuestasRef.current)
      }
    }
    // Botón "atrás": se vuelve a poner la entrada del examen y se pregunta.
    window.history.pushState({ examen: true }, "", window.location.href)
    const alVolver = () => {
      window.history.pushState({ examen: true }, "", window.location.href)
      setPidiendoSalir(true)
    }
    const alCambiarVisibilidad = () => {
      if (document.visibilityState === "hidden") setSalidas((n) => n + 1)
    }
    const alCambiarPantallaCompleta = () => setEnPantallaCompleta(!!document.fullscreenElement)

    window.addEventListener("beforeunload", avisarAntesDeSalir)
    window.addEventListener("pagehide", alOcultarPagina)
    window.addEventListener("popstate", alVolver)
    document.addEventListener("visibilitychange", alCambiarVisibilidad)
    document.addEventListener("fullscreenchange", alCambiarPantallaCompleta)
    const overflowPrevio = document.body.style.overflow
    document.body.style.overflow = "hidden"
    return () => {
      window.removeEventListener("beforeunload", avisarAntesDeSalir)
      window.removeEventListener("pagehide", alOcultarPagina)
      window.removeEventListener("popstate", alVolver)
      document.removeEventListener("visibilitychange", alCambiarVisibilidad)
      document.removeEventListener("fullscreenchange", alCambiarPantallaCompleta)
      document.body.style.overflow = overflowPrevio
    }
  }, [assignmentId])

  const respondidas = preguntas.filter((p) => (respuestas[p.id] ?? "").trim()).length
  const faltan = preguntas.length - respondidas
  const numero = estado.max_intentos - estado.intentos_restantes + 1

  const pedirEntrega = () => (faltan > 0 ? setConfirmarEntrega(true) : entregar())

  return createPortal(
    <div
      className="fixed inset-0 flex flex-col"
      style={{ zIndex: 1100, backgroundColor: "var(--canvas)" }}
      role="dialog"
      aria-modal="true"
      aria-label="Examen final en curso"
    >
      <header className="shrink-0 flex flex-wrap items-center gap-x-4 gap-y-2 px-4 sm:px-8 py-3" style={{ borderBottom: "1px solid var(--border-default)", backgroundColor: "var(--canvas-raised)" }}>
        <span className="flex items-center gap-2 text-xs uppercase tracking-widest" style={{ color: "var(--signal-amber)", fontFamily: "var(--font-mono)" }}>
          <span className="pulso-alerta inline-block rounded-full" style={{ width: 8, height: 8, backgroundColor: "var(--signal-red)" }} aria-hidden="true" />
          Examen en curso · intento {numero} de {estado.max_intentos}
        </span>
        <span className="flex items-center gap-1.5 text-xs tabular-nums" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
          <IconClock width={13} height={13} /> {formatoDuracion(Math.max(0, ahora - iniciadoEn))}
        </span>
        <span className="text-xs" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
          {respondidas}/{preguntas.length} respondidas
        </span>
        <div className="ml-auto flex items-center gap-2">
          {!enPantallaCompleta && (
            <Button variant="outline" size="sm" onClick={() => document.documentElement.requestFullscreen?.().catch(() => undefined)} className="chamfer-sm font-mono text-[10px] uppercase">
              Pantalla completa
            </Button>
          )}
          <Button size="sm" onClick={pedirEntrega} disabled={enviando} className="chamfer-sm font-mono text-xs uppercase tracking-wide">
            {enviando ? "Calificando…" : "Entregar examen"}
          </Button>
        </div>
      </header>

      <div className="h-1 shrink-0" style={{ backgroundColor: "var(--surface-hover)" }} aria-hidden="true">
        <motion.div className="h-full" style={{ backgroundColor: "var(--signal-amber)", originX: 0 }} animate={{ scaleX: preguntas.length ? respondidas / preguntas.length : 0 }} transition={{ duration: 0.3 }} />
      </div>

      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto flex flex-col gap-7 px-4 sm:px-8 py-6 sm:py-10" style={{ maxWidth: 780 }}>
          {salidas > 0 && (
            <Nota
              tono="var(--signal-red)"
              texto={`Saliste de esta pestaña ${salidas === 1 ? "1 vez" : `${salidas} veces`}. Quédate en el examen: si cierras o recargas, se entrega con lo que lleves.`}
            />
          )}
          {error && <MensajeError texto={error} />}
          {preguntas.map((p, i) => (
            <fieldset key={p.id} className="flex flex-col gap-2 border-none p-0 m-0">
              <legend className="text-sm sm:text-base font-semibold mb-2 leading-relaxed" style={{ color: "var(--text-heading)" }}>
                <span style={{ color: "var(--signal-amber)", fontFamily: "var(--font-mono)" }}>{i + 1}.</span> {p.enunciado}
              </legend>
              {p.tipo === "opcion_multiple" && p.opciones ? (
                <div className="flex flex-col gap-1.5">
                  {p.opciones.map((op) => {
                    const marcada = respuestas[p.id] === op
                    return (
                      <label
                        key={op}
                        className="chamfer-sm flex items-center gap-2.5 text-sm cursor-pointer px-3 py-2.5 transition-colors"
                        style={{
                          backgroundColor: marcada ? "color-mix(in srgb, var(--signal-amber) 8%, transparent)" : "var(--surface)",
                          border: `1px solid ${marcada ? "var(--signal-amber)" : "var(--border-default)"}`,
                          color: "var(--text-base)",
                        }}
                      >
                        <input
                          type="radio"
                          name={p.id}
                          value={op}
                          checked={marcada}
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
                  aria-label={`Respuesta a la pregunta ${i + 1}`}
                  autoComplete="off"
                  spellCheck={false}
                  className="chamfer-sm w-full px-3 py-2.5 text-sm outline-none focus-visible:ring-2"
                  style={{ color: "var(--text-heading)", backgroundColor: "var(--surface)", border: "1px solid var(--border-default)", fontFamily: "var(--font-mono)" }}
                />
              )}
            </fieldset>
          ))}
          <Button onClick={pedirEntrega} disabled={enviando} className="self-start chamfer-sm font-mono text-xs uppercase tracking-wide">
            {enviando ? "Calificando…" : "Entregar examen"}
          </Button>
        </div>
      </main>

      <AnimatePresence>
        {(pidiendoSalir || confirmarEntrega) && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 flex items-center justify-center p-4"
            style={{ zIndex: 1200, backgroundColor: "color-mix(in srgb, var(--canvas) 80%, transparent)" }}
            role="alertdialog"
            aria-modal="true"
          >
            <div className="chamfer flex flex-col gap-4 p-6 w-full max-w-md" style={{ backgroundColor: "var(--canvas-raised)", border: "1px solid var(--signal-red)" }}>
              <h3 className="text-lg font-bold m-0" style={{ color: "var(--text-heading)" }}>
                {pidiendoSalir ? "No puedes salir del examen" : `Te faltan ${faltan} pregunta${faltan === 1 ? "" : "s"}`}
              </h3>
              <p className="text-sm m-0 leading-relaxed" style={{ color: "var(--text-base)" }}>
                {pidiendoSalir
                  ? "Para salir tienes que entregarlo. Se califica con lo que respondiste hasta ahora y cuenta como uno de tus intentos."
                  : "Las que dejes en blanco cuentan como incorrectas. ¿Entregar de todas formas?"}
              </p>
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => { setPidiendoSalir(false); setConfirmarEntrega(false) }} className="chamfer-sm font-mono text-xs uppercase" autoFocus>
                  Seguir respondiendo
                </Button>
                <Button onClick={() => { setPidiendoSalir(false); setConfirmarEntrega(false); entregar() }} className="chamfer-sm font-mono text-xs uppercase">
                  Entregar {pidiendoSalir ? "y salir" : "así"}
                </Button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>,
    document.body,
  )
}

/* ───────── Resultado ───────── */
function PantallaResultado({
  resultado,
  estado,
  vencido,
  onOtraVez,
  onDesbloqueo,
}: {
  resultado: ResultadoExamen
  estado: EstadoExamen
  vencido: boolean
  onOtraVez: () => void
  onDesbloqueo: () => void
}) {
  const aprobado = resultado.aprobado
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="chamfer flex flex-col items-center gap-4 p-6 sm:p-10 text-center max-w-[78ch]" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
      <StatusDot variant={aprobado ? "online" : "danger"} label={aprobado ? "Examen aprobado" : "Examen no aprobado"} />
      <ProgressRing percent={Math.round(resultado.puntaje)} size={140} stroke={8} color={aprobado ? "var(--signal-green)" : "var(--signal-red)"} />
      <p className="text-sm m-0" style={{ color: "var(--text-muted)" }}>
        {resultado.correctas} de {resultado.total} correctas · intento {resultado.numero_intento}
        {aprobado ? "" : ` · necesitas ${estado.puntaje_aprobacion} % para aprobar`}
      </p>
      {estado.bloqueado_hasta ? (
        <div className="w-full text-left">
          <Bloqueo hasta={estado.bloqueado_hasta} onFin={onDesbloqueo} />
        </div>
      ) : (
        <>
          <Intentos estado={estado} />
          {!vencido && (
            <Button onClick={onOtraVez} variant={aprobado ? "outline" : "default"} className="chamfer-sm font-mono text-xs uppercase tracking-wide">
              {aprobado ? "Presentarlo otra vez" : "Volver a intentarlo"}
            </Button>
          )}
        </>
      )}
    </motion.div>
  )
}

/* ───────── Piezas ───────── */
function Nota({ tono, texto }: { tono: string; texto: string }) {
  return (
    <p className="m-0 text-sm leading-relaxed chamfer-sm px-3 py-2" style={{ color: "var(--text-base)", backgroundColor: `color-mix(in srgb, ${tono} 9%, transparent)`, border: `1px solid color-mix(in srgb, ${tono} 45%, transparent)` }} role="status">
      {texto}
    </p>
  )
}

function MensajeError({ texto }: { texto: string }) {
  return (
    <p className="text-sm px-3 py-2 chamfer-sm m-0" style={{ color: "var(--signal-red)", backgroundColor: "color-mix(in srgb, var(--signal-red) 8%, transparent)", border: "1px solid var(--signal-red-dim)" }} role="alert">
      ▲ {texto}
    </p>
  )
}

/** Reloj que avanza cada `cadaMs` (para cronómetros y cuentas regresivas). */
function useAhora(cadaMs: number) {
  const [ahora, setAhora] = useState(() => Date.now())
  useEffect(() => {
    const id = window.setInterval(() => setAhora(Date.now()), cadaMs)
    return () => window.clearInterval(id)
  }, [cadaMs])
  return ahora
}

function formatoDuracion(ms: number) {
  const total = Math.floor(ms / 1000)
  const h = Math.floor(total / 3600)
  const m = Math.floor((total % 3600) / 60)
  const s = total % 60
  const dos = (n: number) => String(n).padStart(2, "0")
  return h > 0 ? `${h}:${dos(m)}:${dos(s)}` : `${dos(m)}:${dos(s)}`
}
