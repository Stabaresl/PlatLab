import { useState, type FormEvent } from "react"
import { useNavigate, Link } from "react-router-dom"
import { api } from "./api"
import OAuthButtons from "./OAuthButtons"

interface LoginResponse {
  token: string
  user: { id: number; name: string; email: string }
}

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
      const data = await api<LoginResponse>("/login", {
        method: "POST",
        body: JSON.stringify({ email: email.toLowerCase(), password }),
      })
      localStorage.setItem("token", data.token)
      localStorage.setItem("user", JSON.stringify(data.user))
      // TODO: Reemplazar 'estudiante' fijo por el rol que devuelva el backend
      localStorage.setItem("role", "estudiante")
      navigate("/dashboard")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <main
      className="min-h-screen flex flex-col items-center justify-start sm:justify-center px-4 sm:px-0 pt-8 sm:pt-0"
      style={{ backgroundColor: "var(--bg-canvas)" }}
    >
      <div
        className="w-full max-w-sm flex flex-col items-center gap-5 sm:gap-6 p-6 sm:p-8 rounded-lg"
        style={{
          backgroundColor: "var(--bg-surface)",
          border: "1px solid var(--ui-border-default)",
          boxShadow: "0 4px 32px rgba(0, 0, 0, 0.3)",
        }}
      >
        {/* Icono frío */}
        <div
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
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>

        <h1
          className="text-xl sm:text-2xl font-semibold text-center m-0"
          style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}
        >
          GAIA
        </h1>

        {error && (
          <p className="text-sm w-full text-center m-0" style={{ color: "var(--accent-danger)" }}>
            {error}
          </p>
        )}

        <form onSubmit={handleSubmit} className="w-full flex flex-col gap-4">
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

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded text-sm font-semibold border-none cursor-pointer transition-opacity hover:opacity-85 disabled:opacity-50"
            style={{
              backgroundColor: "var(--text-heading)",
              color: "#0F1117",
              fontFamily: "'Fira Code', monospace",
            }}
          >
            {loading ? "Signing in…" : "Sign In"}
          </button>
        </form>

        {/* Divider */}
        <div className="w-full flex items-center gap-3 text-xs" style={{ color: "var(--ui-border-default)" }}>
          <div className="flex-1 h-px" style={{ backgroundColor: "var(--ui-border-default)" }} />
          <span>or continue with</span>
          <div className="flex-1 h-px" style={{ backgroundColor: "var(--ui-border-default)" }} />
        </div>

        <OAuthButtons />

        <p className="text-sm m-0" style={{ color: "var(--text-muted)" }}>
          Don&apos;t have an account?{" "}
          <Link
            to="/signup"
            className="font-semibold no-underline transition-colors hover:underline"
            style={{ color: "var(--accent-primary)" }}
            onMouseEnter={(e) => { e.currentTarget.style.color = "var(--text-heading)" }}
            onMouseLeave={(e) => { e.currentTarget.style.color = "var(--accent-primary)" }}
          >
            Sign Up
          </Link>
        </p>
      </div>
    </main>
  )
}
