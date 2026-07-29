import { useEffect, useRef, useState } from "react"
import { useNavigate, useParams, useSearchParams } from "react-router-dom"
import { motion } from "framer-motion"
import { oauthCallback, setTokens, setLocalProfile, ApiError, type OAuthProvider } from "./api"

// Recibe el redirect de Google/GitHub (?code=...&state=...) y lo cambia
// por un par de tokens contra POST /auth/oauth/<provider>/callback/.
export default function OAuthCallbackPage() {
  const { provider } = useParams<{ provider: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [error, setError] = useState("")
  const ranOnce = useRef(false)

  useEffect(() => {
    if (ranOnce.current) return
    ranOnce.current = true

    const code = searchParams.get("code")
    const state = searchParams.get("state")

    if (!provider || !code || !state) {
      setError("Falta información del proveedor OAuth en la URL.")
      return
    }

    oauthCallback(provider as OAuthProvider, { code, state })
      .then((tokens) => {
        setTokens(tokens.access, tokens.refresh)
        localStorage.setItem("role", tokens.rol)
        setLocalProfile({ email: "" })
        navigate("/dashboard", { replace: true })
      })
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "No se pudo completar el inicio de sesión.")
      })
  }, [provider, searchParams, navigate])

  return (
    <main
      className="min-h-screen flex flex-col items-center justify-center gap-4 px-4"
      style={{ backgroundColor: "var(--bg-canvas)" }}
    >
      {!error ? (
        <>
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            className="w-8 h-8 rounded-full border-2"
            style={{ borderColor: "var(--ui-border-default)", borderTopColor: "var(--accent-primary)" }}
          />
          <p className="text-sm" style={{ color: "var(--text-muted)" }}>
            Conectando con {provider}…
          </p>
        </>
      ) : (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-sm text-center flex flex-col gap-3"
        >
          <p className="text-sm" style={{ color: "var(--accent-danger)" }}>{error}</p>
          <button
            onClick={() => navigate("/login")}
            className="text-sm font-semibold underline"
            style={{ color: "var(--accent-primary)" }}
          >
            Volver a inicio de sesión
          </button>
        </motion.div>
      )}
    </main>
  )
}
