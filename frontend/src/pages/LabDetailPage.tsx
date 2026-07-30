import { useEffect, useState } from "react"
import { Link, useParams, useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import { getLaboratorio, getToc, enrollLaboratorio, ApiError, type LaboratorioDetalle, type NivelDificultad } from "./api"
import Navbar from "../components/Navbar"
import Footer from "../components/Footer"
import MatrixRain from "../components/MatrixRain"
import HeroBackground from "../components/HeroBackground"
import ReticleFrame from "../components/ReticleFrame"
import MouseGlow, { trackGlow, untrackGlow } from "../components/MouseGlow"
import { IconFlask, IconExam, IconLock } from "../components/icons"
import { Button } from "../components/ui/button"
import { Skeleton } from "../components/ui/skeleton"

const DIFICULTAD_LABEL: Record<NivelDificultad, string> = {
  basico: "Básico",
  intermedio: "Intermedio",
  avanzado: "Avanzado",
}
const DIFICULTAD_COLOR: Record<NivelDificultad, string> = {
  basico: "var(--signal-green)",
  intermedio: "var(--signal-amber)",
  avanzado: "var(--signal-red)",
}

interface TocSeccion {
  orden: number
  titulo: string
  tiene_practica: boolean
}

export default function LabDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [lab, setLab] = useState<LaboratorioDetalle | null>(null)
  const [toc, setToc] = useState<TocSeccion[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [enrolling, setEnrolling] = useState(false)
  const [enrollError, setEnrollError] = useState("")
  const authed = !!localStorage.getItem("token")
  const role = localStorage.getItem("role")

  const handleEnroll = async () => {
    if (!lab) return
    setEnrolling(true)
    setEnrollError("")
    try {
      const asignacion = await enrollLaboratorio(lab.id)
      navigate(`/resolver/${asignacion.id}`)
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setEnrollError("Ya estás inscrito en este laboratorio. Revisa tu Dashboard para continuarlo.")
      } else if (err instanceof ApiError) {
        setEnrollError(err.message)
      } else {
        setEnrollError("No se pudo completar la inscripción.")
      }
      setEnrolling(false)
    }
  }

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
    <div className="relative min-h-screen overflow-hidden" style={{ backgroundColor: "var(--canvas)", color: "var(--text-base)" }}>
      <HeroBackground image="grim" imageOpacity={0.08} overlayOpacity={0.88} texture="matrix" textureOpacity={0.035} />
      <div className="relative z-10 flex flex-col min-h-screen">
        <Navbar />
        <main className="flex-1">
          <div className="mx-auto px-4 sm:px-6 md:px-8 py-8 sm:py-10 md:py-12" style={{ maxWidth: "880px" }}>
            <button
              type="button"
              onClick={() => navigate("/laboratorios")}
              className="text-xs sm:text-sm mb-6 cursor-pointer border-none bg-transparent px-0 uppercase tracking-wide"
              style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
            >
              ← Volver al catálogo
            </button>

            {loading ? (
              <div className="flex flex-col gap-3">
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="chamfer h-14" style={{ backgroundColor: "var(--surface)" }} />
                ))}
              </div>
            ) : error || !lab ? (
              <p className="text-sm px-3 py-2 chamfer-sm" style={{ color: "var(--signal-red)", backgroundColor: "rgba(255,71,87,0.08)", border: "1px solid var(--signal-red-dim)" }}>
                ▲ {error || "Laboratorio no encontrado."}
              </p>
            ) : (
              <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
                <div className="flex items-center gap-2 mb-3">
                  <span
                    className="text-[10px] font-bold px-2.5 py-1 chamfer-sm uppercase tracking-wide"
                    style={{
                      backgroundColor: "color-mix(in srgb, " + DIFICULTAD_COLOR[lab.nivel_dificultad] + " 14%, transparent)",
                      color: DIFICULTAD_COLOR[lab.nivel_dificultad],
                      border: `1px solid ${DIFICULTAD_COLOR[lab.nivel_dificultad]}`,
                    }}
                  >
                    {DIFICULTAD_LABEL[lab.nivel_dificultad]}
                  </span>
                  <span className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>
                    {lab.total_secciones} sección{lab.total_secciones === 1 ? "" : "es"}
                  </span>
                </div>

                <h1 className="text-2xl sm:text-3xl font-black uppercase mb-3" style={{ color: "var(--text-heading)" }}>
                  {lab.nombre}
                </h1>
                <p className="text-sm sm:text-base leading-relaxed mb-5" style={{ color: "var(--text-muted)" }}>
                  {lab.descripcion}
                </p>

                {lab.temas.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-8">
                    {lab.temas.map((t) => (
                      <span key={t} className="text-xs px-2.5 py-1" style={{ backgroundColor: "var(--surface-hover)", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                        {t}
                      </span>
                    ))}
                  </div>
                )}

                <h2 className="flex items-center gap-2 text-sm sm:text-base font-bold uppercase tracking-wide mb-4" style={{ color: "var(--text-heading)" }}>
                  <IconFlask style={{ color: "var(--signal-cyan)" }} /> Contenido del laboratorio
                </h2>
                <div className="flex flex-col gap-2 mb-8">
                  {toc.map((s) => (
                    <div key={s.orden} className="chamfer flex items-center gap-3 p-3 sm:p-4" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
                      <span
                        className="chamfer-sm flex items-center justify-center w-7 h-7 text-xs font-bold shrink-0"
                        style={{ backgroundColor: "var(--surface-hover)", color: "var(--signal-amber)", fontFamily: "var(--font-mono)" }}
                      >
                        {s.orden}
                      </span>
                      <span className="flex-1 text-sm font-medium" style={{ color: "var(--text-base)" }}>
                        {s.titulo}
                      </span>
                      {s.tiene_practica && (
                        <span className="text-[10px] font-bold px-2 py-0.5 whitespace-nowrap uppercase tracking-wide" style={{ backgroundColor: "rgba(56,214,245,0.1)", color: "var(--signal-cyan)", border: "1px solid var(--border-cyan)" }}>
                          práctica
                        </span>
                      )}
                    </div>
                  ))}
                  <div className="chamfer flex items-center gap-3 p-3 sm:p-4" style={{ backgroundColor: "var(--surface)", border: "1px dashed var(--border-strong)" }}>
                    <span className="chamfer-sm flex items-center justify-center w-7 h-7 shrink-0" style={{ backgroundColor: "var(--surface-hover)", color: "var(--text-muted)" }}>
                      <IconExam width={14} height={14} />
                    </span>
                    <span className="flex-1 text-sm font-medium" style={{ color: "var(--text-muted)" }}>
                      Examen final (se habilita al completar todas las secciones)
                    </span>
                  </div>
                </div>

                <ReticleFrame color="var(--signal-amber)" size={14}>
                  <div
                    onMouseMove={trackGlow}
                    onMouseLeave={untrackGlow}
                    className="relative overflow-hidden chamfer flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-5 sm:p-6"
                    style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}
                  >
                    <MatrixRain opacity={0.05} />
                    <MouseGlow color="255,176,32" size={340} opacity={0.14} />
                    <div className="relative z-10 flex items-start gap-3">
                      <IconLock style={{ color: "var(--signal-amber)" }} className="mt-0.5 shrink-0" />
                      <p className="text-xs sm:text-sm m-0 leading-relaxed" style={{ color: "var(--text-muted)" }}>
                        {authed
                          ? role === "estudiante"
                            ? enrollError || "Inscríbete para empezar a resolver este laboratorio ahora mismo. Solo puedes tener un laboratorio activo a la vez."
                            : "Este laboratorio está disponible en el catálogo. Consulta tu Dashboard para gestionar tus laboratorios."
                          : "Crea tu cuenta gratis para inscribirte y empezar a resolver este laboratorio ahora mismo."}
                      </p>
                    </div>
                    {authed ? (
                      role === "estudiante" ? (
                        <Button onClick={handleEnroll} disabled={enrolling} className="relative z-10 shrink-0 chamfer-sm font-mono text-xs uppercase tracking-wide">
                          {enrolling ? "Inscribiendo…" : "Inscribirme ahora"}
                        </Button>
                      ) : (
                        <Button asChild className="relative z-10 shrink-0 chamfer-sm font-mono text-xs uppercase tracking-wide">
                          <Link to="/dashboard">Ir a mi Dashboard</Link>
                        </Button>
                      )
                    ) : (
                      <Button asChild className="relative z-10 shrink-0 chamfer-sm font-mono text-xs uppercase tracking-wide">
                        <Link to="/signup">Crear cuenta gratis</Link>
                      </Button>
                    )}
                  </div>
                </ReticleFrame>
              </motion.div>
            )}
          </div>
        </main>
        <Footer />
      </div>
    </div>
  )
}
