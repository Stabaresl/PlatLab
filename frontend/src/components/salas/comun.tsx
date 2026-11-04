import type { EstadoSala } from "../../pages/api"

const _ESTADO: Record<EstadoSala, { label: string; color: string }> = {
  abierta: { label: "Abierta", color: "var(--signal-green)" },
  cerrada: { label: "Sin ingresos", color: "var(--signal-amber)" },
  finalizada: { label: "Finalizada", color: "var(--text-muted)" },
}

export function EstadoSalaChip({ estado }: { estado: EstadoSala }) {
  const { label, color } = _ESTADO[estado]
  return (
    <span
      className="chamfer-sm inline-flex items-center text-[10px] font-bold px-2 py-0.5 uppercase tracking-wider"
      style={{ color, border: `1px solid color-mix(in srgb, ${color} 50%, transparent)`, backgroundColor: `color-mix(in srgb, ${color} 10%, transparent)`, fontFamily: "var(--font-mono)" }}
    >
      {label}
    </span>
  )
}
