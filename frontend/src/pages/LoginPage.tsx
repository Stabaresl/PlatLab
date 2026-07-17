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
        body: JSON.stringify({ email, password }),
      })
      localStorage.setItem("token", data.token)
      localStorage.setItem("user", JSON.stringify(data.user))
      navigate("/welcome")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center" style={{ backgroundColor: "var(--bg-canvas)" }}>
      <div
        className="w-full max-w-sm flex flex-col items-center gap-6 p-8 rounded-lg"
        style={{
          backgroundColor: "var(--bg-surface)",
          border: "1px solid var(--ui-border-gold)",
        }}
      >
        <div className="flex items-center justify-center w-14 h-14 rounded-lg" style={{ backgroundColor: "var(--accent-danger)" }}>
          <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>
        <h1 className="text-2xl font-semibold text-center" style={{ color: "var(--text-heading)" }}>GAIA</h1>

        {error && <p className="text-sm w-full text-center" style={{ color: "var(--accent-danger)" }}>{error}</p>}

        <form onSubmit={handleSubmit} className="w-full flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium" style={{ color: "var(--text-base)" }}>Email</label>
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
              onFocus={(e) => (e.target.style.borderColor = "var(--ui-border-gold)")}
              onBlur={(e) => (e.target.style.borderColor = "var(--ui-border-default)")}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium" style={{ color: "var(--text-base)" }}>Password</label>
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
              onFocus={(e) => (e.target.style.borderColor = "var(--ui-border-gold)")}
              onBlur={(e) => (e.target.style.borderColor = "var(--ui-border-default)")}
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded text-sm font-semibold text-white border-none cursor-pointer transition-opacity hover:opacity-90 disabled:opacity-50"
            style={{ backgroundColor: "var(--accent-danger)", fontFamily: "'Fira Code', monospace" }}
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

        <p className="text-sm" style={{ color: "var(--text-muted)" }}>
          Don&apos;t have an account?{" "}
          <Link to="/signup" className="font-semibold no-underline hover:underline" style={{ color: "var(--accent-primary)" }}>
            Sign Up
          </Link>
        </p>
      </div>
    </main>
  )
}
