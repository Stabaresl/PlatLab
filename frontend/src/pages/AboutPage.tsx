import { useEffect, useState, useCallback } from "react"
import { useNavigate } from "react-router-dom"
import grimBg from "../assets/grim.png"

export default function AboutPage() {
  const navigate = useNavigate()
  const [showScrollTop, setShowScrollTop] = useState(false)

  const handleScroll = useCallback(() => {
    setShowScrollTop(window.scrollY > 400)
  }, [])

  useEffect(() => {
    window.addEventListener("scroll", handleScroll, { passive: true })
    return () => window.removeEventListener("scroll", handleScroll)
  }, [handleScroll])

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: "smooth" })
  }

  return (
    <div className="min-h-screen flex flex-col relative" style={{ color: "var(--text-base)" }}>
      {/* ── Fondo grim.png con blur ── */}
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
          backgroundColor: "rgba(15, 17, 23, 0.6)",
          backdropFilter: "blur(10px)",
          WebkitBackdropFilter: "blur(10px)",
        }}
      />

      {/* ── Contenido ── */}
      <div className="relative z-10 flex flex-col min-h-screen">
        {/* ── Header ── */}
        <header
          className="flex items-center justify-between w-full
            px-4 sm:px-6 md:px-8 lg:px-12
            h-16 sm:h-20 lg:h-[100px]"
        >
          <button
            type="button"
            onClick={() => navigate("/")}
            className="bg-transparent border-none cursor-pointer p-0"
          >
            <span
              className="text-2xl sm:text-3xl font-semibold select-none"
              style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}
            >
              GAIA
            </span>
          </button>

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

        {/* ══════════════════════════════════════════════
            CONTENIDO PRINCIPAL — scroll
            ══════════════════════════════════════════════ */}
        <main className="flex-1 w-full px-4 sm:px-6 md:px-8 lg:px-12 pb-12 sm:pb-20">
          <div className="mx-auto" style={{ maxWidth: "960px" }}>
            {/* ── Hero de la página ── */}
            <section className="mb-12 sm:mb-20">
              <h1
                className="text-3xl sm:text-4xl md:text-5xl font-semibold mb-3 sm:mb-4"
                style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}
              >
                ¿Qué es PlatLAB?
              </h1>
              <p
                className="text-sm sm:text-base md:text-lg leading-relaxed mb-5 sm:mb-6"
                style={{ maxWidth: "720px", lineHeight: "1.7" }}
              >
                PlatLAB es una plataforma de laboratorios interactivos de hacking ético y 
                ciberseguridad. Está diseñada para que estudiantes, instructores y profesionales 
                puedan aprender, enseñar y evaluar habilidades de seguridad informática en 
                entornos controlados, sin riesgo para sistemas reales.
              </p>
              <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 sm:gap-4">
                <a
                  href="https://github.com/Stabaresl/PlatLab"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-5 sm:px-6 py-2.5 sm:py-3 rounded text-xs sm:text-sm font-semibold cursor-pointer border-none no-underline transition-opacity hover:opacity-80"
                  style={{
                    backgroundColor: "var(--text-heading)",
                    color: "#0F1117",
                    fontFamily: "'Fira Code', monospace",
                  }}
                >
                  <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
                  </svg>
                  Ver en GitHub
                </a>
                <button
                  type="button"
                  onClick={() => navigate("/signup")}
                  className="px-5 sm:px-6 py-2.5 sm:py-3 rounded text-xs sm:text-sm font-semibold cursor-pointer border transition-colors"
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
                  Empezar ahora
                </button>
              </div>
            </section>

            {/* ═══════════════════════════
                CARACTERÍSTICAS
                ═══════════════════════════ */}
            <section className="mb-12 sm:mb-20">
              <h2
                className="text-xl sm:text-2xl font-semibold mb-6 sm:mb-8"
                style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}
              >
                Características principales
              </h2>

              <div className="grid gap-4 sm:gap-6" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))" }}>
                <FeatureCard
                  icon={
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                  }
                  title="Laboratorios interactivos"
                  description="Entornos controlados donde resolver desafíos reales de hacking ético. Cada laboratorio contiene secciones teóricas y prácticas con flags que validan tu progreso."
                />
                <FeatureCard
                  icon={
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  }
                  title="Pistas progresivas"
                  description="¿Te trabaste? El sistema te da una pista tras 5 intentos fallidos y el paso a paso completo tras 15. Diseñado para que aprendas, no para que te frustres."
                />
                <FeatureCard
                  icon={
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                    </svg>
                  }
                  title="Roles definidos"
                  description="Tres roles con permisos específicos: Estudiante (aprende y practica), Instructor (crea y asigna laboratorios personalizados), Administrador (gestiona la plataforma)."
                />
                <FeatureCard
                  icon={
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                    </svg>
                  }
                  title="Examen final"
                  description="Cada laboratorio incluye un examen final que se habilita al completar todas las secciones. Los instructores pueden crear sus propios exámenes de opción múltiple."
                />
                <FeatureCard
                  icon={
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                    </svg>
                  }
                  title="Progreso automático"
                  description="Todo se guarda automáticamente. Podés retomar cualquier laboratorio exactamente donde lo dejaste, incluso después de cerrar sesión o ante una caída del sistema."
                />
                <FeatureCard
                  icon={
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h9m5.25 0l-3-3m0 0l3-3m-3 3H21" />
                    </svg>
                  }
                  title="Invitaciones con control de tiempo"
                  description="Los instructores pueden asignar laboratorios con o sin fecha de vencimiento. Al vencer, el acceso se bloquea automáticamente. Ideal para evaluaciones con plazo definido."
                />
              </div>
            </section>

            {/* ═══════════════════════════
                ARQUITECTURA
                ═══════════════════════════ */}
            <section className="mb-12 sm:mb-20">
              <h2
                className="text-xl sm:text-2xl font-semibold mb-6 sm:mb-8"
                style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}
              >
                Stack tecnológico
              </h2>

              <div
                className="p-5 sm:p-8 rounded-lg mb-6"
                style={{
                  backgroundColor: "var(--bg-surface)",
                  border: "1px solid var(--ui-border-default)",
                }}
              >
                <div className="grid gap-6 sm:gap-8" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))" }}>
                  <TechStackGroup
                    title="Frontend"
                    items={[
                      { label: "React 19", desc: "UI declarativa con Server Components" },
                      { label: "TypeScript", desc: "Tipado estricto en toda la app" },
                      { label: "Tailwind CSS 4", desc: "Estilos utilitarios con diseño atómico" },
                      { label: "Vite", desc: "Build tool rápida con HMR" },
                    ]}
                  />
                  <TechStackGroup
                    title="Backend"
                    items={[
                      { label: "Django + DRF", desc: "API REST con patrón MVT" },
                      { label: "PostgreSQL", desc: "Base de datos relacional" },
                      { label: "Celery + Redis", desc: "Tareas asíncronas y caché" },
                      { label: "SimpleJWT", desc: "Autenticación por tokens JWT" },
                    ]}
                  />
                  <TechStackGroup
                    title="Infraestructura"
                    items={[
                      { label: "Docker Compose", desc: "Orquestación de servicios" },
                      { label: "Arquitectura Hexagonal", desc: "Clean Architecture con DDD" },
                      { label: "API REST", desc: "Documentada con OpenAPI/Swagger" },
                      { label: "OAuth2 + PKCE", desc: "Google y GitHub como proveedores" },
                    ]}
                  />
                </div>
              </div>
            </section>

            {/* ═══════════════════════════
                DOCUMENTACIÓN
                ═══════════════════════════ */}
            <section className="mb-12 sm:mb-20">
              <h2
                className="text-xl sm:text-2xl font-semibold mb-6 sm:mb-8"
                style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}
              >
                Documentación del proyecto
              </h2>

              <div
                className="p-5 sm:p-8 rounded-lg"
                style={{
                  backgroundColor: "var(--bg-surface)",
                  border: "1px solid var(--ui-border-default)",
                }}
              >
                <p className="text-xs sm:text-sm leading-relaxed mb-4" style={{ color: "var(--text-muted)" }}>
                  El proyecto cuenta con documentación técnica detallada que cubre todos los aspectos 
                  del diseño y la implementación:
                </p>
                <div className="grid gap-3" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))" }}>
                  <DocItem
                    title="Historias de usuario"
                    desc="33 HU con criterios de aceptación, prioridades y trazabilidad completa"
                  />
                  <DocItem
                    title="Casos de uso"
                    desc="12 casos de uso detallados con flujos principales, alternativos y excepciones"
                  />
                  <DocItem
                    title="Modelo de dominio"
                    desc="26 entidades, 17 value objects, 7 servicios de dominio, 7 agregados"
                  />
                  <DocItem
                    title="API REST"
                    desc="30+ endpoints documentados con DTOs, validaciones y códigos de error"
                  />
                  <DocItem
                    title="Seguridad"
                    desc="Matriz RBAC, JWT, OAuth2, rate limiting, OWASP Top 10 mapeado"
                  />
                  <DocItem
                    title="Estructura del backend"
                    desc="8 módulos con Clean Architecture: 4 capas por módulo"
                  />
                </div>
              </div>
            </section>

            {/* ═══════════════════════════
                REPOSITORIO
                ═══════════════════════════ */}
            <section>
              <div
                className="p-5 sm:p-8 rounded-lg text-center"
                style={{
                  backgroundColor: "var(--bg-surface)",
                  border: "1px solid var(--ui-border-secondary)",
                }}
              >
                <h2
                  className="text-xl sm:text-2xl font-semibold mb-3"
                  style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}
                >
                  Repositorio
                </h2>
                <p className="text-xs sm:text-sm mb-5" style={{ color: "var(--text-muted)" }}>
                  Todo el código fuente está disponible en GitHub. Contribuciones, issues y forks son bienvenidos.
                </p>
                <a
                  href="https://github.com/Stabaresl/PlatLab"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-5 sm:px-6 py-2.5 sm:py-3 rounded text-xs sm:text-sm font-semibold no-underline transition-opacity hover:opacity-80"
                  style={{
                    backgroundColor: "var(--text-heading)",
                    color: "#0F1117",
                    fontFamily: "'Fira Code', monospace",
                  }}
                >
                  <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
                  </svg>
                  github.com/Stabaresl/PlatLab
                </a>
              </div>
            </section>

            {/* ═══════════════════════════
                VOLVER AL INICIO
                ═══════════════════════════ */}
            <section className="mt-12 sm:mt-16 mb-4 text-center">
              <button
                type="button"
                onClick={() => navigate("/")}
                className="inline-flex items-center gap-2 px-5 sm:px-6 py-2.5 sm:py-3 rounded text-xs sm:text-sm font-semibold cursor-pointer border transition-colors"
                style={{
                  backgroundColor: "transparent",
                  borderColor: "var(--ui-border-default)",
                  color: "var(--text-muted)",
                  fontFamily: "'Fira Code', monospace",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = "var(--text-base)"
                  e.currentTarget.style.color = "var(--text-heading)"
                  e.currentTarget.style.backgroundColor = "var(--bg-surface)"
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = "var(--ui-border-default)"
                  e.currentTarget.style.color = "var(--text-muted)"
                  e.currentTarget.style.backgroundColor = "transparent"
                }}
              >
                <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                </svg>
                Volver al Inicio
              </button>
            </section>
          </div>
        </main>

        {/* ── Footer simplificado ── */}
        <footer
          className="w-full"
          style={{
            backgroundColor: "#0A0C12",
            borderTop: "1px solid var(--ui-border-default)",
          }}
        >
          <div
            className="w-full flex flex-col sm:flex-row items-center justify-between
              px-4 sm:px-6 md:px-8 lg:px-12 py-3 sm:py-4
              gap-2 sm:gap-0 text-xs"
            style={{ color: "var(--text-muted)" }}
          >
            <span>&copy; {new Date().getFullYear()} GAIA — PlatLAB. Todos los derechos reservados.</span>
            <div className="flex items-center gap-4 sm:gap-6">
              <button
                type="button"
                onClick={() => navigate("/")}
                className="bg-transparent border-none cursor-pointer text-xs"
                style={{ color: "var(--text-muted)" }}
                onMouseEnter={(e) => { e.currentTarget.style.color = "var(--text-heading)" }}
                onMouseLeave={(e) => { e.currentTarget.style.color = "var(--text-muted)" }}
              >
                Inicio
              </button>
              <a
                href="https://github.com/Stabaresl/PlatLab"
                target="_blank"
                rel="noopener noreferrer"
                className="no-underline text-xs transition-colors"
                style={{ color: "var(--text-muted)" }}
                onMouseEnter={(e) => { e.currentTarget.style.color = "var(--text-heading)" }}
                onMouseLeave={(e) => { e.currentTarget.style.color = "var(--text-muted)" }}
              >
                GitHub
              </a>
            </div>
          </div>
        </footer>

        {/* ── Float button: scroll to top ── */}
        <button
          type="button"
          onClick={scrollToTop}
          aria-label="Volver arriba"
          className="fixed bottom-6 sm:bottom-8 right-4 sm:right-8 flex items-center justify-center w-10 sm:w-12 h-10 sm:h-12 rounded-full cursor-pointer border transition-all duration-300 z-50"
          style={{
            backgroundColor: "var(--bg-surface)",
            borderColor: "var(--ui-border-default)",
            color: "var(--text-muted)",
            opacity: showScrollTop ? 1 : 0,
            pointerEvents: showScrollTop ? "auto" : "none",
            transform: showScrollTop ? "translateY(0)" : "translateY(16px)",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = "var(--accent-primary)"
            e.currentTarget.style.color = "var(--accent-primary)"
            e.currentTarget.style.backgroundColor = "var(--bg-surface-hover)"
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = "var(--ui-border-default)"
            e.currentTarget.style.color = "var(--text-muted)"
            e.currentTarget.style.backgroundColor = "var(--bg-surface)"
          }}
        >
          <svg className="w-4 sm:w-5 h-4 sm:h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 15l7-7 7 7" />
          </svg>
        </button>
      </div>
    </div>
  )
}

/* ───────── FeatureCard ───────── */
function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode
  title: string
  description: string
}) {
  return (
    <div
      className="flex flex-col p-4 sm:p-5 rounded-lg transition-colors"
      style={{
        backgroundColor: "var(--bg-surface)",
        border: "1px solid var(--ui-border-default)",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = "var(--bg-surface-hover)"
        e.currentTarget.style.borderColor = "var(--ui-border-secondary)"
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = "var(--bg-surface)"
        e.currentTarget.style.borderColor = "var(--ui-border-default)"
      }}
    >
      <div
        className="flex items-center justify-center w-10 h-10 rounded-lg mb-3 shrink-0"
        style={{ backgroundColor: "var(--bg-surface-hover)", color: "var(--text-muted)" }}
      >
        {icon}
      </div>
      <h3
        className="text-sm sm:text-base font-medium mb-1.5"
        style={{ color: "var(--text-heading)", fontFamily: "'Fira Sans', sans-serif" }}
      >
        {title}
      </h3>
      <p className="text-xs sm:text-sm leading-relaxed m-0" style={{ color: "var(--text-muted)" }}>
        {description}
      </p>
    </div>
  )
}

/* ───────── TechStackGroup ───────── */
function TechStackGroup({
  title,
  items,
}: {
  title: string
  items: { label: string; desc: string }[]
}) {
  return (
    <div className="flex flex-col gap-2 sm:gap-3">
      <h4
        className="text-xs sm:text-sm font-semibold m-0"
        style={{ color: "var(--text-heading)", fontFamily: "'Fira Code', monospace" }}
      >
        {title}
      </h4>
      {items.map((item) => (
        <div key={item.label} className="flex flex-col gap-0.5">
          <span className="text-xs sm:text-sm font-medium" style={{ color: "var(--text-base)" }}>
            {item.label}
          </span>
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>
            {item.desc}
          </span>
        </div>
      ))}
    </div>
  )
}

/* ───────── DocItem ───────── */
function DocItem({ title, desc }: { title: string; desc: string }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs sm:text-sm font-medium" style={{ color: "var(--text-base)" }}>
        {title}
      </span>
      <span className="text-xs leading-relaxed" style={{ color: "var(--text-muted)" }}>
        {desc}
      </span>
    </div>
  )
}
