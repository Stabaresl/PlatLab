import { useCallback, useEffect, useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import { getRoadmap, enrollRoadmapNode, ApiError, type RoadmapCategoria } from "./api"
import Navbar from "../components/Navbar"
import Footer from "../components/Footer"
import HeroBackground from "../components/HeroBackground"
import TerminalHeader from "../components/TerminalHeader"
import RoadmapLane from "../components/RoadmapLane"
import { Button } from "../components/ui/button"
import { Skeleton } from "../components/ui/skeleton"

// Roadmap público de laboratorios `predeterminado` (creados por un
// admin) — a diferencia de `/laboratorios` (catálogo, incluye
// laboratorios de instructores), acá solo entra contenido curado por la
// plataforma, organizado en pistas con bloqueo real por prerequisitos.
export default function RoadmapPage() {
  const navigate = useNavigate()
  const [categorias, setCategorias] = useState<RoadmapCategoria[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [busyNodoId, setBusyNodoId] = useState<string | null>(null)
  const authed = !!localStorage.getItem("token")
  const role = localStorage.getItem("role")

  const load = () => {
    setLoading(true)
    getRoadmap()
      .then(setCategorias)
      .catch((err) => setError(err instanceof ApiError ? err.message : "No se pudo cargar el roadmap."))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleEnroll = useCallback(async (nodoId: string) => {
    setBusyNodoId(nodoId)
    setError("")
    try {
      const asignacion = await enrollRoadmapNode(nodoId)
      navigate(`/resolver/${asignacion.id}`)
    } catch (err) {
      if (err instanceof ApiError && err.status === 422) {
        setError("Todavía no completaste los laboratorios anteriores de esta pista.")
      } else if (err instanceof ApiError && err.status === 409) {
        setError("Ya tenés una inscripción vigente en ese laboratorio.")
      } else {
        setError(err instanceof ApiError ? err.message : "No se pudo completar la inscripción.")
      }
      setBusyNodoId(null)
    }
  }, [navigate])

  return (
    <div className="relative min-h-screen overflow-hidden" style={{ backgroundColor: "var(--canvas)", color: "var(--text-base)" }}>
      <HeroBackground image="grim" imageOpacity={0.06} overlayOpacity={0.9} texture="matrix" textureOpacity={0.035} />
      <div className="relative z-10 flex flex-col min-h-screen">
        <Navbar />
        <main className="flex-1">
          <div className="mx-auto px-4 sm:px-6 md:px-8 py-8 sm:py-10 md:py-12" style={{ maxWidth: "1200px" }}>
            <TerminalHeader
              title="Roadmap"
              subtitle="Camino curado por el equipo de PlatLAB — completá cada laboratorio para desbloquear el siguiente de su pista."
              prompt="cat /roadmap --tree"
              right={
                role === "administrador" ? (
                  <Button asChild size="sm" variant="outline" className="chamfer-sm font-mono text-xs uppercase tracking-wide">
                    <Link to="/roadmap/admin">Editar roadmap</Link>
                  </Button>
                ) : undefined
              }
            />

            <AnimatePresence>
              {error && (
                <motion.p initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="text-sm mb-6 px-3 py-2 chamfer-sm" style={{ color: "var(--signal-red)", backgroundColor: "rgba(255,71,87,0.08)", border: "1px solid var(--signal-red-dim)" }} role="alert">
                  ▲ {error}
                </motion.p>
              )}
            </AnimatePresence>

            {loading ? (
              <div className="flex flex-col gap-6">
                {Array.from({ length: 2 }).map((_, i) => (
                  <Skeleton key={i} className="chamfer h-40" style={{ backgroundColor: "var(--surface)" }} />
                ))}
              </div>
            ) : categorias.length === 0 ? (
              <div className="chamfer flex flex-col items-center gap-2 p-10 sm:p-16 text-center" style={{ border: "1px dashed var(--border-strong)" }}>
                <p className="text-xs uppercase tracking-widest m-0" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                  [ Todavía no hay pistas en el roadmap ]
                </p>
              </div>
            ) : (
              categorias.map((categoria) => (
                <RoadmapLane
                  key={categoria.id}
                  categoria={categoria}
                  authed={authed}
                  isEstudiante={role === "estudiante"}
                  busyNodoId={busyNodoId}
                  onEnroll={handleEnroll}
                />
              ))
            )}
          </div>
        </main>
        <Footer />
      </div>
    </div>
  )
}
