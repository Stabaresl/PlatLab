import { useEffect, useMemo, useState, type FormEvent } from "react"
import { Link, useNavigate } from "react-router-dom"
import { AnimatePresence, motion } from "framer-motion"
import {
  ApiError,
  crearSala,
  formatearCodigoSala,
  laboratoriosParaSala,
  listSalas,
  unirseSala,
  vistaPreviaSala,
  type LaboratorioParaSala,
  type Sala,
  type VistaPreviaSala,
} from "./api"
import Navbar from "../components/Navbar"
import FondoAscii from "../components/FondoAscii"
import Footer from "../components/Footer"
import { Button } from "../components/ui/button"
import { Skeleton } from "../components/ui/skeleton"
import { EstadoSalaChip } from "../components/salas/comun"
import { NIVEL_LABEL } from "../components/salas/formato"

// /salas — punto de entrada a las salas privadas. El estudiante entra con
// un código; el instructor o admin crea salas y ve las suyas.
export default function SalasPage() {
  const rol = localStorage.getItem("role") || "estudiante"
  const esAnfitrion = rol === "instructor" || rol === "administrador"
  const [salas, setSalas] = useState<Sala[] | null>(null)
  const [error, setError] = useState("")

  const cargar = () =>
    listSalas()
      .then(setSalas)
      .catch((err) => setError(err instanceof ApiError ? err.message : "No se pudieron cargar las salas."))

  useEffect(() => {
    cargar()
  }, [])

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: "var(--canvas)", color: "var(--text-base)" }}>
      <FondoAscii />
      <div className="relative z-10 flex flex-col flex-1">
      <Navbar />
      <main className="flex-1">
        <div className="mx-auto px-4 sm:px-6 md:px-8 py-8 sm:py-10 flex flex-col gap-8" style={{ maxWidth: "1200px" }}>
          <header className="flex flex-col gap-2">
            <h1 className="text-2xl sm:text-3xl font-black uppercase m-0" style={{ color: "var(--text-heading)", fontFamily: "var(--font-display)" }}>
              Salas
            </h1>
            <p className="text-sm sm:text-base m-0 max-w-[68ch]" style={{ color: "var(--text-muted)" }}>
              {esAnfitrion
                ? "Abre una sala sobre un laboratorio publicado, comparte el código y sigue en vivo cómo avanza cada estudiante. Cada uno trabaja en su propio entorno."
                : "Tu instructor te comparte un código de sala. Al entrar recibes el laboratorio con tu propio entorno de práctica y compites en el tablero de la sala."}
            </p>
          </header>

          {esAnfitrion ? <CrearSalaPanel onCreada={cargar} /> : <UnirsePanel />}

          <section className="flex flex-col gap-3">
            <h2 className="text-sm font-bold uppercase tracking-wider m-0" style={{ color: "var(--text-heading)", fontFamily: "var(--font-mono)" }}>
              {rol === "administrador" ? "Todas las salas" : "Mis salas"}
            </h2>
            {error && <p className="text-sm m-0" style={{ color: "var(--signal-red)" }}>▲ {error}</p>}
            {salas === null && !error ? (
              <Skeleton className="chamfer h-32" style={{ backgroundColor: "var(--surface)" }} />
            ) : salas && salas.length === 0 ? (
              <div className="chamfer p-8 text-center" style={{ border: "1px dashed var(--border-strong)" }}>
                <p className="text-sm m-0" style={{ color: "var(--text-muted)" }}>
                  {esAnfitrion ? "Todavía no has abierto salas. Crea la primera arriba." : "Aún no estás en ninguna sala. Pídele el código a tu instructor."}
                </p>
              </div>
            ) : (
              salas && <ListaSalas salas={salas} esAnfitrion={esAnfitrion} />
            )}
          </section>
        </div>
      </main>
      <Footer />
      </div>
    </div>
  )
}

function ListaSalas({ salas, esAnfitrion }: { salas: Sala[]; esAnfitrion: boolean }) {
  return (
    <ul className="m-0 p-0 list-none flex flex-col" style={{ borderTop: "1px solid var(--border-default)" }}>
      {salas.map((s) => (
        <li key={s.id} className="flex flex-col md:flex-row md:items-center gap-3 md:gap-6 py-4" style={{ borderBottom: "1px solid var(--border-default)" }}>
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2 mb-1">
              <Link to={`/salas/${s.id}`} className="text-base font-semibold no-underline hover:underline" style={{ color: "var(--text-heading)" }}>
                {s.nombre}
              </Link>
              <EstadoSalaChip estado={s.estado} />
            </div>
            <p className="text-sm m-0 truncate" style={{ color: "var(--text-muted)" }}>
              {s.laboratorio.nombre} · {NIVEL_LABEL[s.laboratorio.nivel] || s.laboratorio.nivel} · anfitrión {s.anfitrion.nombre}
            </p>
          </div>
          <dl className="m-0 grid grid-cols-3 gap-4 text-xs shrink-0" style={{ fontFamily: "var(--font-mono)" }}>
            {esAnfitrion && (
              <div>
                <dt style={{ color: "var(--text-dim)" }}>Código</dt>
                <dd className="m-0 font-bold" style={{ color: "var(--signal-amber)" }}>{formatearCodigoSala(s.codigo)}</dd>
              </div>
            )}
            <div>
              <dt style={{ color: "var(--text-dim)" }}>Personas</dt>
              <dd className="m-0" style={{ color: "var(--text-heading)" }}>{s.participantes}/{s.capacidad}</dd>
            </div>
            <div>
              <dt style={{ color: "var(--text-dim)" }}>{esAnfitrion ? "Terminaron" : "Tu puesto"}</dt>
              <dd className="m-0" style={{ color: "var(--signal-green)" }}>{esAnfitrion ? s.completados : s.mi_posicion_final ? `${s.mi_posicion_final}.º` : "—"}</dd>
            </div>
          </dl>
          <div className="flex gap-2 shrink-0">
            {!esAnfitrion && s.mi_asignacion_id && s.estado !== "finalizada" && (
              <Button asChild size="sm" className="chamfer-sm font-mono text-xs uppercase">
                <Link to={`/resolver/${s.mi_asignacion_id}`}>Al laboratorio</Link>
              </Button>
            )}
            <Button asChild size="sm" variant="outline" className="chamfer-sm font-mono text-xs uppercase">
              <Link to={`/salas/${s.id}`}>{esAnfitrion ? "Tablero" : "Ver sala"}</Link>
            </Button>
          </div>
        </li>
      ))}
    </ul>
  )
}

function normalizar(codigo: string) {
  return codigo.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 6)
}

export function UnirsePanel({ codigoInicial = "" }: { codigoInicial?: string }) {
  const navigate = useNavigate()
  const [codigo, setCodigo] = useState(normalizar(codigoInicial))
  const [preview, setPreview] = useState<VistaPreviaSala | null>(null)
  const [buscando, setBuscando] = useState(false)
  const [error, setError] = useState("")
  const [entrando, setEntrando] = useState(false)

  useEffect(() => {
    if (codigo.length !== 6) return
    let cancelado = false
    const t = setTimeout(() => {
      setBuscando(true)
      vistaPreviaSala(codigo)
        .then((p) => !cancelado && (setPreview(p), setError("")))
        .catch((err) => !cancelado && (setPreview(null), setError(err instanceof ApiError ? err.message : "No se pudo verificar el código.")))
        .finally(() => !cancelado && setBuscando(false))
    }, 250)
    return () => {
      cancelado = true
      clearTimeout(t)
    }
  }, [codigo])

  const entrar = async (e: FormEvent) => {
    e.preventDefault()
    if (preview?.ya_participo && preview.sala_id) {
      navigate(`/salas/${preview.sala_id}`)
      return
    }
    setEntrando(true)
    setError("")
    try {
      const r = await unirseSala(codigo)
      navigate(`/salas/${r.sala_id}`)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo entrar a la sala.")
      setEntrando(false)
    }
  }

  const mostrado = codigo.length > 3 ? `${codigo.slice(0, 3)}-${codigo.slice(3)}` : codigo
  const listo = codigo.length === 6 && preview && (preview.acepta_ingresos || preview.ya_participo)

  return (
    <form onSubmit={entrar} className="chamfer grid gap-6 p-5 sm:p-6 md:grid-cols-[minmax(0,22rem)_minmax(0,1fr)] items-start" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
      <div className="flex flex-col gap-2">
        <label htmlFor="codigo-sala" className="text-xs font-bold uppercase tracking-wider" style={{ color: "var(--signal-amber)", fontFamily: "var(--font-mono)" }}>
          Código de la sala
        </label>
        <input
          id="codigo-sala"
          value={mostrado}
          onChange={(e) => {
            const nuevo = normalizar(e.target.value)
            setCodigo(nuevo)
            if (nuevo.length !== 6) {
              setPreview(null)
              setError("")
            }
          }}
          inputMode="text"
          autoComplete="off"
          autoCapitalize="characters"
          spellCheck={false}
          placeholder="ABC-123"
          className="chamfer-sm w-full px-4 py-3 text-2xl sm:text-3xl tracking-[0.25em] text-center uppercase outline-none focus-visible:ring-2"
          style={{ fontFamily: "var(--font-mono)", color: "var(--text-heading)", backgroundColor: "var(--surface-sunken)", border: "1px solid var(--border-strong)" }}
          aria-describedby="codigo-ayuda"
        />
        <p id="codigo-ayuda" className="text-xs m-0" style={{ color: "var(--text-dim)" }}>
          Seis caracteres. Mayúsculas o minúsculas da igual.
        </p>
      </div>

      <div className="flex flex-col gap-3 min-h-[7rem] justify-center" aria-live="polite">
        {buscando && <p className="text-sm m-0" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>Buscando la sala…</p>}
        {!buscando && error && <p className="text-sm m-0" style={{ color: "var(--signal-red)" }}>▲ {error}</p>}
        {!buscando && !error && !preview && <p className="text-sm m-0" style={{ color: "var(--text-muted)" }}>Escribe el código y verás aquí de qué sala se trata antes de entrar.</p>}
        <AnimatePresence>
          {!buscando && preview && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex flex-col gap-3">
              <div>
                <p className="text-lg font-semibold m-0" style={{ color: "var(--text-heading)" }}>{preview.nombre}</p>
                <p className="text-sm m-0" style={{ color: "var(--text-muted)" }}>
                  {preview.laboratorio.nombre} · {NIVEL_LABEL[preview.laboratorio.nivel] || preview.laboratorio.nivel} · con {preview.anfitrion}
                </p>
                {preview.descripcion && <p className="text-sm mt-2 mb-0" style={{ color: "var(--text-base)" }}>{preview.descripcion}</p>}
              </div>
              <p className="text-xs m-0" style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
                {preview.participantes}/{preview.capacidad} personas · {preview.ya_participo ? "ya estás dentro" : preview.acepta_ingresos ? "recibe participantes" : "no recibe participantes"}
              </p>
              <Button type="submit" disabled={!listo || entrando} className="self-start chamfer-sm font-mono text-xs uppercase tracking-wide">
                {entrando ? "Entrando…" : preview.ya_participo ? "Volver a la sala →" : "Entrar a la sala →"}
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </form>
  )
}

function CrearSalaPanel({ onCreada }: { onCreada: () => void }) {
  const navigate = useNavigate()
  const [abierto, setAbierto] = useState(false)
  const [labs, setLabs] = useState<LaboratorioParaSala[] | null>(null)
  const [nombre, setNombre] = useState("")
  const [laboratorioId, setLaboratorioId] = useState("")
  const [capacidad, setCapacidad] = useState(30)
  const [descripcion, setDescripcion] = useState("")
  const [cierre, setCierre] = useState("")
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    if (!abierto || labs) return
    laboratoriosParaSala()
      .then((data) => {
        setLabs(data)
        if (data[0]) setLaboratorioId((actual) => actual || data[0].id)
      })
      .catch(() => setLabs([]))
  }, [abierto, labs])

  const lab = useMemo(() => labs?.find((l) => l.id === laboratorioId), [labs, laboratorioId])

  const crear = async (e: FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError("")
    try {
      const sala = await crearSala({
        nombre: nombre.trim(),
        laboratorio_id: laboratorioId,
        capacidad,
        descripcion: descripcion.trim(),
        fecha_fin: cierre ? new Date(cierre).toISOString() : null,
      })
      onCreada()
      navigate(`/salas/${sala.id}`)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo crear la sala.")
      setBusy(false)
    }
  }

  if (!abierto) {
    return (
      <div className="chamfer flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-amber)" }}>
        <p className="text-sm m-0" style={{ color: "var(--text-base)" }}>
          Una sala admite hasta 100 personas. Cada una recibe su propia asignación y su propio contenedor, y el tablero se actualiza solo.
        </p>
        <Button type="button" onClick={() => setAbierto(true)} className="chamfer-sm font-mono text-xs uppercase tracking-wide shrink-0">
          + Nueva sala
        </Button>
      </div>
    )
  }

  const campo = "chamfer-sm w-full px-3 py-2.5 text-sm outline-none focus-visible:ring-2"
  const estiloCampo = { color: "var(--text-heading)", backgroundColor: "var(--surface-sunken)", border: "1px solid var(--border-default)" }
  const etiqueta = "text-xs font-semibold uppercase tracking-wider"
  const estiloEtiqueta = { color: "var(--text-muted)", fontFamily: "var(--font-mono)" }

  return (
    <form onSubmit={crear} className="chamfer flex flex-col gap-5 p-5 sm:p-6" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-amber)" }}>
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-base font-bold m-0" style={{ color: "var(--text-heading)" }}>Nueva sala</h2>
        <button type="button" className="consola-btn" onClick={() => setAbierto(false)}>Cancelar</button>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <label className="flex flex-col gap-1.5">
          <span className={etiqueta} style={estiloEtiqueta}>Nombre</span>
          <input required maxLength={120} value={nombre} onChange={(e) => setNombre(e.target.value)} placeholder="Seguridad web · grupo 2 · lunes" className={campo} style={estiloCampo} />
        </label>
        <label className="flex flex-col gap-1.5">
          <span className={etiqueta} style={estiloEtiqueta}>Laboratorio</span>
          <select required value={laboratorioId} onChange={(e) => setLaboratorioId(e.target.value)} className={campo} style={estiloCampo} disabled={!labs}>
            {!labs && <option>Cargando…</option>}
            {labs?.length === 0 && <option value="">No hay laboratorios publicados disponibles</option>}
            {labs?.map((l) => (
              <option key={l.id} value={l.id}>
                {l.nombre} · {NIVEL_LABEL[l.nivel_dificultad]} · {l.secciones} secc.{l.tipo === "personalizado" ? " · tuyo" : ""}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1.5">
          <span className={etiqueta} style={estiloEtiqueta}>Capacidad (1–100)</span>
          <input type="number" min={1} max={100} required value={capacidad} onChange={(e) => setCapacidad(Math.max(1, Math.min(100, parseInt(e.target.value || "1", 10))))} className={campo} style={estiloCampo} />
        </label>
        <label className="flex flex-col gap-1.5">
          <span className={etiqueta} style={estiloEtiqueta}>Cierre (opcional)</span>
          <input type="datetime-local" value={cierre} onChange={(e) => setCierre(e.target.value)} className={campo} style={estiloCampo} />
        </label>
        <label className="flex flex-col gap-1.5 md:col-span-2">
          <span className={etiqueta} style={estiloEtiqueta}>Indicaciones para los estudiantes (opcional)</span>
          <textarea maxLength={1000} rows={2} value={descripcion} onChange={(e) => setDescripcion(e.target.value)} placeholder="Terminen hasta la tarea 3; el examen queda para la casa." className={`${campo} resize-y`} style={estiloCampo} />
        </label>
      </div>
      {lab && <p className="text-sm m-0" style={{ color: "var(--text-muted)" }}>{lab.descripcion}</p>}
      {error && <p className="text-sm m-0" style={{ color: "var(--signal-red)" }}>▲ {error}</p>}
      <Button type="submit" disabled={busy || !laboratorioId || !nombre.trim()} className="self-start chamfer-sm font-mono text-xs uppercase tracking-wide">
        {busy ? "Creando…" : "Crear sala y ver el código"}
      </Button>
    </form>
  )
}
