import { useState, type FormEvent } from "react"
import { Link, useNavigate } from "react-router-dom"

/**
 * Atajo a las salas en los dashboards: el estudiante escribe el código y va
 * directo a la vista previa; instructores y admins van a crear o seguir sus salas.
 */
export default function AccesoSalas({ rol }: { rol: string }) {
  const navigate = useNavigate()
  const [codigo, setCodigo] = useState("")
  const limpio = codigo.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 6)

  if (rol !== "estudiante") {
    return (
      <div className="chamfer flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 sm:p-5" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-amber)" }}>
        <div>
          <p className="text-sm font-semibold m-0" style={{ color: "var(--text-heading)" }}>Salas en vivo</p>
          <p className="text-sm m-0" style={{ color: "var(--text-muted)" }}>
            Abre una sala sobre un laboratorio, comparte el código y sigue a tu grupo en un tablero en tiempo real.
          </p>
        </div>
        <Link to="/salas" className="consola-btn no-underline shrink-0" style={{ color: "var(--signal-amber)", borderColor: "var(--border-amber)" }}>
          Ir a salas →
        </Link>
      </div>
    )
  }

  const entrar = (e: FormEvent) => {
    e.preventDefault()
    if (limpio.length === 6) navigate(`/salas/unirse/${limpio}`)
  }

  return (
    <form onSubmit={entrar} className="chamfer flex flex-col sm:flex-row sm:items-center gap-3 p-4 sm:p-5" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-amber)" }}>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold m-0" style={{ color: "var(--text-heading)" }}>¿Tu instructor te dio un código de sala?</p>
        <p className="text-sm m-0" style={{ color: "var(--text-muted)" }}>Entra y trabaja el laboratorio con tu grupo, con tablero en vivo y XP extra por terminar.</p>
      </div>
      <div className="flex gap-2 shrink-0">
        <label className="sr-only" htmlFor="acceso-codigo-sala">Código de sala</label>
        <input
          id="acceso-codigo-sala"
          value={limpio.length > 3 ? `${limpio.slice(0, 3)}-${limpio.slice(3)}` : limpio}
          onChange={(e) => setCodigo(e.target.value)}
          placeholder="ABC-123"
          autoComplete="off"
          spellCheck={false}
          className="chamfer-sm w-32 px-3 py-2 text-sm tracking-[0.2em] uppercase text-center outline-none focus-visible:ring-2"
          style={{ fontFamily: "var(--font-mono)", color: "var(--text-heading)", backgroundColor: "var(--surface-sunken)", border: "1px solid var(--border-strong)" }}
        />
        <button type="submit" disabled={limpio.length !== 6} className="consola-btn" style={{ color: "var(--signal-amber)", borderColor: "var(--border-amber)" }}>
          Entrar
        </button>
      </div>
    </form>
  )
}
