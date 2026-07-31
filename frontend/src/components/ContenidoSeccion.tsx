import type { PasoGuia } from "../pages/api"

// Renderizado compartido de contenido HTML sanitizado (teoría, pasos de
// guía, resumen de cierre) — usado tanto en la vista de resolución del
// estudiante (ResolverLaboratorioPage) como en la vista previa de
// admin/instructor (LabPreviewPage), para no duplicar el markup/estilos.
export function ContenidoHtml({ html }: { html: string }) {
  return (
    <div
      className="text-sm leading-relaxed [&_p]:mb-3 [&_pre]:p-3 [&_pre]:my-3 [&_pre]:overflow-x-auto [&_pre]:font-mono [&_pre]:text-xs [&_code]:font-mono [&_code]:text-[13px] [&_h1]:font-bold [&_h1]:uppercase [&_h1]:mt-4 [&_h1]:mb-2 [&_h2]:font-bold [&_h2]:uppercase [&_h2]:mt-4 [&_h2]:mb-2 [&_h3]:font-bold [&_h3]:mt-3 [&_h3]:mb-1.5 [&_h4]:font-bold [&_h4]:mt-3 [&_h4]:mb-1 [&_a]:underline [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5 [&_blockquote]:pl-3 [&_blockquote]:italic"
      style={{ color: "var(--text-base)" }}
    >
      <style>{`.sec-content pre { background: var(--surface-sunken); border: 1px solid var(--border-default); color: var(--signal-green); }
        .sec-content code { color: var(--signal-amber); }
        .sec-content h1, .sec-content h2, .sec-content h3, .sec-content h4 { color: var(--text-heading); font-family: var(--font-mono); }
        .sec-content a { color: var(--signal-cyan); }
        .sec-content blockquote { border-left: 2px solid var(--signal-amber); color: var(--text-muted); }`}</style>
      <div className="sec-content" dangerouslySetInnerHTML={{ __html: html }} />
    </div>
  )
}

export function PasosGuia({ pasos }: { pasos: PasoGuia[] }) {
  return (
    <div className="flex flex-col gap-3">
      {pasos.map((paso) => (
        <div key={paso.orden} className="chamfer-sm p-3 flex gap-3" style={{ backgroundColor: "var(--surface-hover)", border: "1px solid var(--border-hairline)" }}>
          <span className="chamfer-sm flex items-center justify-center w-7 h-7 text-xs font-bold shrink-0" style={{ backgroundColor: "rgba(56,214,245,0.12)", color: "var(--signal-cyan)", border: "1px solid var(--border-cyan)", fontFamily: "var(--font-mono)" }}>
            {paso.orden}
          </span>
          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-bold uppercase tracking-wide mb-1.5 mt-0" style={{ color: "var(--text-heading)" }}>{paso.titulo}</h4>
            <ContenidoHtml html={paso.instrucciones} />
            {paso.comando_sugerido && (
              <pre className="mt-2 p-2.5 text-xs font-mono overflow-x-auto chamfer-sm whitespace-pre-wrap" style={{ backgroundColor: "var(--surface-sunken)", border: "1px solid var(--border-default)", color: "var(--signal-green)" }}>
                {paso.comando_sugerido}
              </pre>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
