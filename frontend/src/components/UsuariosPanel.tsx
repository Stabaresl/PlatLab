import { useEffect, useRef, useState } from "react"
import { ApiError, buscarUsuarios, disableUser, enableUser, updateUser, type Rol, type UsuarioItem } from "../pages/api"
import { haceCuanto } from "./salas/formato"
import SectionHeading from "./SectionHeading"
import { IconUsers, IconSearch } from "./icons"

const TAMANO_PAGINA = 25

const ROLES: { valor: Rol | ""; label: string }[] = [
  { valor: "", label: "Todos" },
  { valor: "estudiante", label: "Estudiantes" },
  { valor: "instructor", label: "Instructores" },
  { valor: "administrador", label: "Admins" },
]
const ESTADOS: { valor: "" | "true" | "false"; label: string }[] = [
  { valor: "", label: "Todos" },
  { valor: "true", label: "Activos" },
  { valor: "false", label: "Inactivos" },
]
const COLOR_ROL: Record<Rol, string> = {
  estudiante: "var(--signal-cyan)",
  instructor: "var(--signal-green)",
  administrador: "var(--signal-amber)",
}

/**
 * Tabla completa de usuarios del panel de admin: búsqueda por nombre o correo,
 * filtros por rol y estado, paginación en el servidor, cambio de rol en línea
 * y habilitar/deshabilitar (deshabilitar cierra sus sesiones en el acto).
 */
export default function UsuariosPanel() {
  const [buscar, setBuscar] = useState("")
  const [consulta, setConsulta] = useState("")
  const [rol, setRol] = useState<Rol | "">("")
  const [activo, setActivo] = useState<"" | "true" | "false">("")
  const [pagina, setPagina] = useState(0)
  const [datos, setDatos] = useState<{ total: number; filas: UsuarioItem[] } | null>(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState("")
  const [ocupado, setOcupado] = useState<string | null>(null)

  // La búsqueda espera a que se deje de escribir (no una consulta por tecla).
  const consultaRef = useRef(consulta)
  useEffect(() => {
    const t = setTimeout(() => {
      if (consultaRef.current === buscar) return
      consultaRef.current = buscar
      setCargando(true)
      setPagina(0)
      setConsulta(buscar)
    }, 300)
    return () => clearTimeout(t)
  }, [buscar])

  useEffect(() => {
    let cancelado = false
    buscarUsuarios({ buscar: consulta, rol, activo, limit: TAMANO_PAGINA, offset: pagina * TAMANO_PAGINA })
      .then((r) => {
        if (cancelado) return
        setDatos({ total: r.count, filas: r.results })
        setError("")
      })
      .catch((err) => !cancelado && setError(err instanceof ApiError ? err.message : "No se pudieron cargar los usuarios."))
      .finally(() => !cancelado && setCargando(false))
    return () => {
      cancelado = true
    }
  }, [consulta, rol, activo, pagina])

  const reemplazar = (u: UsuarioItem) => setDatos((d) => (d ? { ...d, filas: d.filas.map((x) => (x.id === u.id ? { ...x, ...u } : x)) } : d))

  const cambiarRol = async (u: UsuarioItem, nuevo: Rol) => {
    if (nuevo === u.rol) return
    setOcupado(u.id)
    setError("")
    try {
      reemplazar(await updateUser(u.id, { rol: nuevo }))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo cambiar el rol.")
    } finally {
      setOcupado(null)
    }
  }

  const alternarActivo = async (u: UsuarioItem) => {
    setOcupado(u.id)
    setError("")
    try {
      reemplazar(u.is_active ? await disableUser(u.id) : await enableUser(u.id))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo actualizar la cuenta.")
    } finally {
      setOcupado(null)
    }
  }

  const total = datos?.total ?? 0
  const desde = total === 0 ? 0 : pagina * TAMANO_PAGINA + 1
  const hasta = Math.min(total, (pagina + 1) * TAMANO_PAGINA)
  const paginas = Math.max(1, Math.ceil(total / TAMANO_PAGINA))

  return (
    <section className="flex flex-col gap-4" aria-labelledby="usuarios-titulo">
      <div id="usuarios-titulo">
        <SectionHeading icon={<IconUsers />} title="Usuarios" subtitle={datos ? `${total} ${total === 1 ? "cuenta" : "cuentas"} con estos filtros` : "Cargando…"} />
      </div>

      <div className="flex flex-col lg:flex-row gap-3 lg:items-center">
        <label className="chamfer-sm flex items-center gap-2 px-3 flex-1 min-w-0" style={{ backgroundColor: "var(--surface-sunken)", border: "1px solid var(--border-default)" }}>
          <IconSearch width={14} height={14} style={{ color: "var(--text-dim)" }} />
          <span className="sr-only">Buscar por nombre o correo</span>
          <input
            value={buscar}
            onChange={(e) => setBuscar(e.target.value)}
            placeholder="Buscar por nombre o correo"
            className="flex-1 min-w-0 py-2.5 bg-transparent border-none outline-none text-sm"
            style={{ color: "var(--text-heading)" }}
          />
        </label>
        <Segmento opciones={ROLES} valor={rol} onCambio={(v) => { setCargando(true); setRol(v); setPagina(0) }} etiqueta="Rol" />
        <Segmento opciones={ESTADOS} valor={activo} onCambio={(v) => { setCargando(true); setActivo(v); setPagina(0) }} etiqueta="Estado" />
      </div>

      {error && <p role="alert" className="text-sm m-0 px-3 py-2 chamfer-sm" style={{ color: "var(--signal-red)", backgroundColor: "color-mix(in srgb, var(--signal-red) 8%, transparent)", border: "1px solid var(--signal-red-dim)" }}>▲ {error}</p>}

      <div className="overflow-x-auto" style={{ border: "1px solid var(--border-default)", opacity: cargando ? 0.6 : 1 }}>
        <table className="w-full text-sm" style={{ borderCollapse: "collapse", minWidth: 720 }}>
          <thead>
            <tr style={{ backgroundColor: "var(--surface)" }}>
              {["Persona", "Rol", "Estado", "Registro", "Último acceso"].map((h) => (
                <th key={h} scope="col" className="text-left px-3 py-2 text-[10px] uppercase tracking-wider font-semibold" style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)", borderBottom: "1px solid var(--border-strong)" }}>
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {datos?.filas.length === 0 && (
              <tr>
                <td colSpan={5} className="px-3 py-8 text-center text-sm" style={{ color: "var(--text-muted)" }}>Ninguna cuenta coincide con la búsqueda.</td>
              </tr>
            )}
            {datos?.filas.map((u) => (
              <tr key={u.id} style={{ borderBottom: "1px solid var(--border-hairline)", opacity: ocupado === u.id ? 0.55 : 1 }}>
                <td className="px-3 py-2.5 max-w-[22rem]">
                  <div className="font-medium truncate" style={{ color: u.is_active ? "var(--text-heading)" : "var(--text-muted)" }}>{u.nombre_completo}</div>
                  <div className="text-xs truncate" style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>{u.email}</div>
                </td>
                <td className="px-3 py-2.5">
                  <select
                    value={u.rol}
                    disabled={ocupado === u.id}
                    onChange={(e) => cambiarRol(u, e.target.value as Rol)}
                    aria-label={`Rol de ${u.nombre_completo}`}
                    className="chamfer-sm px-2 py-1 text-xs outline-none cursor-pointer focus-visible:ring-2"
                    style={{ color: COLOR_ROL[u.rol], backgroundColor: "var(--surface-sunken)", border: `1px solid color-mix(in srgb, ${COLOR_ROL[u.rol]} 45%, transparent)`, fontFamily: "var(--font-mono)" }}
                  >
                    <option value="estudiante">estudiante</option>
                    <option value="instructor">instructor</option>
                    <option value="administrador">administrador</option>
                  </select>
                </td>
                <td className="px-3 py-2.5">
                  <button
                    type="button"
                    disabled={ocupado === u.id}
                    onClick={() => alternarActivo(u)}
                    className="consola-btn"
                    style={{ color: u.is_active ? "var(--signal-green)" : "var(--signal-red)", borderColor: u.is_active ? "var(--signal-green-dim)" : "var(--signal-red-dim)" }}
                    title={u.is_active ? "Deshabilitar: cierra sus sesiones y no podrá entrar" : "Habilitar de nuevo"}
                  >
                    {u.is_active ? "● Activa" : "○ Inactiva"}
                  </button>
                </td>
                <td className="px-3 py-2.5 text-xs" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                  {u.date_joined ? new Date(u.date_joined).toLocaleDateString("es-CO") : "—"}
                </td>
                <td className="px-3 py-2.5 text-xs" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                  {u.last_login ? haceCuanto(u.last_login) : "nunca"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between gap-3 flex-wrap">
        <span className="text-xs" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
          {desde}–{hasta} de {total}
        </span>
        <div className="flex items-center gap-2">
          <button type="button" className="consola-btn" disabled={pagina === 0} onClick={() => { setCargando(true); setPagina((p) => Math.max(0, p - 1)) }}>← Anterior</button>
          <span className="text-xs" style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>{pagina + 1}/{paginas}</span>
          <button type="button" className="consola-btn" disabled={pagina >= paginas - 1} onClick={() => { setCargando(true); setPagina((p) => p + 1) }}>Siguiente →</button>
        </div>
      </div>
    </section>
  )
}

function Segmento<T extends string>({ opciones, valor, onCambio, etiqueta }: { opciones: { valor: T; label: string }[]; valor: T; onCambio: (v: T) => void; etiqueta: string }) {
  return (
    <div role="radiogroup" aria-label={etiqueta} className="flex flex-wrap gap-1">
      {opciones.map((o) => {
        const activo = o.valor === valor
        return (
          <button
            key={o.valor || "todos"}
            type="button"
            role="radio"
            aria-checked={activo}
            onClick={() => onCambio(o.valor)}
            className="chamfer-sm px-2.5 py-1.5 text-[11px] uppercase tracking-wide cursor-pointer border transition-colors focus-visible:ring-2"
            style={{
              fontFamily: "var(--font-mono)",
              backgroundColor: activo ? "color-mix(in srgb, var(--signal-cyan) 12%, transparent)" : "transparent",
              borderColor: activo ? "var(--signal-cyan)" : "var(--border-default)",
              color: activo ? "var(--signal-cyan)" : "var(--text-muted)",
            }}
          >
            {o.label}
          </button>
        )
      })}
    </div>
  )
}
