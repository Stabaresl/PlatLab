import { useState, useEffect } from "react"
import { Link, useNavigate, useLocation } from "react-router-dom"
import { motion } from "framer-motion"
import { logout } from "../pages/api"
import { useGamificationStore } from "../store/gamificationStore"
import { Button } from "./ui/button"
import StatusDot from "./StatusDot"
import NotificationBell from "./NotificationBell"
import AvatarBadge from "./AvatarBadge"

const ROLE_LABELS: Record<string, string> = {
  estudiante: "Estudiante",
  instructor: "Instructor",
  administrador: "Administrador",
}

// Barra de navegación compartida — logo con marca de sistema ("GA::IA"),
// enlaces contextuales según sesión y pill de rol. Siempre vuelve a "/".
export default function Navbar({ variant = "solid" }: { variant?: "solid" | "transparent" }) {
  const navigate = useNavigate()
  const location = useLocation()
  const [authed, setAuthed] = useState(false)
  const [role, setRole] = useState<string | null>(null)
  const { perfil, load: loadPerfil } = useGamificationStore()

  useEffect(() => {
    setAuthed(!!localStorage.getItem("token"))
    setRole(localStorage.getItem("role"))
  }, [location.pathname])

  useEffect(() => {
    if (authed && role === "estudiante" && !perfil) loadPerfil()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authed, role])

  return (
    <motion.header
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="w-full sticky top-0 z-40"
      style={{
        backgroundColor: variant === "solid" ? "rgba(8,9,12,0.88)" : "transparent",
        backdropFilter: variant === "solid" ? "blur(10px)" : "none",
        borderBottom: variant === "solid" ? "1px solid var(--border-default)" : "1px solid transparent",
      }}
    >
      <div className="mx-auto flex items-center justify-between px-4 sm:px-6 md:px-8 h-16" style={{ maxWidth: "1400px" }}>
        <Link to="/" className="flex items-center gap-2 no-underline select-none group">
          <span
            className="chamfer-sm flex items-center justify-center w-8 h-8 text-sm font-bold shrink-0"
            style={{ backgroundColor: "var(--signal-amber)", color: "#0a0700", fontFamily: "var(--font-mono)" }}
          >
            G
          </span>
          <span
            className="text-lg sm:text-xl font-bold tracking-wide"
            style={{ color: "var(--text-heading)", fontFamily: "var(--font-mono)" }}
          >
            GA<span style={{ color: "var(--signal-amber)" }}>::</span>IA
          </span>
        </Link>

        <nav className="flex items-center gap-2 sm:gap-3">
          <Link
            to="/laboratorios"
            className="hidden sm:inline text-xs uppercase tracking-wide no-underline transition-colors px-2 py-1"
            style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
            onMouseEnter={(e) => { e.currentTarget.style.color = "var(--text-heading)" }}
            onMouseLeave={(e) => { e.currentTarget.style.color = "var(--text-muted)" }}
          >
            Laboratorios
          </Link>
          <Link
            to="/roadmap"
            className="hidden sm:inline text-xs uppercase tracking-wide no-underline transition-colors px-2 py-1"
            style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
            onMouseEnter={(e) => { e.currentTarget.style.color = "var(--text-heading)" }}
            onMouseLeave={(e) => { e.currentTarget.style.color = "var(--text-muted)" }}
          >
            Roadmap
          </Link>
          <Link
            to="/about"
            className="hidden sm:inline text-xs uppercase tracking-wide no-underline transition-colors px-2 py-1"
            style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
            onMouseEnter={(e) => { e.currentTarget.style.color = "var(--text-heading)" }}
            onMouseLeave={(e) => { e.currentTarget.style.color = "var(--text-muted)" }}
          >
            Sobre GAIA
          </Link>

          {authed ? (
            <>
              {role && (
                <span
                  className="hidden md:inline-flex items-center gap-1.5 text-[10px] uppercase tracking-wider px-2.5 py-1"
                  style={{ backgroundColor: "rgba(56,214,245,0.08)", border: "1px solid var(--border-cyan)", color: "var(--signal-cyan)", fontFamily: "var(--font-mono)" }}
                >
                  <StatusDot variant="online" label={ROLE_LABELS[role] || role} />
                </span>
              )}
              <NotificationBell />
              {role === "estudiante" && (
                <Link to="/profile" aria-label="Mi perfil" className="flex items-center">
                  <AvatarBadge perfil={perfil} size="sm" />
                </Link>
              )}
              <Button asChild size="sm" className="chamfer-sm font-mono text-xs uppercase tracking-wide">
                <Link to="/dashboard">Dashboard</Link>
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={logout}
                className="chamfer-sm font-mono text-xs uppercase tracking-wide hover:text-[var(--signal-red)] hover:border-[var(--signal-red)]"
              >
                Salir
              </Button>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={() => navigate("/login")}
                className="text-xs uppercase tracking-wide font-semibold cursor-pointer border-none bg-transparent px-2 sm:px-3 py-1.5 transition-colors"
                style={{ color: "var(--text-heading)", fontFamily: "var(--font-mono)" }}
              >
                Iniciar sesión
              </button>
              <Button size="sm" onClick={() => navigate("/signup")} className="chamfer-sm font-mono text-xs uppercase tracking-wide">
                Comenzar
              </Button>
            </>
          )}
        </nav>
      </div>
    </motion.header>
  )
}
