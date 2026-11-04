import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"
import { getSectionContent, ApiError, type ContenidoSeccion } from "./api"
import Navbar from "../components/Navbar"
import { ContenidoHtml, PasosGuia } from "../components/ContenidoSeccion"
import { Skeleton } from "../components/ui/skeleton"

// Guía de una sección en una pestaña aparte (window.open desde
// ResolverLaboratorioPage), para tenerla al lado de la consola o en otra
// pantalla. Muestra el contexto y las tareas con las mismas casillas "Hecho"
// (comparten la clave de localStorage con la vista principal).
export default function SeccionMaterialPage() {
  const { assignmentId, seccionId } = useParams<{ assignmentId: string; seccionId: string }>()

  const [contenido, setContenido] = useState<ContenidoSeccion | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    if (!assignmentId || !seccionId) return
    getSectionContent(assignmentId, seccionId)
      .then(setContenido)
      .catch((err) => setError(err instanceof ApiError ? err.message : "No se pudo cargar el contenido."))
      .finally(() => setLoading(false))
  }, [assignmentId, seccionId])

  return (
    <div className="min-h-screen" style={{ backgroundColor: "var(--canvas)", color: "var(--text-base)" }}>
      <Navbar />
      <main className="mx-auto px-4 sm:px-6 md:px-8 py-8 sm:py-12" style={{ maxWidth: "820px" }}>
        {loading ? (
          <div className="flex flex-col gap-3">
            <Skeleton className="chamfer h-8 w-2/3" style={{ backgroundColor: "var(--surface)" }} />
            <Skeleton className="chamfer h-40" style={{ backgroundColor: "var(--surface)" }} />
          </div>
        ) : error || !contenido ? (
          <p className="text-sm px-3 py-2 chamfer-sm" style={{ color: "var(--signal-red)", backgroundColor: "color-mix(in srgb, var(--signal-red) 8%, transparent)", border: "1px solid var(--signal-red-dim)" }}>
            ▲ {error || "Contenido no disponible."}
          </p>
        ) : (
          <article className="flex flex-col gap-6">
            <header>
              <span className="text-[11px] uppercase tracking-wider" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                Guía de la sección · {contenido.duracion_estimada_minutos} min
              </span>
              <h1 className="text-2xl sm:text-3xl font-bold mt-1 mb-0" style={{ color: "var(--text-heading)", overflowWrap: "anywhere" }}>
                {contenido.titulo}
              </h1>
            </header>
            {contenido.objetivos.length > 0 && (
              <ul className="m-0 p-4 list-none flex flex-col gap-1.5 chamfer-sm" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
                {contenido.objetivos.map((o, i) => (
                  <li key={i} className="flex gap-2 text-sm">
                    <span aria-hidden="true" style={{ color: "var(--signal-cyan)" }}>▸</span>
                    {o}
                  </li>
                ))}
              </ul>
            )}
            {contenido.contenido_teorico && <ContenidoHtml html={contenido.contenido_teorico} />}
            {contenido.pasos_guia.length > 0 && (
              <section>
                <h2 className="text-sm font-bold uppercase tracking-wider m-0 mb-3" style={{ color: "var(--text-heading)", fontFamily: "var(--font-mono)" }}>Tareas</h2>
                <PasosGuia pasos={contenido.pasos_guia} progresoKey={`platlab:tareas:${assignmentId}:${seccionId}`} />
              </section>
            )}
          </article>
        )}
      </main>
    </div>
  )
}
