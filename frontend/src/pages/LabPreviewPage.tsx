import { useEffect, useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import {
  getLaboratorio,
  getToc,
  getSeccionPreview,
  checkFlagPreview,
  approveLab,
  rejectLab,
  resolveMediaUrl,
  ApiError,
  type LaboratorioDetalle,
  type ContenidoSeccionPreview,
} from "./api"
import Navbar from "../components/Navbar"
import Footer from "../components/Footer"
import { Skeleton } from "../components/ui/skeleton"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Textarea } from "../components/ui/textarea"
import SimulatedTerminal from "../components/SimulatedTerminal"
import { ContenidoHtml, PasosGuia } from "../components/ContenidoSeccion"

type TocItem = { id: string; orden: number; titulo: string; tiene_practica: boolean }

export default function LabPreviewPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const rol = localStorage.getItem("role") || "estudiante"
  const esAdmin = rol === "administrador"

  const [lab, setLab] = useState<LaboratorioDetalle | null>(null)
  const [secciones, setSecciones] = useState<TocItem[]>([])
  const [contenidos, setContenidos] = useState<Record<string, ContenidoSeccionPreview>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [busy, setBusy] = useState(false)
  const [mostrarRechazo, setMostrarRechazo] = useState(false)
  const [motivoRechazo, setMotivoRechazo] = useState("")

  useEffect(() => {
    if (!id) return
    let cancelled = false
    Promise.all([getLaboratorio(id), getToc(id)])
      .then(async ([labData, tocData]) => {
        if (cancelled) return
        setLab(labData)
        setSecciones(tocData.secciones)
        const entries = await Promise.all(
          tocData.secciones.map(async (s) => [s.id, await getSeccionPreview(id, s.id)] as const),
        )
        if (cancelled) return
        setContenidos(Object.fromEntries(entries))
      })
      .catch((err) => {
        if (cancelled) return
        setError(err instanceof ApiError ? err.message : "No se pudo cargar el laboratorio.")
      })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [id])

  const handleAprobar = async () => {
    if (!id) return
    setBusy(true)
    setError("")
    try {
      await approveLab(id)
      navigate("/dashboard")
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo aprobar el laboratorio.")
      setBusy(false)
    }
  }

  const handleRechazar = async () => {
    if (!id || !motivoRechazo.trim()) return
    setBusy(true)
    setError("")
    try {
      await rejectLab(id, motivoRechazo.trim())
      navigate("/dashboard")
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo rechazar el laboratorio.")
      setBusy(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: "var(--canvas)", color: "var(--text-base)" }}>
      <Navbar />
      <main className="flex-1">
        <div className="mx-auto px-4 sm:px-6 md:px-8 py-6 sm:py-8" style={{ maxWidth: "900px" }}>
          {loading ? (
            <div className="flex flex-col gap-3">
              <Skeleton className="chamfer h-10 w-2/3" style={{ backgroundColor: "var(--surface)" }} />
              <Skeleton className="chamfer h-40" style={{ backgroundColor: "var(--surface)" }} />
            </div>
          ) : error && !lab ? (
            <p className="text-sm px-3 py-2 chamfer-sm" style={{ color: "var(--signal-red)", backgroundColor: "rgba(255,71,87,0.08)", border: "1px solid var(--signal-red-dim)" }}>▲ {error}</p>
          ) : lab ? (
            <>
              <span className="text-[10px] uppercase tracking-widest font-bold" style={{ color: "var(--signal-amber)", fontFamily: "var(--font-mono)" }}>
                Vista previa — {lab.estado === "en_revision" ? "en revisión" : lab.estado}
              </span>
              <h1 className="text-2xl sm:text-3xl font-black uppercase mt-1 mb-2" style={{ color: "var(--text-heading)" }}>{lab.nombre}</h1>
              <p className="text-sm mb-6" style={{ color: "var(--text-muted)" }}>{lab.descripcion}</p>

              {lab.motivo_rechazo && (
                <div className="chamfer-sm p-3 mb-6 text-sm" style={{ backgroundColor: "rgba(255,71,87,0.08)", border: "1px solid var(--signal-red-dim)", color: "var(--text-base)" }}>
                  <strong style={{ color: "var(--signal-red)" }}>Último rechazo: </strong>{lab.motivo_rechazo}
                </div>
              )}

              {error && (
                <p className="text-sm mb-4 px-3 py-2 chamfer-sm" style={{ color: "var(--signal-red)", backgroundColor: "rgba(255,71,87,0.08)", border: "1px solid var(--signal-red-dim)" }}>▲ {error}</p>
              )}

              <div className="flex flex-col gap-6">
                {secciones.map((s) => {
                  const contenido = contenidos[s.id]
                  if (!contenido) return null
                  return <SeccionPreviewCard key={s.id} orden={s.orden} contenido={contenido} laboratorioId={id!} seccionId={s.id} />
                })}
              </div>

              {esAdmin && lab.estado === "en_revision" && (
                <div className="chamfer p-4 sm:p-5 mt-8 flex flex-col gap-3" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-strong)" }}>
                  <span className="text-xs font-bold uppercase tracking-wide" style={{ color: "var(--text-heading)", fontFamily: "var(--font-mono)" }}>Decisión</span>
                  {mostrarRechazo ? (
                    <div className="flex flex-col gap-2">
                      <Textarea value={motivoRechazo} onChange={(e) => setMotivoRechazo(e.target.value)} placeholder="Motivo del rechazo (visible para el instructor)" rows={3} className="chamfer-sm text-sm" />
                      <div className="flex gap-2">
                        <Button type="button" variant="outline" onClick={() => setMostrarRechazo(false)} className="chamfer-sm font-mono text-xs uppercase">Cancelar</Button>
                        <Button type="button" disabled={busy || !motivoRechazo.trim()} onClick={handleRechazar} className="chamfer-sm font-mono text-xs uppercase" style={{ backgroundColor: "var(--signal-red)" }}>
                          Confirmar rechazo
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex gap-2">
                      <Button type="button" variant="outline" disabled={busy} onClick={() => setMostrarRechazo(true)} className="chamfer-sm font-mono text-xs uppercase">
                        Rechazar
                      </Button>
                      <Button type="button" disabled={busy} onClick={handleAprobar} className="chamfer-sm font-mono text-xs uppercase">
                        {busy ? "Procesando…" : "Aprobar y publicar"}
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </>
          ) : null}
        </div>
      </main>
      <Footer />
    </div>
  )
}

function SeccionPreviewCard({
  orden,
  contenido,
  laboratorioId,
  seccionId,
}: {
  orden: number
  contenido: ContenidoSeccionPreview
  laboratorioId: string
  seccionId: string
}) {
  const [flagValor, setFlagValor] = useState("")
  const [flagBusy, setFlagBusy] = useState(false)
  const [flagResultado, setFlagResultado] = useState<boolean | null>(null)

  const probarFlag = async () => {
    if (!flagValor.trim()) return
    setFlagBusy(true)
    try {
      const { correcto } = await checkFlagPreview(laboratorioId, seccionId, flagValor)
      setFlagResultado(correcto)
    } catch {
      setFlagResultado(false)
    } finally {
      setFlagBusy(false)
    }
  }

  return (
    <div className="chamfer p-4 sm:p-5" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
      <h2 className="text-base font-bold uppercase tracking-wide mb-3 mt-0" style={{ color: "var(--text-heading)" }}>
        {orden}. {contenido.titulo}
      </h2>

      {(contenido.objetivos.length > 0 || contenido.duracion_estimada_minutos > 0) && (
        <div className="flex flex-wrap items-start gap-4 mb-4 chamfer-sm p-3" style={{ backgroundColor: "var(--surface-hover)", border: "1px solid var(--border-hairline)" }}>
          {contenido.objetivos.length > 0 && (
            <ul className="text-sm list-disc pl-4 flex-1 min-w-[200px]" style={{ color: "var(--text-base)" }}>
              {contenido.objetivos.map((o, i) => <li key={i}>{o}</li>)}
            </ul>
          )}
          <span className="text-xs font-mono shrink-0" style={{ color: "var(--signal-amber)" }}>{contenido.duracion_estimada_minutos} min</span>
        </div>
      )}

      <ContenidoHtml html={contenido.contenido_teorico} />

      {contenido.tiene_practica && (
        <div className="flex flex-col gap-4 mt-4 pt-4" style={{ borderTop: "1px solid var(--border-hairline)" }}>
          {contenido.pasos_guia.length > 0 && (
            <div>
              <span className="text-xs font-bold uppercase tracking-wide mb-2 block" style={{ color: "var(--signal-cyan)", fontFamily: "var(--font-mono)" }}>Guía paso a paso</span>
              <PasosGuia pasos={contenido.pasos_guia} />
            </div>
          )}

          {contenido.entorno_practica && (
            <div>
              <span className="text-xs font-bold uppercase tracking-wide mb-2 block" style={{ color: "var(--signal-cyan)", fontFamily: "var(--font-mono)" }}>Consola simulada</span>
              <SimulatedTerminal entorno={contenido.entorno_practica} />
            </div>
          )}

          <div>
            <span className="text-xs font-bold uppercase tracking-wide mb-2 block" style={{ color: "var(--signal-cyan)", fontFamily: "var(--font-mono)" }}>Probar flag</span>
            <div className="flex gap-2 items-center flex-wrap">
              <Input value={flagValor} onChange={(e) => { setFlagValor(e.target.value); setFlagResultado(null) }} placeholder="FLAG{...}" className="chamfer-sm h-9 font-mono flex-1 min-w-[200px]" />
              <Button type="button" size="sm" disabled={flagBusy || !flagValor.trim()} onClick={probarFlag} className="chamfer-sm font-mono text-xs uppercase">
                Verificar
              </Button>
              {flagResultado !== null && (
                <span className="text-xs font-bold uppercase" style={{ color: flagResultado ? "var(--signal-green)" : "var(--signal-red)" }}>
                  {flagResultado ? "✓ Correcta" : "✗ Incorrecta"}
                </span>
              )}
            </div>
          </div>

          <div>
            <span className="text-xs font-bold uppercase tracking-wide mb-1 block" style={{ color: "var(--signal-cyan)", fontFamily: "var(--font-mono)" }}>Entorno real</span>
            {contenido.tiene_dockerfile && contenido.dockerfile_url ? (
              <a href={resolveMediaUrl(contenido.dockerfile_url)} target="_blank" rel="noopener noreferrer" download className="text-xs font-mono underline" style={{ color: "var(--signal-cyan)" }}>
                ↓ Descargar Dockerfile para revisar y construir manualmente
              </a>
            ) : (
              <span className="text-xs" style={{ color: "var(--text-muted)" }}>Sin Dockerfile subido para esta sección.</span>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
