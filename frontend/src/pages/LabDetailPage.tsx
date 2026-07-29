import { useEffect, useState } from "react"
import { Link, useParams, useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import { getLaboratorio, getToc, ApiError, type LaboratorioDetalle, type NivelDificultad } from "./api"
import Navbar from "../components/Navbar"
import Footer from "../components/Footer"
import { IconFlask, IconExam, IconLock } from "../components/icons"

const DIFICULTAD_LABEL: Record<NivelDificultad, string> = {
  basico: "Básico",
  intermedio: "Intermedio",
  avanzado: "Avanzado",
}
const DIFICULTAD_COLOR: Record<NivelDificultad, string> = {
  basico: "#22C55E",
  intermedio: "#F59E0B",
  avanzado: "#EF4444",
}

interface TocSeccion {
  orden: number
  titulo: string
  tiene_practica: boolean
}

// Detalle público de un laboratorio (HV-03): tabla de contenidos visible sin
// invitación previa, para que cualquiera entienda el "roadmap" del lab antes
// de pedir/recibir acceso. La inscripción real sigue siendo por invitación
// del instructor (no hay endpoint de auto-inscripción en el backend).
export default function LabDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [lab, setLab] = useState<LaboratorioDetalle | null>(null)
  const [toc, setToc] = useState<TocSeccion[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const authed = !!localStorage.getItem("token")

  useEffect(() => {
    if (!id) return
    setLoading(true)
    Promise.all([getLaboratorio(id), getToc(id)])
      .then(([detalle, tocRes]) => {
        setLab(detalle)
        setToc(tocRes.secciones)
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "No se pudo cargar el laboratorio."))
      .finally(() => setLoading(false))
  }, [id])

  return (
    <div className="min-h-screen flex flex-col" style={{ backgroundColor: "var(--bg-canvas)", color: "var(--text-base)" }}>
      <Navbar />
      <main className="flex-1">
        <div className="mx-auto px-4 sm:px-6 md:px-8 py-8 sm:py-10 md:py-12" style={{ maxWidth: "880px" }}>
          <button
            type="button"
            onClick={() => navigate("/laboratorios")}
            className="text-xs sm:text-sm mb-6 cursor-pointer border-none bg-transparent px-0"
            style={{ color: "var(--text-muted)", fontFamily: "'Fira Code', monospace" }}
          >
            ← Volver al catálogo
          </button>

          {loading ? (
            <div className="flex flex-col gap-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <motion.div
                  key={i}
                  animate={{ opacity: [0.4, 0.8, 0.4] }}
                  transition={{ duration: 1.4, repeat: Infinity, delay: i * 0.08 }}
                  className="h-14 rounded-lg"
                  style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--ui-border-default)" }}
                />
              ))}
            </div>
          ) : error || !lab ? (
            <p className="text-sm" style={{ color: "var(--accent-danger)" }}>
              {error || "Laboratorio no encontrado."}
            </p>
          ) : (
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
              <div className="flex items-center gap-2 mb-3">
                <span
                  className="text-xs font-medium px-2.5 py-1 rounded-full"
                  style={{
                    backgroundColor: `${DIFICULTAD_COLOR[lab.nivel_dificultad]}18`,
                    color: DIFICULTAD_COLOR[lab.nivel_dificultad],
                    border: `1px solid ${DIFICULTAD_COLOR[lab.nivel_dificultad]}40`,
                  }}
                >
                  {DIFICULTAD_LABEL[lab.nivel_dificultad]}
                </span>
                <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                  {lab.total_secciones} sección{lab.total_secciones === 1 ? "" : "es"}
                </span>
              </div>

              <h1 className="text-2xl sm:text-3xl font-semibold mb-3" style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}>
                {lab.nombre}
              </h1>
              <p className="text-sm sm:text-base leading-relaxed mb-5" style={{ color: "var(--text-muted)" }}>
                {lab.descripcion}
              </p>

              {lab.temas.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-8">
                  {lab.temas.map((t) => (
                    <span key={t} className="text-xs px-2.5 py-1 rounded-full" style={{ backgroundColor: "var(--bg-surface-hover)", color: "var(--text-muted)" }}>
                      {t}
                    </span>
                  ))}
                </div>
              )}

              <h2 className="flex items-center gap-2 text-base sm:text-lg font-semibold mb-4" style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}>
                <IconFlask /> Contenido del laboratorio
              </h2>
              <div className="flex flex-col gap-2 mb-8">
                {toc.map((s) => (
                  <div
                    key={s.orden}
                    className="flex items-center gap-3 p-3 sm:p-4 rounded-lg"
                    style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--ui-border-default)" }}
                  >
                    <span
                      className="flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold shrink-0"
                      style={{ backgroundColor: "var(--bg-surface-hover)", color: "var(--ui-border-gold)", fontFamily: "'Fira Code', monospace" }}
                    >
                      {s.orden}
                    </span>
                    <span className="flex-1 text-sm font-medium" style={{ color: "var(--text-base)" }}>
                      {s.titulo}
                    </span>
                    {s.tiene_practica && (
                      <span className="text-[10px] font-medium px-2 py-0.5 rounded-full whitespace-nowrap" style={{ backgroundColor: "rgba(59,130,246,0.12)", color: "var(--accent-primary)" }}>
                        práctica
                      </span>
                    )}
                  </div>
                ))}
                <div
                  className="flex items-center gap-3 p-3 sm:p-4 rounded-lg"
                  style={{ backgroundColor: "var(--bg-surface)", border: "1px dashed var(--ui-border-default)" }}
                >
                  <span
                    className="flex items-center justify-center w-7 h-7 rounded-full shrink-0"
                    style={{ backgroundColor: "var(--bg-surface-hover)", color: "var(--text-muted)" }}
                  >
                    <IconExam width={14} height={14} />
                  </span>
                  <span className="flex-1 text-sm font-medium" style={{ color: "var(--text-muted)" }}>
                    Examen final (se habilita al completar todas las secciones)
                  </span>
                </div>
              </div>

              <div
                className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 sm:p-6 rounded-lg"
                style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--ui-border-gold)" }}
              >
                <div className="flex items-start gap-3">
                  <IconLock style={{ color: "var(--ui-border-gold)" }} className="mt-0.5 shrink-0" />
                  <p className="text-xs sm:text-sm m-0 leading-relaxed" style={{ color: "var(--text-muted)" }}>
                    {authed
                      ? "El acceso a resolver este laboratorio depende de una invitación de tu instructor. Si ya te la enviaron, la vas a ver en tu Dashboard."
                      : "Para inscribirte necesitás una cuenta e invitación de un instructor. Iniciá sesión o creá tu cuenta para empezar."}
                  </p>
                </div>
                {authed ? (
                  <Link
                    to="/dashboard"
                    className="shrink-0 px-5 py-2.5 rounded text-sm font-semibold no-underline transition-opacity hover:opacity-85"
                    style={{ backgroundColor: "var(--text-heading)", color: "#0F1117", fontFamily: "'Fira Code', monospace" }}
                  >
                    Ir a mi Dashboard
                  </Link>
                ) : (
                  <Link
                    to="/signup"
                    className="shrink-0 px-5 py-2.5 rounded text-sm font-semibold no-underline transition-opacity hover:opacity-85"
                    style={{ backgroundColor: "var(--text-heading)", color: "#0F1117", fontFamily: "'Fira Code', monospace" }}
                  >
                    Crear cuenta gratis
                  </Link>
                )}
              </div>
            </motion.div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  )
}
