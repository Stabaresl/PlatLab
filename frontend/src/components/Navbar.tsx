import { useState, useEffect } from "react"
import { Link, useNavigate, useLocation } from "react-router-dom"
import { motion } from "framer-motion"
import { logout } from "../pages/api"

const ROLE_LABELS: Record<string, string> = {
  estudiante: "Estudiante",
  instructor: "Instructor",
  administrador: "Administrador",
}

// Navbar compartida — GAIA (logo, siempre vuelve a "/"), links contextuales
// según sesión, usada en About/Login/SignUp/Dashboards.
export default function Navbar({ variant = "solid" }: { variant?: "solid" | "transparent" }) {
  const navigate = useNavigate()
  const location = useLocation()
  const [authed, setAuthed] = useState(false)
  const [role, setRole] = useState<string | null>(null)

  useEffect(() => {
    setAuthed(!!localStorage.getItem("token"))
    setRole(localStorage.getItem("role"))
  }, [location.pathname])

  return (
    <motion.header
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="w-full sticky top-0 z-40"
      style={{
        backgroundColor: variant === "solid" ? "rgba(15,17,23,0.85)" : "transparent",
        backdropFilter: variant === "solid" ? "blur(10px)" : "none",
        borderBottom: variant === "solid" ? "1px solid var(--ui-border-default)" : "none",
      }}
    >
      <div
        className="mx-auto flex items-center justify-between px-4 sm:px-6 md:px-8 h-16"
        style={{ maxWidth: "1400px" }}
      >
        <Link
          to="/"
          className="text-xl sm:text-2xl font-semibold no-underline select-none"
          style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}
        >
          GAIA
        </Link>

        <nav className="flex items-center gap-2 sm:gap-3">
          <Link
            to="/laboratorios"
            className="hidden sm:inline text-sm no-underline transition-colors px-2 py-1"
            style={{ color: "var(--text-muted)" }}
            onMouseEnter={(e) => { e.currentTarget.style.color = "var(--text-heading)" }}
            onMouseLeave={(e) => { e.currentTarget.style.color = "var(--text-muted)" }}
          >
            Laboratorios
          </Link>
          <Link
            to="/about"
            className="hidden sm:inline text-sm no-underline transition-colors px-2 py-1"
            style={{ color: "var(--text-muted)" }}
            onMouseEnter={(e) => { e.currentTarget.style.color = "var(--text-heading)" }}
            onMouseLeave={(e) => { e.currentTarget.style.color = "var(--text-muted)" }}
          >
            Sobre GAIA
          </Link>

          {authed ? (
            <>
              {role && (
                <span
                  className="hidden md:inline text-xs font-medium px-2.5 py-1 rounded-full"
                  style={{ backgroundColor: "rgba(59,130,246,0.12)", color: "var(--accent-primary)", border: "1px solid rgba(59,130,246,0.3)" }}
                >
                  {ROLE_LABELS[role] || role}
                </span>
              )}
              <Link
                to="/dashboard"
                className="text-sm font-semibold no-underline px-3 sm:px-4 py-1.5 sm:py-2 rounded transition-opacity hover:opacity-85"
                style={{ backgroundColor: "var(--text-heading)", color: "#0F1117", fontFamily: "'Fira Code', monospace" }}
              >
                Dashboard
              </Link>
              <button
                type="button"
                onClick={logout}
                className="text-xs sm:text-sm font-semibold cursor-pointer border px-3 sm:px-4 py-1.5 sm:py-2 rounded transition-colors"
                style={{ backgroundColor: "transparent", borderColor: "var(--ui-border-default)", color: "var(--text-muted)", fontFamily: "'Fira Code', monospace" }}
                onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--accent-danger)"; e.currentTarget.style.color = "var(--accent-danger)" }}
                onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--ui-border-default)"; e.currentTarget.style.color = "var(--text-muted)" }}
              >
                Salir
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={() => navigate("/login")}
                className="text-xs sm:text-sm font-semibold cursor-pointer border-none bg-transparent px-2 sm:px-3 py-1.5 transition-colors"
                style={{ color: "var(--text-heading)", fontFamily: "'Fira Code', monospace" }}
              >
                Iniciar sesión
              </button>
              <button
                type="button"
                onClick={() => navigate("/signup")}
                className="text-xs sm:text-sm font-semibold cursor-pointer border-none px-3 sm:px-5 py-1.5 sm:py-2 rounded transition-opacity hover:opacity-85"
                style={{ backgroundColor: "var(--text-heading)", color: "#0F1117", fontFamily: "'Fira Code', monospace" }}
              >
                Comenzar
              </button>
            </>
          )}
        </nav>
      </div>
    </motion.header>
  )
}
