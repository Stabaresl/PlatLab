import { useNavigate } from "react-router-dom"

export default function Footer() {
  const navigate = useNavigate()

  return (
    <footer
      className="w-full"
      style={{ backgroundColor: "#0A0C12", borderTop: "1px solid var(--ui-border-default)" }}
    >
      <div
        className="w-full mx-auto px-4 sm:px-6 md:px-8 lg:px-12 py-8 sm:py-10"
        style={{ maxWidth: "1400px" }}
      >
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 sm:gap-8 md:gap-12">
          <div className="col-span-2 sm:col-span-1 flex flex-col gap-2 sm:gap-3">
            <span
              className="text-lg sm:text-xl font-semibold"
              style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}
            >
              GAIA
            </span>
            <p className="text-xs sm:text-sm leading-relaxed" style={{ color: "var(--text-muted)" }}>
              Plataforma de laboratorios interactivos para aprender ciberseguridad
              mediante la práctica en entornos reales controlados.
            </p>
          </div>

          <div className="flex flex-col gap-1.5 sm:gap-2.5">
            <span className="text-xs sm:text-sm font-semibold" style={{ color: "var(--text-heading)" }}>
              Plataforma
            </span>
            <a
              href="#"
              onClick={(e) => { e.preventDefault(); navigate("/login") }}
              className="text-xs sm:text-sm no-underline transition-colors hover:underline"
              style={{ color: "var(--text-muted)" }}
              onMouseEnter={(e) => { e.currentTarget.style.color = "var(--text-base)" }}
              onMouseLeave={(e) => { e.currentTarget.style.color = "var(--text-muted)" }}
            >
              Laboratorios
            </a>
            <a
              href="#"
              onClick={(e) => { e.preventDefault(); navigate("/signup") }}
              className="text-xs sm:text-sm no-underline transition-colors hover:underline"
              style={{ color: "var(--text-muted)" }}
              onMouseEnter={(e) => { e.currentTarget.style.color = "var(--text-base)" }}
              onMouseLeave={(e) => { e.currentTarget.style.color = "var(--text-muted)" }}
            >
              Registrarse
            </a>
            <a
              href="#"
              onClick={(e) => { e.preventDefault(); navigate("/dashboard") }}
              className="text-xs sm:text-sm no-underline transition-colors hover:underline"
              style={{ color: "var(--text-muted)" }}
              onMouseEnter={(e) => { e.currentTarget.style.color = "var(--text-base)" }}
              onMouseLeave={(e) => { e.currentTarget.style.color = "var(--text-muted)" }}
            >
              Dashboard
            </a>
          </div>

          <div className="flex flex-col gap-1.5 sm:gap-2.5">
            <span className="text-xs sm:text-sm font-semibold" style={{ color: "var(--text-heading)" }}>
              Recursos
            </span>
            <a
              href="http://localhost:8000/api/v1/docs/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs sm:text-sm no-underline transition-colors hover:underline"
              style={{ color: "var(--text-muted)" }}
              onMouseEnter={(e) => { e.currentTarget.style.color = "var(--text-base)" }}
              onMouseLeave={(e) => { e.currentTarget.style.color = "var(--text-muted)" }}
            >
              Documentación API
            </a>
            <span className="text-xs sm:text-sm" style={{ color: "var(--text-muted)" }}>
              Estado del sistema
            </span>
          </div>

          <div className="flex flex-col gap-1.5 sm:gap-2.5">
            <span className="text-xs sm:text-sm font-semibold" style={{ color: "var(--text-heading)" }}>
              Conectar
            </span>
            <div className="flex items-center gap-3 sm:gap-4">
              <a
                href="https://github.com/Stabaresl/PlatLab"
                target="_blank"
                rel="noopener noreferrer"
                className="transition-opacity hover:opacity-80"
                aria-label="GitHub"
              >
                <svg className="w-4 h-4 sm:w-5 sm:h-5" viewBox="0 0 24 24" fill="var(--text-muted)">
                  <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
                </svg>
              </a>
              <a
                href="mailto:contact@gaia-platlab.com"
                className="transition-opacity hover:opacity-80"
                aria-label="Email"
              >
                <svg className="w-4 h-4 sm:w-5 sm:h-5" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </a>
            </div>
          </div>
        </div>

        <div
          className="flex flex-col sm:flex-row items-center justify-between pt-4 sm:pt-5 mt-6 sm:mt-8 gap-2 sm:gap-0 text-xs"
          style={{ borderTop: "1px solid var(--ui-border-default)", color: "var(--text-muted)" }}
        >
          <span>&copy; {new Date().getFullYear()} GAIA — PlatLAB.</span>
          <div className="flex items-center gap-4 sm:gap-6">
            <span>Privacidad</span>
            <span>Términos</span>
          </div>
        </div>
      </div>
    </footer>
  )
}
