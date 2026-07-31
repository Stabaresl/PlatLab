export type ActivityTone = "info" | "success" | "warning" | "neutral"

export interface ActivityItem {
  id: string
  title: string
  description?: string
  timestamp: string
  tone?: ActivityTone
}

export const TONE_COLOR: Record<ActivityTone, string> = {
  info: "var(--signal-cyan)",
  success: "var(--signal-green)",
  warning: "var(--signal-amber)",
  neutral: "var(--text-muted)",
}

export function relativeTime(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diffMs / 60000)
  if (mins < 1) return "ahora"
  if (mins < 60) return `hace ${mins} min`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `hace ${hours} h`
  const days = Math.floor(hours / 24)
  if (days < 30) return `hace ${days} d`
  return new Date(iso).toLocaleDateString()
}

// Timeline vertical con línea conectora + punto de estado — inspirado en
// el patrón "Chrono Board" de 21st.dev, adaptado a nuestros tokens.
// Reutilizado tanto para la actividad/auditoría del admin como (con otro
// origen de datos) para cualquier otro listado cronológico futuro.
export default function ActivityTimeline({
  items,
  emptyLabel = "Sin actividad reciente.",
}: {
  items: ActivityItem[]
  emptyLabel?: string
}) {
  if (items.length === 0) {
    return (
      <div className="chamfer-sm p-6 text-center" style={{ border: "1px dashed var(--border-default)" }}>
        <p className="text-xs uppercase tracking-widest m-0" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
          [ {emptyLabel} ]
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col">
      {items.map((item, i) => {
        const color = TONE_COLOR[item.tone || "neutral"]
        const isLast = i === items.length - 1
        return (
          <div key={item.id} className="relative flex gap-3 pb-4">
            {!isLast && (
              <span
                className="absolute left-[7px] top-4 bottom-0 w-px"
                style={{ backgroundColor: "var(--border-default)" }}
                aria-hidden="true"
              />
            )}
            <span
              className="relative z-10 mt-1 w-3.5 h-3.5 rounded-full shrink-0"
              style={{ backgroundColor: `color-mix(in srgb, ${color} 22%, transparent)`, border: `1.5px solid ${color}` }}
              aria-hidden="true"
            />
            <div className="flex-1 min-w-0 pb-1">
              <div className="flex items-baseline justify-between gap-2 flex-wrap">
                <span className="text-sm font-medium" style={{ color: "var(--text-heading)" }}>{item.title}</span>
                <span className="text-[10px] font-mono shrink-0" style={{ color: "var(--text-dim)" }}>{relativeTime(item.timestamp)}</span>
              </div>
              {item.description && (
                <p className="text-xs mt-0.5 m-0" style={{ color: "var(--text-muted)" }}>{item.description}</p>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
