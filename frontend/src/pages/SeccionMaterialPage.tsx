import { useEffect, useState } from "react"
import { useParams, useSearchParams } from "react-router-dom"
import { getSectionContent, ApiError, type ContenidoSeccion, type PasoGuia } from "./api"
import Navbar from "../components/Navbar"
import { Skeleton } from "../components/ui/skeleton"

const materialContentClasses =
  "text-sm sm:text-base leading-relaxed [&_p]:mb-3 [&_pre]:p-3 [&_pre]:my-3 [&_pre]:overflow-x-auto [&_pre]:font-mono [&_pre]:text-xs [&_code]:font-mono [&_h1]:font-bold [&_h1]:uppercase [&_h1]:mt-5 [&_h1]:mb-2 [&_h2]:font-bold [&_h2]:uppercase [&_h2]:mt-5 [&_h2]:mb-2 [&_h3]:font-bold [&_h3]:mt-4 [&_h3]:mb-2 [&_h4]:font-bold [&_h4]:mt-3 [&_h4]:mb-1.5 [&_a]:underline [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5 [&_blockquote]:pl-4 [&_blockquote]:italic"

function MaterialStyles() {
  return (
    <style>{`.material-content pre { background: var(--surface-sunken); border: 1px solid var(--border-default); color: var(--signal-green); }
      .material-content code { color: var(--signal-amber); }
      .material-content h1, .material-content h2, .material-content h3, .material-content h4 { color: var(--text-heading); font-family: var(--font-mono); }
      .material-content a { color: var(--signal-cyan); }
      .material-content blockquote { border-left: 2px solid var(--signal-amber); color: var(--text-muted); }`}</style>
  )
}

function ContenidoHtml({ html }: { html: string }) {
  return (
    <div className={materialContentClasses} style={{ color: "var(--text-base)" }}>
      <MaterialStyles />
      <div className="material-content" dangerouslySetInnerHTML={{ __html: html }} />
    </div>
  )
}

function PasosGuia({ pasos }: { pasos: PasoGuia[] }) {
  return (
    <div className="flex flex-col gap-4">
      {pasos.map((paso) => (
        <div key={paso.orden} className="chamfer-sm p-3 sm:p-4 flex gap-3" style={{ backgroundColor: "var(--surface-hover)", border: "1px solid var(--border-hairline)" }}>
          <span className="chamfer-sm flex items-center justify-center w-7 h-7 text-xs font-bold shrink-0" style={{ backgroundColor: "rgba(56,214,245,0.12)", color: "var(--signal-cyan)", border: "1px solid var(--border-cyan)", fontFamily: "var(--font-mono)" }}>
            {paso.orden}
          </span>
          <div className="flex-1 min-w-0">
            <h4 className="text-sm sm:text-base font-bold uppercase tracking-wide mb-1.5 mt-0" style={{ color: "var(--text-heading)" }}>{paso.titulo}</h4>
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

// Página de referencia standalone — pensada para abrirse en una pestaña
// aparte (window.open) desde ResolverLaboratorioPage y quedar disponible
// mientras el estudiante trabaja en la práctica, sin competir por el
// mismo espacio de pantalla. `modo` decide si se muestra el material
// teórico o la guía paso a paso de la misma sección.
export default function SeccionMaterialPage() {
  const { assignmentId, seccionId } = useParams<{ assignmentId: string; seccionId: string }>()
  const [searchParams] = useSearchParams()
  const modo = searchParams.get("modo") === "guia" ? "guia" : "teoria"

  const [contenido, setContenido] = useState<ContenidoSeccion | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    if (!assignmentId || !seccionId) return
    setLoading(true)
    getSectionContent(assignmentId, seccionId)
      .then(setContenido)
      .catch((err) => setError(err instanceof ApiError ? err.message : "No se pudo cargar el contenido."))
      .finally(() => setLoading(false))
  }, [assignmentId, seccionId])

  return (
    <div className="min-h-screen" style={{ backgroundColor: "var(--canvas)", color: "var(--text-base)" }}>
      <Navbar />
      <main className="mx-auto px-4 sm:px-6 md:px-8 py-8 sm:py-12" style={{ maxWidth: "780px" }}>
        {loading ? (
          <div className="flex flex-col gap-3">
            <Skeleton className="chamfer h-8 w-2/3" style={{ backgroundColor: "var(--surface)" }} />
            <Skeleton className="chamfer h-40" style={{ backgroundColor: "var(--surface)" }} />
          </div>
        ) : error || !contenido ? (
          <p className="text-sm px-3 py-2 chamfer-sm" style={{ color: "var(--signal-red)", backgroundColor: "rgba(255,71,87,0.08)", border: "1px solid var(--signal-red-dim)" }}>
            ▲ {error || "Contenido no disponible."}
          </p>
        ) : (
          <>
            <span className="text-[10px] uppercase tracking-widest font-bold" style={{ color: modo === "guia" ? "var(--signal-amber)" : "var(--signal-cyan)", fontFamily: "var(--font-mono)" }}>
              {modo === "guia" ? "Guía paso a paso" : "Material teórico"}
            </span>
            <h1 className="text-2xl sm:text-3xl font-black uppercase mt-1 mb-6" style={{ color: "var(--text-heading)" }}>
              {contenido.titulo}
            </h1>
            {modo === "guia" ? (
              contenido.pasos_guia.length > 0 ? (
                <PasosGuia pasos={contenido.pasos_guia} />
              ) : (
                <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                  Esta sección todavía no tiene guía paso a paso cargada.
                </p>
              )
            ) : contenido.contenido_teorico ? (
              <ContenidoHtml html={contenido.contenido_teorico} />
            ) : (
              <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                Esta sección todavía no tiene material teórico cargado.
              </p>
            )}
          </>
        )}
      </main>
    </div>
  )
}
