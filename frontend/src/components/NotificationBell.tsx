import { useEffect, useRef, useState } from "react"
import { createPortal } from "react-dom"
import { useNavigate } from "react-router-dom"
import { listNotifications, markNotificationRead, ApiError, type Notificacion } from "../pages/api"
import { relativeTime, TONE_COLOR, type ActivityTone } from "./ActivityTimeline"
import { IconBell } from "./icons"

const TIPO_TONE: Record<string, ActivityTone> = {
  instructor_aprobado: "success",
  laboratorio_aprobado: "success",
  invitacion: "info",
  laboratorio_publicado: "info",
  instructor_rechazado: "warning",
  laboratorio_rechazado: "warning",
  acceso_vencido: "warning",
  vencimiento_proximo: "warning",
  reporte_resuelto: "info",
  logro_desbloqueado: "success",
}

const POLL_INTERVAL_MS = 60_000
const PANEL_WIDTH = 340
const VIEWPORT_MARGIN = 16

// A dónde navegar al hacer click, según el tipo de notificación — no
// alcanza con entidad_tipo solo: "invitacion" y "acceso_vencido" comparten
// entidad_tipo="asignacion", pero una invitación pendiente todavía no
// tiene Progreso creado (se crea recién al aceptar, ver
// AceptarInvitacionUseCase) — /resolver/:id fallaría con 404 para esa.
function rutaDeNotificacion(n: Notificacion): string | null {
  switch (n.tipo) {
    case "acceso_vencido":
      return n.entidad_id ? `/resolver/${n.entidad_id}` : "/dashboard"
    case "invitacion":
    case "reporte_resuelto":
    case "instructor_aprobado":
    case "instructor_rechazado":
      return "/dashboard"
    case "laboratorio_aprobado":
    case "laboratorio_rechazado":
      return n.entidad_id ? `/laboratorios/${n.entidad_id}/revision` : "/dashboard"
    case "laboratorio_publicado":
      return "/laboratorios"
    case "logro_desbloqueado":
      return "/profile"
    default:
      return null
  }
}

// Campana de notificaciones — conecta `listNotifications`/
// `markNotificationRead` (ya existían en api.ts, sin ningún componente
// que los llamara) a la UI. Sin esto, notificaciones reales como
// "tu laboratorio fue aprobado" o "tu ORCID fue verificado" quedaban
// generadas en el backend pero invisibles para el usuario.
//
// El panel se renderiza en un portal a `document.body` con
// `position: fixed`, posicionado desde el `getBoundingClientRect()` del
// botón — antes era `position: absolute; right: 0` relativo al botón,
// y como la campana no está pegada al borde derecho real de la
// pantalla (hay más elementos después: avatar, Dashboard, Salir), un
// panel de 340px se salía del viewport en pantallas angostas y se veía
// "cortado". Mismo patrón ya usado en `RoadmapNode.tsx` para el mismo
// tipo de problema.
export default function NotificationBell() {
  const navigate = useNavigate()
  const buttonRef = useRef<HTMLButtonElement>(null)
  const panelRef = useRef<HTMLDivElement>(null)
  const [open, setOpen] = useState(false)
  const [panelPos, setPanelPos] = useState<{ top: number; left: number } | null>(null)
  const [items, setItems] = useState<Notificacion[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const unread = items.filter((n) => !n.leida).length

  useEffect(() => {
    const load = () => {
      setLoading(true)
      listNotifications()
        .then((data) => {
          setItems(data)
          setError("")
        })
        .catch((err) => setError(err instanceof ApiError ? err.message : "No se pudieron cargar las notificaciones."))
        .finally(() => setLoading(false))
    }
    load()
    const interval = setInterval(load, POLL_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [])

  const computePosition = () => {
    const rect = buttonRef.current?.getBoundingClientRect()
    if (!rect) return
    const left = Math.min(rect.right - PANEL_WIDTH, window.innerWidth - PANEL_WIDTH - VIEWPORT_MARGIN)
    setPanelPos({ top: rect.bottom + 8, left: Math.max(VIEWPORT_MARGIN, left) })
  }

  const toggleOpen = () => {
    if (!open) computePosition()
    setOpen((o) => !o)
  }

  useEffect(() => {
    if (!open) return

    const onClickOutside = (e: MouseEvent) => {
      const target = e.target as Node
      if (buttonRef.current?.contains(target) || panelRef.current?.contains(target)) return
      setOpen(false)
    }
    const onReposition = () => computePosition()

    document.addEventListener("mousedown", onClickOutside)
    window.addEventListener("resize", onReposition)
    window.addEventListener("scroll", onReposition, true)
    return () => {
      document.removeEventListener("mousedown", onClickOutside)
      window.removeEventListener("resize", onReposition)
      window.removeEventListener("scroll", onReposition, true)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  const handleClick = async (n: Notificacion) => {
    if (!n.leida) {
      try {
        const updated = await markNotificationRead(n.id)
        setItems((prev) => prev.map((x) => (x.id === updated.id ? updated : x)))
      } catch {
        // No es crítico si falla marcar como leída — se reintentará en el próximo poll.
      }
    }

    const ruta = rutaDeNotificacion(n)
    if (ruta) {
      setOpen(false)
      navigate(ruta)
    }
  }

  return (
    <div className="relative">
      {/* WCAG 4.1.3 — el conteo de no-leídas cambia con cada poll (60s)
          sin que nada lo anuncie; el texto solo cambia de verdad cuando
          `unread` cambia, así que esto no spamea el lector de pantalla
          en cada poll sin novedades. */}
      <span className="sr-only" role="status" aria-live="polite">
        {unread > 0 ? `${unread} notificación${unread === 1 ? "" : "es"} sin leer` : ""}
      </span>

      <button
        ref={buttonRef}
        type="button"
        onClick={toggleOpen}
        aria-label={unread > 0 ? `Notificaciones — ${unread} sin leer` : "Notificaciones"}
        className="chamfer-sm flex items-center justify-center w-8 h-8 cursor-pointer border transition-colors"
        style={{ backgroundColor: open ? "var(--surface-hover)" : "transparent", borderColor: "var(--border-default)", color: "var(--text-muted)" }}
        onMouseEnter={(e) => { if (!open) e.currentTarget.style.color = "var(--text-heading)" }}
        onMouseLeave={(e) => { if (!open) e.currentTarget.style.color = "var(--text-muted)" }}
      >
        <IconBell width={16} height={16} />
      </button>
      {/* Badge fuera del <button> a propósito: el botón tiene su propio
          clip-path (chamfer-sm) — un hijo posicionado afuera de su caja
          (para "flotar" sobre la esquina) queda recortado por ESE
          clip-path, no solo por overflow. Como hermano en este wrapper
          (sin clip-path propio) se ve completo. chamfer-sm en vez de
          rounded-full: es la única badge circular de toda la plataforma,
          el resto (roles, dificultad, estados) usa el mismo chip
          angular — un borde de 2px del color del fondo la "recorta" del
          botón de abajo en vez de superponerse sin transición. */}
      {unread > 0 && (
        <span
          className="absolute -top-1.5 -right-1.5 flex items-center justify-center min-w-[17px] h-[17px] px-1 text-[9px] font-bold chamfer-sm pointer-events-none"
          style={{ backgroundColor: "var(--signal-red)", color: "#1a0505", fontFamily: "var(--font-mono)", border: "2px solid var(--canvas)" }}
        >
          {unread > 9 ? "9+" : unread}
        </span>
      )}

      {open && panelPos &&
        createPortal(
          <div
            ref={panelRef}
            className="chamfer-sm p-3 max-h-[70vh] overflow-y-auto"
            style={{
              position: "fixed",
              top: panelPos.top,
              left: panelPos.left,
              width: `min(${PANEL_WIDTH}px, calc(100vw - ${VIEWPORT_MARGIN * 2}px))`,
              zIndex: 1000,
              backgroundColor: "var(--canvas-raised)",
              border: "1px solid var(--border-default)",
              boxShadow: "0 12px 32px rgba(0,0,0,0.5)",
            }}
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-[10px] font-bold uppercase tracking-widest" style={{ color: "var(--text-heading)", fontFamily: "var(--font-mono)" }}>
                Notificaciones
              </span>
              {unread > 0 && (
                <span className="text-[10px] font-mono" style={{ color: "var(--signal-cyan)" }}>{unread} sin leer</span>
              )}
            </div>

            {error ? (
              <p className="text-xs" style={{ color: "var(--signal-red)" }}>{error}</p>
            ) : loading && items.length === 0 ? (
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>Cargando…</p>
            ) : items.length === 0 ? (
              <p className="text-xs text-center py-4 m-0" style={{ color: "var(--text-muted)" }}>Sin notificaciones todavía.</p>
            ) : (
              <div className="flex flex-col gap-1">
                {items.slice(0, 15).map((n) => {
                  const color = TONE_COLOR[TIPO_TONE[n.tipo] || "neutral"]
                  return (
                    <button
                      key={n.id}
                      type="button"
                      onClick={() => handleClick(n)}
                      className="text-left px-2 py-2 chamfer-sm border-none cursor-pointer transition-colors"
                      style={{ backgroundColor: n.leida ? "transparent" : "rgba(56,214,245,0.06)" }}
                    >
                      <div className="flex items-start gap-2">
                        <span className="w-1.5 h-1.5 rounded-full mt-1.5 shrink-0" style={{ backgroundColor: color }} aria-hidden="true" />
                        <div className="flex-1 min-w-0">
                          <p className="text-xs m-0" style={{ color: n.leida ? "var(--text-muted)" : "var(--text-base)" }}>{n.mensaje}</p>
                          <span className="text-[10px] font-mono" style={{ color: "var(--text-dim)" }}>{relativeTime(n.fecha_creacion)}</span>
                        </div>
                      </div>
                    </button>
                  )
                })}
              </div>
            )}
          </div>,
          document.body,
        )}
    </div>
  )
}
