import { useState, type FormEvent } from "react"
import { useNavigate, Link } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import { register, login, setTokens, setLocalProfile, ApiError, OAUTH_ENABLED } from "./api"
import OAuthButtons from "./OAuthButtons"
import Navbar from "../components/Navbar"
import HeroBackground from "../components/HeroBackground"

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
      // El registro no devuelve tokens (solo confirma la cuenta creada) —
      // se inicia sesión inmediatamente después con las mismas credenciales.
      const tokens = await login({ email: normalizedEmail, password })
      setTokens(tokens.access, tokens.refresh)
      localStorage.setItem("role", tokens.rol)
      setLocalProfile({ email: normalizedEmail, nombre_completo: name })
      navigate("/dashboard")
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo crear la cuenta.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative min-h-screen flex flex-col overflow-hidden" style={{ backgroundColor: "var(--bg-canvas)" }}>
      <HeroBackground image="term" imageOpacity={0.12} texture="grid" textureOpacity={0.06} />
      <div className="relative z-10">
        <Navbar />
      </div>
    <main
      className="relative z-10 flex-1 flex flex-col items-center justify-start sm:justify-center px-4 sm:px-0 py-6 sm:py-0"
    >
      <motion.div
        initial={{ opacity: 0, y: 16, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="w-full max-w-sm flex flex-col items-center gap-5 sm:gap-6 p-6 sm:p-8 rounded-lg my-6 sm:my-10"
        style={{
          backgroundColor: "var(--bg-surface)",
          border: "1px solid var(--ui-border-default)",
          boxShadow: "0 4px 32px rgba(0, 0, 0, 0.3)",
        }}
      >
        {/* Icono frío */}
        <motion.div
          initial={{ scale: 0.7, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.35, delay: 0.1 }}
          className="flex items-center justify-center w-12 sm:w-14 h-12 sm:h-14 rounded-lg"
          style={{ backgroundColor: "var(--bg-surface-hover)" }}
        >
          <svg
            className="w-5 sm:w-6 h-5 sm:h-6"
            style={{ color: "var(--text-muted)" }}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
          </svg>
        </motion.div>

        <h1
          className="text-xl sm:text-2xl font-semibold text-center m-0"
          style={{ color: "var(--text-heading)", fontFamily: "var(--font-heading)" }}
        >
          Create Account
        </h1>

        <AnimatePresence>
          {error && (
            <motion.p
              initial={{ opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: [0, -6, 6, -3, 0] }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.35 }}
              className="text-sm w-full text-center m-0"
              style={{ color: "var(--accent-danger)" }}
            >
              {error}
            </motion.p>
          )}
        </AnimatePresence>

        <form onSubmit={handleSubmit} className="w-full flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium" style={{ color: "var(--text-base)" }}>
              Name
            </label>
            <input
              type="text"
              placeholder="Your name"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2.5 rounded text-sm outline-none border transition-colors"
              style={{
                backgroundColor: "var(--bg-canvas)",
                borderColor: "var(--ui-border-default)",
                color: "var(--text-heading)",
              }}
              onFocus={(e) => { e.currentTarget.style.borderColor = "var(--accent-primary)" }}
              onBlur={(e) => { e.currentTarget.style.borderColor = "var(--ui-border-default)" }}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium" style={{ color: "var(--text-base)" }}>
              Email
            </label>
            <input
              type="email"
              placeholder="name@domain.com"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2.5 rounded text-sm outline-none border transition-colors"
              style={{
                backgroundColor: "var(--bg-canvas)",
                borderColor: "var(--ui-border-default)",
                color: "var(--text-heading)",
              }}
              onFocus={(e) => { e.currentTarget.style.borderColor = "var(--accent-primary)" }}
              onBlur={(e) => { e.currentTarget.style.borderColor = "var(--ui-border-default)" }}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium" style={{ color: "var(--text-base)" }}>
              Password
            </label>
            <input
              type="password"
              placeholder="············"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2.5 rounded text-sm outline-none border transition-colors"
              style={{
                backgroundColor: "var(--bg-canvas)",
                borderColor: "var(--ui-border-default)",
                color: "var(--text-heading)",
              }}
              onFocus={(e) => { e.currentTarget.style.borderColor = "var(--accent-primary)" }}
              onBlur={(e) => { e.currentTarget.style.borderColor = "var(--ui-border-default)" }}
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium" style={{ color: "var(--text-base)" }}>
              Confirm Password
            </label>
            <input
              type="password"
              placeholder="············"
              required
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              className="w-full px-3 py-2.5 rounded text-sm outline-none border transition-colors"
              style={{
                backgroundColor: "var(--bg-canvas)",
                borderColor: "var(--ui-border-default)",
                color: "var(--text-heading)",
              }}
              onFocus={(e) => { e.currentTarget.style.borderColor = "var(--accent-primary)" }}
              onBlur={(e) => { e.currentTarget.style.borderColor = "var(--ui-border-default)" }}
            />
          </div>

          <motion.button
            type="submit"
            disabled={loading}
            whileHover={{ scale: loading ? 1 : 1.02 }}
            whileTap={{ scale: loading ? 1 : 0.97 }}
            className="w-full py-2.5 rounded text-sm font-semibold border-none cursor-pointer transition-opacity hover:opacity-85 disabled:opacity-50"
            style={{
              backgroundColor: "var(--text-heading)",
              color: "#0F1117",
              fontFamily: "var(--font-mono)",
            }}
          >
            {loading ? "Creating account…" : "Sign Up"}
          </motion.button>
        </form>

        {OAUTH_ENABLED && (
          <>
            {/* Divider */}
            <div className="w-full flex items-center gap-3 text-xs" style={{ color: "var(--ui-border-default)" }}>
              <div className="flex-1 h-px" style={{ backgroundColor: "var(--ui-border-default)" }} />
              <span>or continue with</span>
              <div className="flex-1 h-px" style={{ backgroundColor: "var(--ui-border-default)" }} />
            </div>

            <OAuthButtons />
          </>
        )}

        <p className="text-sm m-0" style={{ color: "var(--text-muted)" }}>
          Already have an account?{" "}
          <Link
            to="/login"
            className="font-semibold no-underline transition-colors hover:underline"
            style={{ color: "var(--accent-primary)" }}
            onMouseEnter={(e) => { e.currentTarget.style.color = "var(--text-heading)" }}
            onMouseLeave={(e) => { e.currentTarget.style.color = "var(--accent-primary)" }}
          >
            Sign In
          </Link>
        </p>
      </motion.div>
    </main>
    </div>
  )
}
