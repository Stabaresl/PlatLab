import { useEffect, useRef, useState, type ReactNode } from "react"
import { AnimatePresence, motion } from "framer-motion"
import {
  ApiError,
  aprobarSolicitudInstructor,
  listSolicitudesInstructor,
  rechazarSolicitudInstructor,
  type EstadoSolicitudFiltro,
  type ResultadoOpenAlex,
  type SolicitudInstructorAdmin,
} from "../pages/api"
import SectionHeading from "./SectionHeading"
import { IconGlobe, IconUsers } from "./icons"
import { Textarea } from "./ui/textarea"
import { relativeTime } from "./ActivityTimeline"

const FILTROS: { value: EstadoSolicitudFiltro; label: string }[] = [
  { value: "pendiente", label: "Pendientes" },
  { value: "aprobada", label: "Aprobadas" },
  { value: "rechazada", label: "Rechazadas" },
  { value: "todas", label: "Todas" },
]

const TIPO_LABEL: Record<string, string> = {
  docente: "Docente",
  investigador: "Investigador",
  profesional: "Profesional",
}

const ESTADO_ESTILO: Record<SolicitudInstructorAdmin["estado"], { label: string; color: string }> = {
  pendiente: { label: "Pendiente", color: "var(--signal-amber)" },
  aprobada: { label: "Aprobada", color: "var(--signal-green)" },
  rechazada: { label: "Rechazada", color: "var(--signal-red)" },
}

/**
 * Cola de solicitudes de instructor. El admin decide; OpenAlex solo aporta
 * evidencia: cada tarjeta pone lado a lado lo que declaró la persona (y los
 * datos de su cuenta) y lo que OpenAlex encontró para ese ORCID.
 */
export default function SolicitudesInstructorPanel() {
  const ref = useRef<HTMLElement>(null)
  const [filtro, setFiltro] = useState<EstadoSolicitudFiltro>("pendiente")
  const [items, setItems] = useState<SolicitudInstructorAdmin[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [busyId, setBusyId] = useState<string | null>(null)
  const [rechazandoId, setRechazandoId] = useState<string | null>(null)
  const [motivo, setMotivo] = useState("")

  useEffect(() => {
    let cancelled = false
    listSolicitudesInstructor(filtro)
      .then((data) => {
        if (cancelled) return
        setItems(data)
        setError("")
      })
      .catch((err) => !cancelled && setError(err instanceof ApiError ? err.message : "No se pudieron cargar las solicitudes."))
      .finally(() => !cancelled && setLoading(false))
    return () => { cancelled = true }
  }, [filtro])

  // La notificación "X pidió ser instructor" enlaza a /dashboard#solicitudes-instructor.
  useEffect(() => {
    if (!loading && window.location.hash === "#solicitudes-instructor") {
      ref.current?.scrollIntoView({ behavior: "smooth", block: "start" })
    }
  }, [loading])

  const resolver = async (s: SolicitudInstructorAdmin, aprobar: boolean) => {
    setBusyId(s.id)
    setError("")
    try {
      const r = aprobar ? await aprobarSolicitudInstructor(s.id) : await rechazarSolicitudInstructor(s.id, motivo.trim())
      setItems((prev) =>
        filtro === "todas"
          ? prev.map((x) => (x.id === s.id ? { ...x, estado: r.estado, motivo_rechazo: r.motivo_rechazo, resolved_at: new Date().toISOString() } : x))
          : prev.filter((x) => x.id !== s.id),
      )
      setRechazandoId(null)
      setMotivo("")
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo resolver la solicitud.")
    } finally {
      setBusyId(null)
    }
  }

  const pendientes = filtro === "pendiente" ? items.length : null

  return (
    <section ref={ref} id="solicitudes-instructor" className="mb-8 sm:mb-10 scroll-mt-24">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3 mb-5">
        <SectionHeading
          icon={<IconUsers />}
          title="Solicitudes de Instructor"
          subtitle={
            pendientes === null
              ? "Historial de solicitudes"
              : pendientes === 0
                ? "No hay solicitudes esperando tu revisión"
                : `${pendientes} solicitud${pendientes === 1 ? "" : "es"} esperando tu decisión`
          }
        />
        <div role="tablist" aria-label="Filtrar solicitudes" className="flex flex-wrap gap-1.5 self-start sm:self-auto">
          {FILTROS.map((f) => (
            <button
              key={f.value}
              type="button"
              role="tab"
              aria-selected={filtro === f.value}
              onClick={() => {
                if (f.value === filtro) return
                setLoading(true)
                setFiltro(f.value)
              }}
              className="chamfer-sm px-2.5 py-1 text-[11px] uppercase tracking-wide cursor-pointer border transition-colors"
              style={{
                fontFamily: "var(--font-mono)",
                backgroundColor: filtro === f.value ? "rgba(56,214,245,0.12)" : "transparent",
                borderColor: filtro === f.value ? "var(--signal-cyan)" : "var(--border-default)",
                color: filtro === f.value ? "var(--signal-cyan)" : "var(--text-muted)",
              }}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <p role="alert" className="text-sm mb-4 px-3 py-2 chamfer-sm" style={{ color: "var(--signal-red)", backgroundColor: "rgba(255,71,87,0.08)", border: "1px solid var(--signal-red-dim)" }}>
          ▲ {error}
        </p>
      )}

      {loading ? (
        <div className="chamfer h-32 animate-pulse" style={{ backgroundColor: "var(--surface)" }} />
      ) : items.length === 0 ? (
        <div className="chamfer p-8 text-center" style={{ border: "1px dashed var(--border-strong)" }}>
          <p className="text-xs uppercase tracking-widest m-0" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
            [ {filtro === "pendiente" ? "Nada pendiente — todo al día" : "Sin solicitudes en este filtro"} ]
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          <AnimatePresence mode="popLayout">
            {items.map((s) => (
              <motion.article
                key={s.id}
                layout
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, x: 24 }}
                transition={{ duration: 0.22 }}
                className="chamfer p-4 sm:p-5"
                style={{ backgroundColor: "var(--surface)", border: `1px solid ${s.estado === "pendiente" ? "var(--border-strong)" : "var(--border-default)"}` }}
              >
                <header className="flex flex-wrap items-center gap-2 mb-4">
                  <span className="text-base font-bold" style={{ color: "var(--text-heading)" }}>
                    {s.usuario.nombre_completo || s.nombre_declarado}
                  </span>
                  <Chip color={ESTADO_ESTILO[s.estado].color}>{ESTADO_ESTILO[s.estado].label}</Chip>
                  <Chip color="var(--signal-cyan)">{TIPO_LABEL[s.tipo] || s.tipo}</Chip>
                  {s.created_at && (
                    <span className="text-xs ml-auto" style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
                      solicitó {relativeTime(s.created_at)}
                    </span>
                  )}
                </header>

                <div className="grid gap-4 md:grid-cols-2">
                  <Columna titulo="Quién se inscribió">
                    <Dato label="Correo">{s.usuario.email || "—"}</Dato>
                    <Dato label="Nombre declarado">{s.nombre_declarado}</Dato>
                    <Dato label="Cuenta creada">{s.usuario.registrado_desde ? new Date(s.usuario.registrado_desde).toLocaleDateString() : "—"}</Dato>
                    <Dato label="Institución">{s.institucion || "—"}</Dato>
                    <Dato label="Especialidades">{s.especialidades || "—"}</Dato>
                    {s.motivacion && (
                      <p className="text-sm mt-2 mb-0 pl-3 italic" style={{ color: "var(--text-base)", borderLeft: "2px solid var(--border-strong)" }}>
                        “{s.motivacion}”
                      </p>
                    )}
                  </Columna>

                  <Columna
                    titulo="Lo que encontró OpenAlex"
                    accion={
                      <a href={s.orcid_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-xs no-underline" style={{ color: "var(--signal-cyan)", fontFamily: "var(--font-mono)" }}>
                        <IconGlobe width={12} height={12} /> {s.orcid} ↗
                      </a>
                    }
                  >
                    <EvidenciaOpenAlex resultado={s.openalex} nombreDeclarado={s.nombre_declarado} />
                  </Columna>
                </div>

                {s.estado === "rechazada" && s.motivo_rechazo && (
                  <p className="text-sm mt-4 mb-0" style={{ color: "var(--text-muted)" }}>
                    <strong style={{ color: "var(--signal-red)" }}>Motivo del rechazo:</strong> {s.motivo_rechazo}
                  </p>
                )}

                {s.estado === "pendiente" && (
                  <footer className="mt-4 pt-4" style={{ borderTop: "1px solid var(--border-default)" }}>
                    {rechazandoId === s.id ? (
                      <div className="flex flex-col gap-2">
                        <label htmlFor={`motivo-${s.id}`} className="text-xs uppercase tracking-wide" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                          Motivo (la persona lo verá en su notificación)
                        </label>
                        <Textarea
                          id={`motivo-${s.id}`}
                          value={motivo}
                          onChange={(e) => setMotivo(e.target.value)}
                          maxLength={300}
                          rows={2}
                          autoFocus
                          placeholder="Ej.: El ORCID no tiene publicaciones a tu nombre. Escríbenos con otro perfil o más datos."
                          className="chamfer-sm resize-none"
                        />
                        <div className="flex flex-wrap gap-2 justify-end">
                          <AccionBoton onClick={() => { setRechazandoId(null); setMotivo("") }} color="var(--text-muted)" disabled={busyId === s.id}>
                            Cancelar
                          </AccionBoton>
                          <AccionBoton onClick={() => resolver(s, false)} color="var(--signal-red)" disabled={busyId === s.id || !motivo.trim()}>
                            {busyId === s.id ? "Enviando…" : "Confirmar rechazo"}
                          </AccionBoton>
                        </div>
                      </div>
                    ) : (
                      <div className="flex flex-wrap gap-2 justify-end">
                        <AccionBoton onClick={() => { setRechazandoId(s.id); setMotivo("") }} color="var(--signal-red)" disabled={busyId === s.id}>
                          Rechazar
                        </AccionBoton>
                        <AccionBoton onClick={() => resolver(s, true)} color="var(--signal-green)" disabled={busyId === s.id} solido>
                          {busyId === s.id ? "Aprobando…" : "Aprobar como instructor"}
                        </AccionBoton>
                      </div>
                    )}
                  </footer>
                )}
              </motion.article>
            ))}
          </AnimatePresence>
        </div>
      )}
    </section>
  )
}

function EvidenciaOpenAlex({ resultado, nombreDeclarado }: { resultado: ResultadoOpenAlex | null; nombreDeclarado: string }) {
  if (!resultado) {
    return (
      <p className="text-sm m-0" style={{ color: "var(--text-muted)" }}>
        Todavía sin respuesta de OpenAlex (la consulta corre en segundo plano y reintenta si la red falla). Puedes revisar el perfil ORCID directamente.
      </p>
    )
  }
  if (!resultado.encontrado) {
    return (
      <Señal tono="var(--signal-red)" titulo="ORCID no encontrado">
        OpenAlex no tiene un autor con ese ORCID. Puede ser un perfil nuevo o sin publicaciones indexadas.
      </Señal>
    )
  }
  return (
    <>
      <Dato label="Nombre en OpenAlex">{resultado.nombre_openalex || "—"}</Dato>
      <Dato label="Publicaciones">{resultado.works_count}</Dato>
      <div className="mt-2">
        {resultado.coincide_nombre ? (
          <Señal tono="var(--signal-green)" titulo="El nombre coincide">
            “{nombreDeclarado}” corresponde al autor del ORCID. Ojo: esto no prueba que la cuenta sea de esa persona; el correo institucional ayuda a confirmarlo.
          </Señal>
        ) : (
          <Señal tono="var(--signal-amber)" titulo="El nombre no coincide">
            Declaró “{nombreDeclarado}”, pero el ORCID es de otra persona según OpenAlex.
          </Señal>
        )}
      </div>
    </>
  )
}

function Columna({ titulo, accion, children }: { titulo: string; accion?: ReactNode; children: ReactNode }) {
  return (
    <div className="chamfer-sm p-3 sm:p-4" style={{ backgroundColor: "var(--canvas)", border: "1px solid var(--border-default)" }}>
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="text-[11px] uppercase tracking-widest" style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>{titulo}</span>
        {accion}
      </div>
      {children}
    </div>
  )
}

function Dato({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex gap-3 py-1 text-sm">
      <span className="w-32 shrink-0" style={{ color: "var(--text-muted)" }}>{label}</span>
      <span className="min-w-0 break-words" style={{ color: "var(--text-heading)" }}>{children}</span>
    </div>
  )
}

function Señal({ tono, titulo, children }: { tono: string; titulo: string; children: ReactNode }) {
  return (
    <div className="chamfer-sm px-3 py-2 text-sm" style={{ backgroundColor: `color-mix(in srgb, ${tono} 10%, transparent)`, border: `1px solid ${tono}` }}>
      <strong className="block text-xs uppercase tracking-wide mb-0.5" style={{ color: tono, fontFamily: "var(--font-mono)" }}>{titulo}</strong>
      <span style={{ color: "var(--text-base)" }}>{children}</span>
    </div>
  )
}

function Chip({ color, children }: { color: string; children: ReactNode }) {
  return (
    <span className="text-[10px] font-bold px-2 py-0.5 chamfer-sm uppercase tracking-wide" style={{ backgroundColor: `color-mix(in srgb, ${color} 12%, transparent)`, color, border: `1px solid ${color}` }}>
      {children}
    </span>
  )
}

function AccionBoton({ onClick, color, disabled, solido, children }: { onClick: () => void; color: string; disabled?: boolean; solido?: boolean; children: ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="chamfer-sm px-3 py-1.5 text-xs font-semibold uppercase tracking-wide cursor-pointer border transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      style={{
        fontFamily: "var(--font-mono)",
        borderColor: color,
        color: solido ? "var(--canvas)" : color,
        backgroundColor: solido ? color : "transparent",
      }}
    >
      {children}
    </button>
  )
}
