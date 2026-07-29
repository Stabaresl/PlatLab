import { useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import grimBg from "../assets/grim.png"
import termBg from "../assets/term.png"

export default function WelcomePage() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen flex flex-col relative" style={{ color: "var(--text-base)" }}>
      {/* ═══════════════════════════════════════════
          CAPA DE FONDO — grim.png con blur
          ═══════════════════════════════════════════ */}
      <div
        className="absolute inset-0"
        style={{
          backgroundImage: `url(${grimBg})`,
          backgroundSize: "cover",
          backgroundPosition: "center",
          backgroundRepeat: "no-repeat",
        }}
      />
      <div
        className="absolute inset-0"
        style={{
          backgroundColor: "rgba(15, 17, 23, 0.55)",
          backdropFilter: "blur(8px)",
          WebkitBackdropFilter: "blur(8px)",
        }}
      />

      {/* ═══════════════════════════════════════════
          CONTENIDO
          ═══════════════════════════════════════════ */}
      <div className="relative z-10 flex flex-col min-h-screen">
        {/* ─── HEADER ─── */}
        <header
          className="flex items-center justify-between w-full
            px-4 sm:px-6 md:px-8 lg:px-12
            h-16 sm:h-20 lg:h-[100px]"
        >
          <span
            className="text-2xl sm:text-3xl font-semibold select-none"
            style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}
          >
            GAIA
          </span>

          <nav className="flex items-center gap-2 sm:gap-3 md:gap-4">
            <button
              type="button"
              onClick={() => navigate("/signup")}
              className="
                px-3 sm:px-5 md:px-6
                py-1.5 sm:py-2 md:py-3
                rounded text-xs sm:text-sm
                font-semibold cursor-pointer border
                transition-all duration-200
                whitespace-nowrap
              "
              style={{
                backgroundColor: "transparent",
                borderColor: "transparent",
                color: "var(--text-heading)",
                fontFamily: "'Fira Code', monospace",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = "#EF4444"
                e.currentTarget.style.borderColor = "#EF4444"
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = "var(--text-heading)"
                e.currentTarget.style.borderColor = "transparent"
              }}
            >
              Sign Up
            </button>

            <button
              type="button"
              onClick={() => navigate("/login")}
              className="
                px-3 sm:px-5 md:px-6
                py-1.5 sm:py-2 md:py-3
                rounded text-xs sm:text-sm
                font-semibold cursor-pointer border-none
                transition-opacity hover:opacity-80
                whitespace-nowrap
              "
              style={{
                backgroundColor: "var(--text-heading)",
                color: "#0F1117",
                fontFamily: "'Fira Code', monospace",
              }}
            >
              Get Started
            </button>
          </nav>
        </header>

        {/* ─── HERO ─── */}
        <section
          className="
            flex-1 flex flex-col lg:flex-row items-center
            w-full
            px-4 sm:px-6 md:px-8 lg:px-12
            py-8 sm:py-12 md:py-16 lg:py-0
            gap-6 sm:gap-8 md:gap-12 lg:gap-[80px]
          "
        >
          {/* Columna izquierda: texto */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className="
              flex flex-col items-center lg:items-start
              w-full lg:w-1/2
              gap-4 sm:gap-5 md:gap-6 lg:gap-8
              text-center lg:text-left
            "
          >
            <h1
              className="
                text-3xl sm:text-4xl md:text-5xl
                font-semibold leading-tight
              "
              style={{
                color: "var(--text-heading)",
                fontFamily: "'Fira Sans', sans-serif",
              }}
            >
              Aprende seguridad
              <br />
              informática
            </h1>

            <p
              className="
                text-sm sm:text-base md:text-lg
                leading-relaxed
              "
              style={{ maxWidth: "560px", lineHeight: "1.7" }}
            >
              Plataforma de laboratorios interactivos de hacking ético.
              Pon a prueba tus habilidades en entornos reales controlados,
              aprende de tus errores y conviértete en un experto en
              ciberseguridad.
            </p>

            <div className="flex items-center gap-3 sm:gap-4">
              <button
                type="button"
                onClick={() => navigate("/login")}
                className="
                  px-5 sm:px-6 md:px-8
                  py-2 sm:py-2.5 md:py-3
                  rounded text-xs sm:text-sm
                  font-semibold cursor-pointer border-none
                  transition-opacity hover:opacity-80
                "
                style={{
                  backgroundColor: "var(--text-heading)",
                  color: "#0F1117",
                  fontFamily: "'Fira Code', monospace",
                }}
              >
                Sign In
              </button>

              <button
                type="button"
                onClick={() => navigate("/about")}
                className="
                  px-5 sm:px-6 md:px-8
                  py-2 sm:py-2.5 md:py-3
                  rounded text-xs sm:text-sm
                  font-semibold cursor-pointer border
                  transition-colors
                "
                style={{
                  backgroundColor: "transparent",
                  borderColor: "var(--ui-border-default)",
                  color: "var(--text-muted)",
                  fontFamily: "'Fira Code', monospace",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = "var(--text-base)"
                  e.currentTarget.style.color = "var(--text-base)"
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = "var(--ui-border-default)"
                  e.currentTarget.style.color = "var(--text-muted)"
                }}
              >
                know more
              </button>
            </div>
          </motion.div>

          {/* Columna derecha: card con term.png + borde dorado */}
          <div className="flex-1 flex items-center justify-center w-full lg:w-auto">
            <motion.div
              initial={{ opacity: 0, scale: 0.94 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.55, ease: "easeOut", delay: 0.15 }}
              whileHover={{ scale: 1.015 }}
              className="
                relative overflow-hidden
                w-full max-w-[650px]
                aspect-[650/371]
              "
              style={{
                borderRadius: "17px",
                border: "2px solid var(--ui-border-gold)",
                boxShadow: "0 0 0 1px rgba(0,0,0,0.2)",
              }}
            >
              {/* term.png como fondo */}
              <div
                className="absolute inset-0"
                style={{
                  backgroundImage: `url(${termBg})`,
                  backgroundSize: "cover",
                  backgroundPosition: "center",
                  backgroundRepeat: "no-repeat",
                }}
              />

              {/* Overlay con blur */}
              <div
                className="absolute inset-0"
                style={{
                  backgroundColor: "rgba(15, 17, 23, 0.3)",
                  backdropFilter: "blur(1px)",
                  WebkitBackdropFilter: "blur(1px)",
                }}
              />

              {/* Texto sobre la card */}
              <div className="relative z-10 flex items-center justify-center w-full h-full px-6 sm:px-8">
                <p
                  className="text-sm sm:text-base md:text-lg font-medium text-center"
                  style={{
                    color: "var(--text-heading)",
                    fontFamily: "'Fira Sans', sans-serif",
                  }}
                >
                  Explora, aprende y domina
                  <br />
                  la ciberseguridad
                </p>
              </div>
            </motion.div>
          </div>
        </section>

        {/* ─── FOOTER ─── */}
        <footer
          className="w-full"
          style={{
            backgroundColor: "#0A0C12",
            borderTop: "1px solid var(--ui-border-default)",
          }}
        >
          <div
            className="
              w-full mx-auto
              px-4 sm:px-6 md:px-8 lg:px-12
              py-8 sm:py-10
            "
            style={{ maxWidth: "1400px" }}
          >
            {/* Grid de columnas */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 sm:gap-8 md:gap-12">
              {/* Brand — ocupa todo el ancho en mobile, normal en desktop */}
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

              {/* Plataforma */}
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
                <span className="text-xs sm:text-sm" style={{ color: "var(--text-muted)" }}>
                  Dashboard
                </span>
              </div>

              {/* Recursos */}
              <div className="flex flex-col gap-1.5 sm:gap-2.5">
                <span className="text-xs sm:text-sm font-semibold" style={{ color: "var(--text-heading)" }}>
                  Recursos
                </span>
                <span className="text-xs sm:text-sm" style={{ color: "var(--text-muted)" }}>
                  Documentación
                </span>
                <span className="text-xs sm:text-sm" style={{ color: "var(--text-muted)" }}>
                  API
                </span>
                <span className="text-xs sm:text-sm" style={{ color: "var(--text-muted)" }}>
                  Estado del sistema
                </span>
              </div>

              {/* Conectar */}
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

            {/* Copyright */}
            <div
              className="
                flex flex-col sm:flex-row items-center justify-between
                pt-4 sm:pt-5 mt-6 sm:mt-8 gap-2 sm:gap-0
                text-xs
              "
              style={{
                borderTop: "1px solid var(--ui-border-default)",
                color: "var(--text-muted)",
              }}
            >
              <span>&copy; {new Date().getFullYear()} GAIA — PlatLAB.</span>
              <div className="flex items-center gap-4 sm:gap-6">
                <span>Privacidad</span>
                <span>Términos</span>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </div>
  )
}
