import type { ReactNode } from "react"

export default function SectionHeading({
  icon,
  title,
  subtitle,
  right,
}: {
  icon: ReactNode
  title: string
  subtitle?: string
  right?: ReactNode
}) {
  return (
    <div className="flex items-center justify-between gap-3 mb-4 sm:mb-5 flex-wrap">
      <div className="flex items-center gap-3">
        <div
          className="chamfer-sm flex items-center justify-center w-9 h-9 shrink-0"
          style={{ backgroundColor: "var(--surface-hover)", color: "var(--signal-cyan)", border: "1px solid var(--border-default)" }}
        >
          {icon}
        </div>
        <div>
          <h2 className="text-base sm:text-lg font-bold uppercase tracking-wide m-0" style={{ color: "var(--text-heading)" }}>
            {title}
          </h2>
          {subtitle && (
            <p className="text-xs sm:text-sm mt-0.5 m-0" style={{ color: "var(--text-muted)" }}>
              {subtitle}
            </p>
          )}
        </div>
      </div>
      {right}
    </div>
  )
}
