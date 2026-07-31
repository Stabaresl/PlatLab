import { useState, type FormEvent } from "react"
import { useNavigate, Link } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import { register, login, setTokens, setLocalProfile, ApiError, OAUTH_ENABLED } from "./api"
import OAuthButtons from "./OAuthButtons"
import Navbar from "../components/Navbar"
import ReticleFrame from "../components/ReticleFrame"
import CyberGrid from "../components/CyberGrid"
import StatusDot from "../components/StatusDot"
import MouseGlow, { trackGlow, untrackGlow } from "../components/MouseGlow"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Label } from "../components/ui/label"
import grimBg from "../assets/grim.png"

export default function SignUpPage() {
  const navigate = useNavigate()
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirm, setConfirm] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError("")

    if (password !== confirm) {
      setError("Las contraseñas no coinciden.")
      return
    }
    if (password.length < 8 || !/[A-Z]/.test(password) || !/\d/.test(password)) {
      setError("La contraseña debe tener al menos 8 caracteres, una mayúscula y un número.")
      return
    }

    setLoading(true)
    try {
      const normalizedEmail = email.toLowerCase()
      await register({
        email: normalizedEmail,
        password,
        password_confirm: confirm,
        nombre_completo: name,
      })
      const tokens = await login({ email: normalizedEmail, password })
      setTokens(tokens.access, tokens.refresh)
      localStorage.setItem("role", tokens.rol)
      setLocalProfile({ email: normalizedEmail, nombre_completo: name })
      localStorage.setItem("just_registered", "true")
      navigate("/dashboard")
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo crear la cuenta.")
    } finally {
      setLoading(false)
    }
  }

  const passLenOk = password.length >= 8
  const passUpperOk = /[A-Z]/.test(password)
  const passNumOk = /\d/.test(password)

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
          <div className="absolute inset-0" style={{ backgroundImage: `url(${grimBg})`, backgroundSize: "cover", backgroundPosition: "center", opacity: 0.14 }} />
          <CyberGrid opacity={0.12} />
          <MouseGlow color="255,176,32" size={420} opacity={0.14} />
          <div className="relative z-10 max-w-sm flex flex-col gap-6">
            <StatusDot variant="active" label="Registro de nuevo operador" pulse />
            <h2 className="text-display text-2xl xl:text-3xl font-black uppercase leading-tight" style={{ color: "var(--text-heading)" }}>
              Súmate a la
              <br />
              siguiente misión
            </h2>
            <p className="text-sm leading-relaxed" style={{ color: "var(--text-muted)" }}>
              Un solo laboratorio activo por vez, secciones con flags reales
              y examen final al completar el recorrido.
            </p>
            <ul className="flex flex-col gap-2 font-mono text-xs" style={{ color: "var(--text-dim)" }}>
              <li>[✓] Progreso guardado automáticamente</li>
              <li>[✓] Pistas progresivas ante intentos fallidos</li>
              <li>[✓] Rol Estudiante activado al registrarte</li>
            </ul>
          </div>
        </div>

        {/* ═══ Formulario ═══ */}
        <div className="relative flex flex-col items-center justify-start px-4 sm:px-8 py-8 sm:py-12">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="w-full max-w-sm"
          >
            <ReticleFrame color="var(--signal-amber)" size={14}>
              <div className="chamfer flex flex-col gap-5 p-6 sm:p-8" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
                <div className="flex items-center gap-2">
                  <span className="chamfer-sm flex items-center justify-center w-8 h-8 text-sm font-bold" style={{ backgroundColor: "var(--signal-amber)", color: "#0a0700", fontFamily: "var(--font-mono)" }}>G</span>
                  <div>
                    <h1 className="text-lg font-bold m-0" style={{ color: "var(--text-heading)" }}>Crear cuenta</h1>
                    <p className="text-[11px] m-0" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>gaia@platlab:~$ auth --register</p>
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
                    <Label htmlFor="signup-name" className="text-xs uppercase tracking-wide" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>Nombre</Label>
                    <Input id="signup-name" type="text" placeholder="Tu nombre completo" required value={name} onChange={(e) => setName(e.target.value)} className="chamfer-sm h-10" />
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="signup-email" className="text-xs uppercase tracking-wide" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>Email</Label>
                    <Input id="signup-email" type="email" placeholder="nombre@dominio.com" required value={email} onChange={(e) => setEmail(e.target.value)} className="chamfer-sm h-10" />
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="signup-password" className="text-xs uppercase tracking-wide" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>Contraseña</Label>
                    <Input id="signup-password" type="password" placeholder="············" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} className="chamfer-sm h-10" />
                    {password.length > 0 && (
                      <div className="flex flex-wrap gap-x-3 gap-y-1 mt-1 text-[10px] font-mono">
                        <span style={{ color: passLenOk ? "var(--signal-green)" : "var(--text-dim)" }}>{passLenOk ? "✓" : "○"} 8+ caracteres</span>
                        <span style={{ color: passUpperOk ? "var(--signal-green)" : "var(--text-dim)" }}>{passUpperOk ? "✓" : "○"} 1 mayúscula</span>
                        <span style={{ color: passNumOk ? "var(--signal-green)" : "var(--text-dim)" }}>{passNumOk ? "✓" : "○"} 1 número</span>
                      </div>
                    )}
                  </div>

                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="signup-confirm" className="text-xs uppercase tracking-wide" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>Confirmar contraseña</Label>
                    <Input id="signup-confirm" type="password" placeholder="············" required value={confirm} onChange={(e) => setConfirm(e.target.value)} className="chamfer-sm h-10" />
                  </div>

                  <Button type="submit" disabled={loading} className="chamfer-sm h-10 font-mono text-xs uppercase tracking-wide">
                    {loading ? "Creando cuenta…" : "Crear cuenta"}
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
                  ¿Ya tienes cuenta?{" "}
                  <Link to="/login" className="font-semibold no-underline transition-colors hover:underline" style={{ color: "var(--signal-cyan)" }}>
                    Inicia sesión
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
