import { useState } from "react"
import type { PasoGuia } from "../pages/api"

// Renderizado compartido del contenido de una sección (teoría, tareas,
// resumen de cierre) — lo usan la vista del estudiante
// (ResolverLaboratorioPage) y la vista previa de admin/instructor
// (LabPreviewPage). El HTML ya llega sanitizado por el backend (bleach).

const _ESTILOS = `
.sec-content { color: var(--text-base); font-size: 0.9375rem; line-height: 1.7; }
.sec-content > * + * { margin-top: 0.85rem; }
.sec-content > :first-child { margin-top: 0; }
.sec-content h2, .sec-content h3, .sec-content h4, .sec-content h5 { color: var(--text-heading); font-family: var(--font-body); font-weight: 700; line-height: 1.3; margin-top: 1.6rem; }
.sec-content h2 { font-size: 1.25rem; }
.sec-content h3 { font-size: 1.0625rem; }
.sec-content h4, .sec-content h5 { font-size: 0.9375rem; color: var(--signal-cyan); font-family: var(--font-mono); text-transform: uppercase; letter-spacing: 0.04em; }
.sec-content a { color: var(--signal-cyan); text-decoration: underline; text-underline-offset: 3px; }
.sec-content strong { color: var(--text-heading); font-weight: 600; }
.sec-content ul { list-style: disc; padding-left: 1.25rem; }
.sec-content ol { list-style: decimal; padding-left: 1.25rem; }
.sec-content li + li { margin-top: 0.35rem; }
.sec-content code { font-family: var(--font-mono); font-size: 0.8125rem; color: var(--signal-amber); background: var(--surface-sunken); padding: 0.1rem 0.35rem; border: 1px solid var(--border-hairline); }
.sec-content pre { font-family: var(--font-mono); font-size: 0.8125rem; line-height: 1.55; color: var(--text-base); background: var(--surface-sunken); border: 1px solid var(--border-default); padding: 0.85rem 1rem; overflow-x: auto; white-space: pre; }
.sec-content pre code { background: none; border: 0; padding: 0; color: inherit; }
.sec-content kbd { font-family: var(--font-mono); font-size: 0.75rem; padding: 0.05rem 0.4rem; border: 1px solid var(--border-strong); border-bottom-width: 2px; color: var(--text-heading); background: var(--surface-raised); }
.sec-content blockquote { border-left: 2px solid var(--signal-amber); padding-left: 0.85rem; color: var(--text-muted); }
.sec-content hr { border: 0; border-top: 1px solid var(--border-default); margin: 1.5rem 0; }
.sec-content table { width: 100%; border-collapse: collapse; font-size: 0.875rem; display: block; overflow-x: auto; }
.sec-content th, .sec-content td { text-align: left; padding: 0.45rem 0.7rem; border-bottom: 1px solid var(--border-hairline); vertical-align: top; }
.sec-content th { color: var(--text-heading); font-family: var(--font-mono); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; border-bottom-color: var(--border-strong); }
.sec-content td code { white-space: nowrap; }
.sec-content .nota, .sec-content .aviso, .sec-content .tip, .sec-content .importante, .sec-content .escenario {
  border: 1px solid var(--border-default); border-left-width: 3px; padding: 0.75rem 0.95rem; background: var(--surface-raised);
}
.sec-content .nota { border-left-color: var(--signal-cyan); }
.sec-content .tip { border-left-color: var(--signal-green); }
.sec-content .aviso, .sec-content .importante { border-left-color: var(--signal-amber); }
.sec-content .escenario { border-left-color: var(--text-muted); background: var(--surface); }
.sec-content .nota > :first-child::before { content: "Nota · "; color: var(--signal-cyan); font-family: var(--font-mono); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; }
.sec-content .tip > :first-child::before { content: "Consejo · "; color: var(--signal-green); font-family: var(--font-mono); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; }
.sec-content .aviso > :first-child::before { content: "Atención · "; color: var(--signal-amber); font-family: var(--font-mono); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; }
.sec-content .importante > :first-child::before { content: "Importante · "; color: var(--signal-amber); font-family: var(--font-mono); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; }
.sec-content .escenario > :first-child::before { content: "Escenario · "; color: var(--text-muted); font-family: var(--font-mono); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; }
.sec-content .nota > * + *, .sec-content .tip > * + *, .sec-content .aviso > * + *, .sec-content .importante > * + *, .sec-content .escenario > * + * { margin-top: 0.5rem; }
`

export function ContenidoHtml({ html }: { html: string }) {
  return (
    <>
      <style>{_ESTILOS}</style>
      <div className="sec-content min-w-0" dangerouslySetInnerHTML={{ __html: html }} />
    </>
  )
}

function leerHechos(clave?: string): number[] {
  if (!clave) return []
  try {
    return JSON.parse(localStorage.getItem(clave) || "[]")
  } catch {
    return []
  }
}

export function BloqueComando({ comando, onEjecutar }: { comando: string; onEjecutar?: (comando: string) => void }) {
  const [copiado, setCopiado] = useState(false)
  const copiar = async () => {
    try {
      await navigator.clipboard.writeText(comando)
      setCopiado(true)
      setTimeout(() => setCopiado(false), 1500)
    } catch {
      // Sin permiso de portapapeles (http en red local): el comando queda seleccionable a mano.
    }
  }
  return (
    <div className="chamfer-sm overflow-hidden" style={{ backgroundColor: "var(--surface-sunken)", border: "1px solid var(--border-default)" }}>
      <div className="flex items-start gap-2 px-3 py-2.5">
        <span aria-hidden="true" className="shrink-0 select-none text-[13px]" style={{ color: "var(--signal-green)", fontFamily: "var(--font-mono)" }}>
          $
        </span>
        <code className="flex-1 min-w-0 text-[13px] whitespace-pre-wrap break-all" style={{ color: "var(--text-heading)", fontFamily: "var(--font-mono)" }}>
          {comando}
        </code>
      </div>
      <div className="flex items-center justify-end gap-1.5 px-2 py-1.5" style={{ borderTop: "1px solid var(--border-hairline)" }}>
        <button type="button" onClick={copiar} className="consola-btn" data-estado={copiado ? "ok" : undefined} aria-live="polite">
          {copiado ? "Copiado" : "Copiar"}
        </button>
        {onEjecutar && (
          <button type="button" onClick={() => onEjecutar(comando)} className="consola-btn" title="Lo escribe y ejecuta en la consola de la derecha">
            Ejecutar en consola →
          </button>
        )}
      </div>
    </div>
  )
}

/**
 * Tareas numeradas estilo AWS Workshop: instrucciones, comando con copiar /
 * ejecutar, resultado esperado y una casilla "hecho" que se guarda en el
 * navegador (`progresoKey`), para retomar donde se quedó.
 */
export function PasosGuia({
  pasos,
  onEjecutar,
  progresoKey,
}: {
  pasos: PasoGuia[]
  onEjecutar?: (comando: string) => void
  progresoKey?: string
}) {
  const [hechos, setHechos] = useState<number[]>(() => leerHechos(progresoKey))
  const alternar = (orden: number) => {
    setHechos((prev) => {
      const next = prev.includes(orden) ? prev.filter((n) => n !== orden) : [...prev, orden]
      if (progresoKey) {
        try {
          localStorage.setItem(progresoKey, JSON.stringify(next))
        } catch {
          // almacenamiento no disponible: el check vive solo en esta visita
        }
      }
      return next
    })
  }
  const total = pasos.length
  const listos = pasos.filter((p) => hechos.includes(p.orden)).length

  return (
    <div className="flex flex-col gap-4">
      {progresoKey && total > 0 && (
        <div className="flex items-center gap-3">
          <div className="flex-1 h-1 overflow-hidden" style={{ backgroundColor: "var(--surface-hover)" }} role="progressbar" aria-valuemin={0} aria-valuemax={total} aria-valuenow={listos} aria-label="Tareas marcadas como hechas">
            <div className="h-full transition-transform duration-300" style={{ width: "100%", transformOrigin: "left", transform: `scaleX(${total ? listos / total : 0})`, backgroundColor: "var(--signal-green)" }} />
          </div>
          <span className="text-[11px] shrink-0" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
            {listos} de {total} tareas
          </span>
        </div>
      )}
      <ol className="flex flex-col gap-3 m-0 p-0 list-none">
        {pasos.map((paso) => {
          const hecho = hechos.includes(paso.orden)
          return (
            <li
              key={paso.orden}
              className="chamfer-sm p-4 flex flex-col gap-3"
              style={{ backgroundColor: "var(--surface)", border: `1px solid ${hecho ? "var(--signal-green-dim)" : "var(--border-default)"}` }}
            >
              <div className="flex items-start gap-3">
                <span
                  className="chamfer-sm flex items-center justify-center w-7 h-7 text-xs font-bold shrink-0"
                  style={{
                    backgroundColor: hecho ? "var(--signal-green)" : "color-mix(in srgb, var(--signal-cyan) 12%, transparent)",
                    color: hecho ? "var(--canvas)" : "var(--signal-cyan)",
                    border: `1px solid ${hecho ? "var(--signal-green)" : "var(--border-cyan)"}`,
                    fontFamily: "var(--font-mono)",
                  }}
                  aria-hidden="true"
                >
                  {hecho ? "✓" : paso.orden}
                </span>
                <div className="flex-1 min-w-0">
                  <h4 className="text-[15px] font-semibold m-0 leading-snug" style={{ color: "var(--text-heading)", fontFamily: "var(--font-body)" }}>
                    <span className="sr-only">Tarea {paso.orden}: </span>
                    {paso.titulo}
                  </h4>
                </div>
                {progresoKey && (
                  <label className="flex items-center gap-1.5 text-[11px] cursor-pointer shrink-0 select-none" style={{ color: hecho ? "var(--signal-green)" : "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                    <input type="checkbox" checked={hecho} onChange={() => alternar(paso.orden)} style={{ accentColor: "var(--signal-green)" }} />
                    Hecho
                  </label>
                )}
              </div>
              <ContenidoHtml html={paso.instrucciones} />
              {paso.comando_sugerido && <BloqueComando comando={paso.comando_sugerido} onEjecutar={onEjecutar} />}
              {paso.resultado_esperado && (
                <details className="group" open>
                  <summary className="text-[11px] uppercase tracking-wider cursor-pointer select-none" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                    Resultado esperado
                  </summary>
                  <pre className="mt-2 m-0 p-3 text-xs overflow-x-auto" style={{ backgroundColor: "var(--surface-sunken)", border: "1px dashed var(--border-default)", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                    {paso.resultado_esperado}
                  </pre>
                </details>
              )}
            </li>
          )
        })}
      </ol>
    </div>
  )
}
