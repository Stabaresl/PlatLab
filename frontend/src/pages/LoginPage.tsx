import { useState, type FormEvent } from "react"
import { useNavigate, Link } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import { login, setTokens, setLocalProfile, ApiError, OAUTH_ENABLED } from "./api"
import OAuthButtons from "./OAuthButtons"
import Navbar from "../components/Navbar"
import ReticleFrame from "../components/ReticleFrame"
import MatrixRain from "../components/MatrixRain"
import StatusDot from "../components/StatusDot"
import MouseGlow, { trackGlow, untrackGlow } from "../components/MouseGlow"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Label } from "../components/ui/label"
import termBg from "../assets/term.png"

export default function LoginPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)

    try {
      const data = await login({ email: email.toLowerCase(), password })
      setTokens(data.access, data.refresh)
      localStorage.setItem("role", data.rol)
      setLocalProfile({ email: email.toLowerCase() })
      navigate("/dashboard")
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo iniciar sesión.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative min-h-screen flex flex-col" style={{ backgroundColor: "var(--canvas)" }}>
      <Navbar />

      <main className="relative z-10 flex-1 grid grid-cols-1 lg:grid-cols-2">
        {/* ═══ Panel de marca ═══ */}
        <div
          onMouseMove={trackGlow}
          onMouseLeave={untrackGlow}
          className="relative hidden lg:flex items-center justify-center overflow-hidden p-10"
          style={{ backgroundColor: "var(--canvas-raised)", borderRight: "1px solid var(--border-default)" }}
        >
          <div className="absolute inset-0" style={{ backgroundImage: `url(${termBg})`, backgroundSize: "cover", backgroundPosition: "center", opacity: 0.16 }} />
          <MatrixRain opacity={0.05} />
          <MouseGlow color="56,214,245" size={420} opacity={0.14} />
          <div className="relative z-10 max-w-sm flex flex-col gap-6">
            <StatusDot variant="info" label="Acceso restringido" />
            <h2 className="text-display text-2xl xl:text-3xl font-black uppercase leading-tight" style={{ color: "var(--text-heading)" }}>
              Ingresa de nuevo a tu
              <br />
              consola de operaciones
            </h2>
            <p className="text-sm leading-relaxed" style={{ color: "var(--text-muted)" }}>
              Tu progreso, flags capturadas y laboratorio activo te esperan
              exactamente donde los dejaste.
            </p>
            <div className="flex flex-col gap-2 font-mono text-xs" style={{ color: "var(--text-dim)" }}>
              <span>&gt; verificando credenciales…</span>
              <span>&gt; sesión persistente: <span style={{ color: "var(--signal-green)" }}>habilitada</span></span>
            </div>
          </div>
        </div>

        {/* ═══ Formulario ═══ */}
        <div className="relative flex flex-col items-center justify-start sm:justify-center px-4 sm:px-8 py-8 sm:py-12">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="w-full max-w-sm"
          >
            <ReticleFrame color="var(--signal-amber)" size={14}>
              <div className="chamfer flex flex-col gap-5 sm:gap-6 p-6 sm:p-8" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
                <div className="flex items-center gap-2">
                  <span className="chamfer-sm flex items-center justify-center w-8 h-8 text-sm font-bold" style={{ backgroundColor: "var(--signal-amber)", color: "#0a0700", fontFamily: "var(--font-mono)" }}>G</span>
                  <div>
                    <h1 className="text-lg font-bold m-0" style={{ color: "var(--text-heading)" }}>Iniciar sesión</h1>
                    <p className="text-[11px] m-0" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>gaia@platlab:~$ auth --login</p>
                  </div>
                </div>

                <AnimatePresence>
                  {error && (
                    <motion.p
                      initial={{ opacity: 0, x: -6 }}
                      animate={{ opacity: 1, x: [0, -6, 6, -3, 0] }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.35 }}
                      className="text-sm w-full m-0 px-3 py-2 chamfer-sm"
                      style={{ color: "var(--signal-red)", backgroundColor: "rgba(255,71,87,0.08)", border: "1px solid var(--signal-red-dim)" }}
                      role="alert"
                    >
                      ▲ {error}
                    </motion.p>
                  )}
                </AnimatePresence>

                <form onSubmit={handleSubmit} className="w-full flex flex-col gap-4">
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="login-email" className="text-xs uppercase tracking-wide" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>Email</Label>
                    <Input
                      id="login-email"
                      type="email"
                      placeholder="nombre@dominio.com"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="chamfer-sm h-10"
                    />
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="login-password" className="text-xs uppercase tracking-wide" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>Contraseña</Label>
                    <Input
                      id="login-password"
                      type="password"
                      placeholder="············"
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="chamfer-sm h-10"
                    />
                  </div>

                  <Button type="submit" disabled={loading} className="chamfer-sm h-10 font-mono text-xs uppercase tracking-wide">
                    {loading ? "Verificando…" : "Iniciar sesión"}
                  </Button>
                </form>

                {OAUTH_ENABLED && (
                  <>
                    <div className="w-full flex items-center gap-3 text-[10px] uppercase tracking-wider" style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
                      <div className="flex-1 h-px" style={{ backgroundColor: "var(--border-default)" }} />
                      <span>o continuar con</span>
                      <div className="flex-1 h-px" style={{ backgroundColor: "var(--border-default)" }} />
                    </div>
                    <OAuthButtons />
                  </>
                )}

                <p className="text-sm m-0 text-center" style={{ color: "var(--text-muted)" }}>
                  ¿No tienes cuenta?{" "}
                  <Link to="/signup" className="font-semibold no-underline transition-colors hover:underline" style={{ color: "var(--signal-cyan)" }}>
                    Regístrate
                  </Link>
                </p>
              </div>
            </ReticleFrame>
          </motion.div>
        </div>
      </main>
    </div>
  )
}
