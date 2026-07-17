import { useState, type FormEvent } from "react"
import { useNavigate, Link } from "react-router-dom"
import { api } from "./api"
import OAuthButtons from "./OAuthButtons"

interface RegisterResponse {
  token: string
  user: { id: number; name: string; email: string }
}

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
      setError("Passwords do not match")
      return
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters")
      return
    }

    setLoading(true)
    try {
      const data = await api<RegisterResponse>("/register", {
        method: "POST",
        body: JSON.stringify({ name, email, password }),
      })
      localStorage.setItem("token", data.token)
      localStorage.setItem("user", JSON.stringify(data.user))
      navigate("/welcome")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed")
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
        <div className="flex items-center justify-center w-14 h-14 rounded-lg" style={{ backgroundColor: "var(--accent-primary)" }}>
          <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
          </svg>
        </div>
        <h1 className="text-2xl font-semibold text-center" style={{ color: "var(--text-heading)" }}>Create Account</h1>

        {error && <p className="text-sm w-full text-center" style={{ color: "var(--accent-danger)" }}>{error}</p>}

        <form onSubmit={handleSubmit} className="w-full flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium" style={{ color: "var(--text-base)" }}>Name</label>
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
              onFocus={(e) => (e.target.style.borderColor = "var(--ui-border-gold)")}
              onBlur={(e) => (e.target.style.borderColor = "var(--ui-border-default)")}
            />
          </div>
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
              minLength={6}
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
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium" style={{ color: "var(--text-base)" }}>Confirm Password</label>
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
              onFocus={(e) => (e.target.style.borderColor = "var(--ui-border-gold)")}
              onBlur={(e) => (e.target.style.borderColor = "var(--ui-border-default)")}
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded text-sm font-semibold text-white border-none cursor-pointer transition-opacity hover:opacity-90 disabled:opacity-50"
            style={{ backgroundColor: "var(--accent-primary)", fontFamily: "'Fira Code', monospace" }}
          >
            {loading ? "Creating account…" : "Sign Up"}
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
          Already have an account?{" "}
          <Link to="/login" className="font-semibold no-underline hover:underline" style={{ color: "var(--accent-primary)" }}>
            Sign In
          </Link>
        </p>
      </div>
    </main>
  )
}
