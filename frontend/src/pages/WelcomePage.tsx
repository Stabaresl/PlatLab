import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { api } from "./api"

interface MeResponse {
  user: { id: number; name: string; email: string }
}

export default function WelcomePage() {
  const navigate = useNavigate()
  const [user, setUser] = useState<MeResponse["user"] | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api<MeResponse>("/me")
      .then((data) => setUser(data.user))
      .catch(() => {
        localStorage.removeItem("token")
        localStorage.removeItem("user")
        navigate("/login")
      })
      .finally(() => setLoading(false))
  }, [navigate])

  const handleLogout = () => {
    localStorage.removeItem("token")
    localStorage.removeItem("user")
    navigate("/login")
  }

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center" style={{ backgroundColor: "var(--bg-canvas)" }}>
        <p className="text-lg" style={{ color: "var(--text-muted)" }}>Loading…</p>
      </main>
    )
  }

  return (
    <main className="min-h-screen flex items-center justify-center" style={{ backgroundColor: "var(--bg-canvas)" }}>
      <div
        className="w-full max-w-md flex flex-col items-center gap-8 p-10 rounded-lg"
        style={{
          backgroundColor: "var(--bg-surface)",
          border: "1px solid var(--ui-border-gold)",
        }}
      >
        <div className="flex items-center justify-center w-16 h-16 rounded-full" style={{ backgroundColor: "var(--accent-primary)" }}>
          <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0zm6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h1 className="text-3xl font-bold text-center" style={{ color: "var(--text-heading)" }}>
          Bienvenido {user?.name ?? "Usuario"}
        </h1>
        <p className="text-base text-center" style={{ color: "var(--text-base)" }}>
          {user?.email}
        </p>

        <button
          onClick={handleLogout}
          className="w-full py-2.5 rounded text-sm font-semibold text-white border-none cursor-pointer transition-opacity hover:opacity-90"
          style={{ backgroundColor: "var(--accent-danger)", fontFamily: "'Fira Code', monospace" }}
        >
          Sign Out
        </button>
      </div>
    </main>
  )
}
