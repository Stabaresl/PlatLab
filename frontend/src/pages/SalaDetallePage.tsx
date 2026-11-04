import { lazy, Suspense, useCallback, useEffect, useMemo, useState } from "react"
import { Link, useParams } from "react-router-dom"
import {
  ApiError,
  cambiarEstadoSala,
  formatearCodigoSala,
  getSala,
  type EstadoSala,
  type ParticipanteTablero,
  type SalaDetalle,
} from "./api"
import Navbar from "../components/Navbar"
import Footer from "../components/Footer"
import { Button } from "../components/ui/button"
import { Skeleton } from "../components/ui/skeleton"
import { EstadoSalaChip } from "../components/salas/comun"
import { haceCuanto, NIVEL_LABEL } from "../components/salas/formato"

const OrbitaSala = lazy(() => import("../components/three/OrbitaSala"))

const REFRESCO_MS = 8000
// Mismo reparto que `XP_POR_PUESTO_SALA` en gamification (backend).
const BONO_POR_PUESTO = [
  { puesto: "1.º", xp: 150 },
  { puesto: "2.º", xp: 110 },
  { puesto: "3.º", xp: 80 },
  { puesto: "resto", xp: 50 },
]

export default function SalaDetallePage() {
  const { id } = useParams<{ id: string }>()
  const [sala, setSala] = useState<SalaDetalle | null>(null)
  const [error, setError] = useState("")
  const [actualizado, setActualizado] = useState<Date | null>(null)

  const cargar = useCallback(() => {
    if (!id) return
    getSala(id)
      .then((s) => {
        setSala(s)
        setActualizado(new Date())
        setError("")
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "No se pudo cargar la sala."))
  }, [id])

  useEffect(() => {
    cargar()
    // Tablero en vivo: se refresca solo mientras la pestaña está a la vista.
    const t = setInterval(() => {
      if (!document.hidden) cargar()
    }, REFRESCO_MS)
    return () => clearInterval(t)
  }, [cargar])

  const nodos = useMemo(
    () => (sala?.tablero || []).map((p) => ({ id: p.estudiante_id, porcentaje: p.porcentaje, completado: p.posicion_final !== null || p.completado, esYo: p.es_yo })),
    [sala],
  )

  if (!sala) {
    return (
      <div className="min-h-screen flex flex-col" style={{ backgroundColor: "var(--canvas)" }}>
        <Navbar />
        <main className="flex-1 mx-auto w-full px-4 sm:px-6 md:px-8 py-10" style={{ maxWidth: "1280px" }}>
          {error ? (
            <div className="flex flex-col gap-3 items-start">
              <p className="text-sm m-0" style={{ color: "var(--signal-red)" }}>▲ {error}</p>
              <Link to="/salas" className="consola-btn no-underline">← Volver a salas</Link>
            </div>
          ) : (
            <Skeleton className="chamfer h-80" style={{ backgroundColor: "var(--surface)" }} />
          )}
        </main>
        <Footer />
      </div>
    )
  }

  const yo = sala.tablero.find((p) => p.es_yo)
  const avancePromedio = sala.tablero.length ? Math.round(sala.tablero.reduce((a, p) => a + p.porcentaje, 0) / sala.tablero.length) : 0

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: "var(--canvas)", color: "var(--text-base)" }}>
      <Navbar />
      <main className="flex-1">
        <div className="mx-auto px-4 sm:px-6 md:px-8 py-6 sm:py-8 flex flex-col gap-6" style={{ maxWidth: "1280px" }}>
          <Link to="/salas" className="text-xs uppercase tracking-wide no-underline self-start" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
            ← Salas
          </Link>

          <header className="flex flex-col lg:flex-row lg:items-end justify-between gap-4">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2 mb-2">
                <EstadoSalaChip estado={sala.estado} />
                <span className="text-[11px] uppercase tracking-wider" style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
                  anfitrión · {sala.anfitrion.nombre}
                </span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-black uppercase m-0 leading-tight" style={{ color: "var(--text-heading)", fontFamily: "var(--font-display)", overflowWrap: "anywhere" }}>
                {sala.nombre}
              </h1>
              <p className="text-sm mt-2 mb-0" style={{ color: "var(--text-muted)" }}>
                {sala.laboratorio.nombre} · {NIVEL_LABEL[sala.laboratorio.nivel] || sala.laboratorio.nivel}
                {sala.fecha_fin && ` · cierra ${new Date(sala.fecha_fin).toLocaleString("es-CO", { dateStyle: "medium", timeStyle: "short" })}`}
              </p>
              {sala.descripcion && <p className="text-sm mt-2 mb-0 max-w-[70ch]" style={{ color: "var(--text-base)" }}>{sala.descripcion}</p>}
            </div>
            {!sala.es_anfitrion && sala.mi_asignacion_id && sala.estado !== "finalizada" && (
              <Button asChild className="chamfer-sm font-mono text-xs uppercase tracking-wide self-start lg:self-auto">
                <Link to={`/resolver/${sala.mi_asignacion_id}`}>Abrir el laboratorio →</Link>
              </Button>
            )}
          </header>

          <div className="grid gap-6 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] items-start">
            {/* Columna izquierda: código + lobby 3D + controles */}
            <div className="flex flex-col gap-4 min-w-0">
              {sala.es_anfitrion ? <CodigoSala sala={sala} /> : yo && <MiEstado yo={yo} total={sala.tablero.length} />}

              <div className="chamfer relative overflow-hidden" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
                <Suspense fallback={<div style={{ height: 340 }} />}>
                  <OrbitaSala nodos={nodos} alto={340} />
                </Suspense>
                <dl className="absolute inset-x-0 bottom-0 m-0 grid grid-cols-3 text-center py-3" style={{ backgroundColor: "color-mix(in srgb, var(--surface) 82%, transparent)", borderTop: "1px solid var(--border-hairline)", fontFamily: "var(--font-mono)" }}>
                  <div>
                    <dt className="text-[10px] uppercase tracking-wider" style={{ color: "var(--text-dim)" }}>Personas</dt>
                    <dd className="m-0 text-lg font-bold" style={{ color: "var(--text-heading)" }}>{sala.participantes}<span className="text-xs" style={{ color: "var(--text-dim)" }}>/{sala.capacidad}</span></dd>
                  </div>
                  <div>
                    <dt className="text-[10px] uppercase tracking-wider" style={{ color: "var(--text-dim)" }}>Avance medio</dt>
                    <dd className="m-0 text-lg font-bold" style={{ color: "var(--signal-cyan)" }}>{avancePromedio}%</dd>
                  </div>
                  <div>
                    <dt className="text-[10px] uppercase tracking-wider" style={{ color: "var(--text-dim)" }}>Terminaron</dt>
                    <dd className="m-0 text-lg font-bold" style={{ color: "var(--signal-green)" }}>{sala.completados}</dd>
                  </div>
                </dl>
              </div>
              <p className="text-xs m-0" style={{ color: "var(--text-dim)" }}>
                Cada punto es una persona: se acerca al núcleo a medida que avanza y se acopla en verde al terminar{sala.es_anfitrion ? "" : "; el tuyo tiene un anillo ámbar"}.
              </p>

              {sala.es_anfitrion ? <ControlesSala sala={sala} onCambio={cargar} /> : <Recompensas />}
            </div>

            {/* Columna derecha: tablero */}
            <section className="flex flex-col gap-3 min-w-0" aria-labelledby="tablero-titulo">
              <div className="flex items-end justify-between gap-3">
                <h2 id="tablero-titulo" className="text-sm font-bold uppercase tracking-wider m-0" style={{ color: "var(--text-heading)", fontFamily: "var(--font-mono)" }}>
                  Tablero
                </h2>
                <span className="text-[11px]" style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)" }} aria-live="polite">
                  {actualizado ? `actualizado ${actualizado.toLocaleTimeString("es-CO")}` : ""} · cada {REFRESCO_MS / 1000} s
                </span>
              </div>
              {error && <p className="text-xs m-0" style={{ color: "var(--signal-amber)" }}>▲ {error} (se reintenta solo)</p>}
              <Tablero filas={sala.tablero} esAnfitrion={sala.es_anfitrion} />
            </section>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  )
}

function CodigoSala({ sala }: { sala: SalaDetalle }) {
  const [copiado, setCopiado] = useState<"codigo" | "enlace" | null>(null)
  const enlace = `${window.location.origin}/salas/unirse/${sala.codigo}`
  const copiar = async (texto: string, cual: "codigo" | "enlace") => {
    try {
      await navigator.clipboard.writeText(texto)
      setCopiado(cual)
      setTimeout(() => setCopiado(null), 1500)
    } catch {
      // Sin portapapeles (http en red local): el código queda a la vista para dictarlo.
    }
  }
  return (
    <div className="chamfer p-5 flex flex-col gap-3" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-amber)" }}>
      <span className="text-[11px] font-bold uppercase tracking-wider" style={{ color: "var(--signal-amber)", fontFamily: "var(--font-mono)" }}>
        Código de ingreso
      </span>
      <p className="m-0 text-4xl sm:text-5xl font-black tracking-[0.18em] select-all" style={{ color: "var(--text-heading)", fontFamily: "var(--font-display)" }}>
        {formatearCodigoSala(sala.codigo)}
      </p>
      <p className="text-xs m-0" style={{ color: "var(--text-muted)" }}>
        Los estudiantes lo escriben en <span style={{ fontFamily: "var(--font-mono)" }}>Salas</span>, o entran directo con el enlace.
      </p>
      <div className="flex flex-wrap gap-2">
        <button type="button" className="consola-btn" data-estado={copiado === "codigo" ? "ok" : undefined} onClick={() => copiar(sala.codigo, "codigo")}>
          {copiado === "codigo" ? "Copiado" : "Copiar código"}
        </button>
        <button type="button" className="consola-btn" data-estado={copiado === "enlace" ? "ok" : undefined} onClick={() => copiar(enlace, "enlace")}>
          {copiado === "enlace" ? "Copiado" : "Copiar enlace de invitación"}
        </button>
      </div>
      {!sala.acepta_ingresos && sala.estado !== "finalizada" && (
        <p className="text-xs m-0" style={{ color: "var(--signal-amber)" }}>Los ingresos están cerrados: el código no deja entrar a nadie nuevo.</p>
      )}
    </div>
  )
}

function ControlesSala({ sala, onCambio }: { sala: SalaDetalle; onCambio: () => void }) {
  const [busy, setBusy] = useState(false)
  const [confirmarFin, setConfirmarFin] = useState(false)
  const [error, setError] = useState("")
  const cambiar = async (estado: EstadoSala) => {
    setBusy(true)
    setError("")
    try {
      await cambiarEstadoSala(sala.id, estado)
      onCambio()
      setConfirmarFin(false)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo cambiar el estado.")
    } finally {
      setBusy(false)
    }
  }
  if (sala.estado === "finalizada") {
    return <p className="text-sm m-0" style={{ color: "var(--text-muted)" }}>Sala finalizada: el tablero queda como registro y ya no reparte puestos.</p>
  }
  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap gap-2">
        {sala.estado === "abierta" ? (
          <Button type="button" variant="outline" size="sm" disabled={busy} onClick={() => cambiar("cerrada")} className="chamfer-sm font-mono text-xs uppercase">
            Cerrar ingresos
          </Button>
        ) : (
          <Button type="button" variant="outline" size="sm" disabled={busy} onClick={() => cambiar("abierta")} className="chamfer-sm font-mono text-xs uppercase">
            Abrir ingresos
          </Button>
        )}
        {!confirmarFin ? (
          <Button type="button" variant="outline" size="sm" disabled={busy} onClick={() => setConfirmarFin(true)} className="chamfer-sm font-mono text-xs uppercase hover:text-[var(--signal-red)] hover:border-[var(--signal-red)]">
            Finalizar sala
          </Button>
        ) : (
          <span className="flex flex-wrap items-center gap-2">
            <span className="text-xs" style={{ color: "var(--signal-red)" }}>No se puede reabrir. ¿Finalizar?</span>
            <Button type="button" size="sm" disabled={busy} onClick={() => cambiar("finalizada")} className="chamfer-sm font-mono text-xs uppercase" style={{ backgroundColor: "var(--signal-red)" }}>
              Sí, finalizar
            </Button>
            <button type="button" className="consola-btn" onClick={() => setConfirmarFin(false)}>No</button>
          </span>
        )}
      </div>
      <p className="text-xs m-0" style={{ color: "var(--text-dim)" }}>Cerrar ingresos no saca a nadie: quienes ya entraron siguen trabajando.</p>
      {error && <p className="text-xs m-0" style={{ color: "var(--signal-red)" }}>▲ {error}</p>}
    </div>
  )
}

function MiEstado({ yo, total }: { yo: ParticipanteTablero; total: number }) {
  const terminado = yo.posicion_final !== null
  return (
    <div className="chamfer p-5 flex flex-col gap-2" style={{ backgroundColor: "var(--surface)", border: `1px solid ${terminado ? "var(--signal-green-dim)" : "var(--border-amber)"}` }}>
      <span className="text-[11px] font-bold uppercase tracking-wider" style={{ color: terminado ? "var(--signal-green)" : "var(--signal-amber)", fontFamily: "var(--font-mono)" }}>
        {terminado ? "Terminaste" : yo.completado_antes ? "Ya habías hecho este laboratorio" : "Tu posición"}
      </span>
      <p className="m-0 text-4xl font-black" style={{ color: "var(--text-heading)", fontFamily: "var(--font-display)" }}>
        {terminado ? `${yo.posicion_final}.º` : `${yo.puesto}.º`}
        <span className="text-base font-normal" style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}> de {total}</span>
      </p>
      <p className="text-sm m-0" style={{ color: "var(--text-muted)" }}>
        {terminado
          ? "Tu puesto ya quedó fijado. El bono de XP se sumó a tu perfil."
          : yo.completado_antes
            ? "Lo completaste antes de entrar, así que no compites por puesto en esta sala."
            : `${yo.secciones_completadas} de ${yo.secciones_total} secciones. Termina las secciones y aprueba el examen para fijar tu puesto.`}
      </p>
    </div>
  )
}

function Recompensas() {
  return (
    <div className="chamfer-sm p-4 flex flex-col gap-2" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
      <span className="text-[11px] font-bold uppercase tracking-wider" style={{ color: "var(--text-heading)", fontFamily: "var(--font-mono)" }}>Bono por terminar la sala</span>
      <ul className="m-0 p-0 list-none grid grid-cols-4 gap-2 text-center" style={{ fontFamily: "var(--font-mono)" }}>
        {BONO_POR_PUESTO.map((b) => (
          <li key={b.puesto} className="chamfer-sm py-2" style={{ backgroundColor: "var(--surface-sunken)", border: "1px solid var(--border-hairline)" }}>
            <span className="block text-[10px] uppercase" style={{ color: "var(--text-dim)" }}>{b.puesto}</span>
            <span className="block text-sm font-bold" style={{ color: "var(--signal-amber)" }}>+{b.xp} XP</span>
          </li>
        ))}
      </ul>
      <p className="text-xs m-0" style={{ color: "var(--text-dim)" }}>
        Se suma al XP del laboratorio. Terminar salas desbloquea logros, títulos y cosméticos (por ejemplo, «Campeón de Sala» al llegar primero).
      </p>
    </div>
  )
}

function Tablero({ filas, esAnfitrion }: { filas: ParticipanteTablero[]; esAnfitrion: boolean }) {
  if (filas.length === 0) {
    return (
      <div className="chamfer p-8 text-center" style={{ border: "1px dashed var(--border-strong)" }}>
        <p className="text-sm m-0" style={{ color: "var(--text-muted)" }}>
          {esAnfitrion ? "Todavía no entra nadie. Comparte el código y verás aparecer a cada persona aquí." : "Eres la primera persona en la sala."}
        </p>
      </div>
    )
  }
  return (
    <div className="overflow-x-auto" style={{ border: "1px solid var(--border-default)" }}>
      <table className="w-full text-sm" style={{ borderCollapse: "collapse", minWidth: 560 }}>
        <thead>
          <tr style={{ backgroundColor: "var(--surface)" }}>
            {["#", "Persona", "Avance", "Examen", "Estado", "Actividad"].map((h) => (
              <th key={h} scope="col" className="text-left px-3 py-2 text-[10px] uppercase tracking-wider font-semibold" style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)", borderBottom: "1px solid var(--border-strong)" }}>
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {filas.map((p) => {
            const terminado = p.posicion_final !== null
            const podio = terminado && p.posicion_final! <= 3
            return (
              <tr key={p.estudiante_id} style={{ backgroundColor: p.es_yo ? "color-mix(in srgb, var(--signal-amber) 7%, transparent)" : "transparent", borderBottom: "1px solid var(--border-hairline)" }}>
                <td className="px-3 py-2.5 font-bold" style={{ color: podio ? "var(--signal-amber)" : "var(--text-muted)", fontFamily: "var(--font-mono)" }}>{p.puesto}</td>
                <td className="px-3 py-2.5" style={{ color: "var(--text-heading)" }}>
                  {p.nombre}
                  {p.es_yo && <span className="ml-2 text-[10px] uppercase" style={{ color: "var(--signal-amber)", fontFamily: "var(--font-mono)" }}>tú</span>}
                </td>
                <td className="px-3 py-2.5">
                  <div className="flex items-center gap-2">
                    <div className="w-20 h-1.5 overflow-hidden" style={{ backgroundColor: "var(--surface-hover)" }}>
                      <div className="h-full origin-left transition-transform duration-500" style={{ transform: `scaleX(${p.porcentaje / 100})`, backgroundColor: terminado ? "var(--signal-green)" : "var(--signal-cyan)" }} />
                    </div>
                    <span className="text-xs" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>{p.secciones_completadas}/{p.secciones_total}</span>
                  </div>
                </td>
                <td className="px-3 py-2.5 text-xs" style={{ color: p.mejor_puntaje !== null && p.mejor_puntaje >= 60 ? "var(--signal-green)" : "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                  {p.mejor_puntaje !== null ? `${Math.round(p.mejor_puntaje)}%` : "—"}
                </td>
                <td className="px-3 py-2.5 text-xs" style={{ fontFamily: "var(--font-mono)" }}>
                  {terminado ? (
                    <span style={{ color: "var(--signal-green)" }}>terminó {p.posicion_final}.º</span>
                  ) : p.completado_antes ? (
                    <span style={{ color: "var(--text-muted)" }}>ya lo había hecho</span>
                  ) : (
                    <span style={{ color: "var(--signal-cyan)" }}>en curso</span>
                  )}
                </td>
                <td className="px-3 py-2.5 text-xs" style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>{haceCuanto(p.ultima_actividad)}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
