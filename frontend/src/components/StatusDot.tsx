// Indicador de estado — nunca depende solo del color: siempre trae un
// glifo/label de texto al lado (ok / warn / error / idle) para accesibilidad.
const VARIANTS = {
  online: { color: "var(--signal-green)", glyph: "●", label: "En línea" },
  active: { color: "var(--signal-amber)", glyph: "◆", label: "Activo" },
  danger: { color: "var(--signal-red)", glyph: "▲", label: "Error" },
  idle: { color: "var(--text-muted)", glyph: "○", label: "Inactivo" },
  info: { color: "var(--signal-cyan)", glyph: "◈", label: "Info" },
} as const

export default function StatusDot({
  variant,
  label,
  pulse = false,
  className = "",
}: {
  variant: keyof typeof VARIANTS
  label?: string
  pulse?: boolean
  className?: string
}) {
  const v = VARIANTS[variant]
  return (
    <span
      className={`inline-flex items-center gap-1.5 text-[10px] uppercase tracking-wider ${className}`}
      style={{ fontFamily: "var(--font-mono)", color: v.color }}
    >
      <span
        aria-hidden="true"
        className="inline-block"
        style={{
          fontSize: 8,
          animation: pulse ? "status-blink 1.6s ease-in-out infinite" : undefined,
        }}
      >
        {v.glyph}
      </span>
      {label ?? v.label}
    </span>
  )
}
