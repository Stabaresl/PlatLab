import type { ReactNode } from "react"

// Encabezado de sección con icono — reemplaza los <h2> genéricos de los
// dashboards para dar más jerarquía visual.
export default function SectionHeading({
  icon,
  title,
  subtitle,
}: {
  icon: ReactNode
  title: string
  subtitle?: string
}) {
  return (
    <div className="flex items-center gap-3 mb-4 sm:mb-5">
      <div
        className="flex items-center justify-center w-9 h-9 rounded-lg shrink-0"
        style={{ backgroundColor: "var(--bg-surface-hover)", color: "var(--accent-primary)" }}
      >
        {icon}
      </div>
      <div>
        <h2
          className="text-lg sm:text-xl font-semibold m-0"
          style={{ color: "var(--text-heading)", fontFamily: "var(--font-heading)" }}
        >
          {title}
        </h2>
        {subtitle && (
          <p className="text-xs sm:text-sm mt-0.5 m-0" style={{ color: "var(--text-muted)" }}>
            {subtitle}
          </p>
        )}
      </div>
    </div>
  )
}
