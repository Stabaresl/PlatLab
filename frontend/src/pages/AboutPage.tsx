import { useEffect, useState, useCallback, type ReactNode } from "react"
import { useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import Navbar from "../components/Navbar"
import Footer from "../components/Footer"
import ReticleFrame from "../components/ReticleFrame"
import StatusDot from "../components/StatusDot"
import MouseGlow, { trackGlow, untrackGlow } from "../components/MouseGlow"
import { Button } from "../components/ui/button"
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

  const scrollToTop = () => window.scrollTo({ top: 0, behavior: "smooth" })

  return (
    <div className="min-h-screen flex flex-col relative" style={{ color: "var(--text-base)", backgroundColor: "var(--canvas)" }}>
      <div
        className="absolute inset-0"
        style={{
          backgroundImage: `url(${grimBg})`,
          backgroundSize: "cover",
          backgroundPosition: "center",
          backgroundRepeat: "no-repeat",
          opacity: 0.45,
          animation: "hero-kenburns 28s ease-in-out infinite",
          willChange: "transform",
        }}
      />
      <div className="absolute inset-0" style={{ backgroundColor: "rgba(8,9,12,0.7)", backdropFilter: "blur(10px)", WebkitBackdropFilter: "blur(10px)" }} />

      <div className="relative z-10 flex flex-col min-h-screen">
        <Navbar />

        <main className="flex-1 w-full px-4 sm:px-6 md:px-8 lg:px-12 pb-12 sm:pb-20">
          <div className="mx-auto" style={{ maxWidth: "960px" }}>
            {/* ── Hero ── */}
            <section
              onMouseMove={trackGlow}
              onMouseLeave={untrackGlow}
              className="relative mb-12 sm:mb-20 pt-8 sm:pt-12"
            >
              <MouseGlow color="56,214,245" size={460} opacity={0.1} />
              <div className="relative z-10">
                <StatusDot variant="info" label="Documento técnico // acceso público" className="mb-4" />
                <h1 className="text-display text-3xl sm:text-4xl md:text-5xl font-black uppercase leading-tight mb-3 sm:mb-4" style={{ color: "var(--text-heading)" }}>
                  ¿Qué es PlatLAB?
                </h1>
                <p className="text-sm sm:text-base md:text-lg leading-relaxed mb-5 sm:mb-6" style={{ maxWidth: "720px", lineHeight: "1.7" }}>
                  PlatLAB es una plataforma de laboratorios interactivos de hacking ético y
                  ciberseguridad. Está diseñada para que estudiantes, instructores y profesionales
                  puedan aprender, enseñar y evaluar habilidades de seguridad informática en
                  entornos controlados, sin riesgo para sistemas reales.
                </p>
                <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 sm:gap-4">
                  <Button asChild size="lg" className="chamfer font-mono text-xs sm:text-sm uppercase tracking-wide">
                    <a href="https://github.com/Stabaresl/PlatLab" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2">
                      <GitHubIcon />
                      Ver en GitHub
                    </a>
                  </Button>
                  <Button variant="outline" size="lg" onClick={() => navigate("/signup")} className="chamfer font-mono text-xs sm:text-sm uppercase tracking-wide">
                    Empezar ahora
                  </Button>
                </div>
              </div>
            </section>

            {/* ── Características ── */}
            <section className="mb-12 sm:mb-20">
              <SectionTitle color="var(--signal-amber)">Características principales</SectionTitle>

              <div className="grid gap-4 sm:gap-6" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))" }}>
                <FeatureCard
                  icon={<path strokeLinecap="round" strokeLinejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />}
                  title="Laboratorios interactivos"
                  description="Entornos controlados donde resolver desafíos reales de hacking ético. Cada laboratorio contiene secciones teóricas y prácticas con flags que validan tu progreso."
                />
                <FeatureCard
                  icon={<path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />}
                  title="Pistas progresivas"
                  description="¿Te trabaste? El sistema te da una pista tras 5 intentos fallidos y el paso a paso completo tras 15. Diseñado para que aprendas, no para que te frustres."
                />
                <FeatureCard
                  icon={<path strokeLinecap="round" strokeLinejoin="round" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />}
                  title="Roles definidos"
                  description="Tres roles con permisos específicos: Estudiante (aprende y practica), Instructor (crea y asigna laboratorios personalizados), Administrador (gestiona la plataforma)."
                />
                <FeatureCard
                  icon={<path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />}
                  title="Examen final"
                  description="Cada laboratorio incluye un examen final que se habilita al completar todas las secciones. Los instructores pueden crear sus propios exámenes de opción múltiple."
                />
                <FeatureCard
                  icon={<path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />}
                  title="Progreso automático"
                  description="Todo se guarda automáticamente. Podés retomar cualquier laboratorio exactamente donde lo dejaste, incluso después de cerrar sesión o ante una caída del sistema."
                />
                <FeatureCard
                  icon={<path strokeLinecap="round" strokeLinejoin="round" d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h9m5.25 0l-3-3m0 0l3-3m-3 3H21" />}
                  title="Invitaciones con control de tiempo"
                  description="Los instructores pueden asignar laboratorios con o sin fecha de vencimiento. Al vencer, el acceso se bloquea automáticamente. Ideal para evaluaciones con plazo definido."
                />
              </div>
            </section>

            {/* ── Stack ── */}
            <section className="mb-12 sm:mb-20">
              <SectionTitle color="var(--signal-cyan)">Stack tecnológico</SectionTitle>

              <div className="chamfer p-5 sm:p-8 mb-6" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
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

            {/* ── Documentación ── */}
            <section className="mb-12 sm:mb-20">
              <SectionTitle color="var(--signal-amber)">Documentación del proyecto</SectionTitle>

              <div className="chamfer p-5 sm:p-8" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
                <p className="text-xs sm:text-sm leading-relaxed mb-4" style={{ color: "var(--text-muted)" }}>
                  El proyecto cuenta con documentación técnica detallada que cubre todos los aspectos
                  del diseño y la implementación:
                </p>
                <div className="grid gap-3" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))" }}>
                  <DocItem title="Historias de usuario" desc="33 HU con criterios de aceptación, prioridades y trazabilidad completa" />
                  <DocItem title="Casos de uso" desc="12 casos de uso detallados con flujos principales, alternativos y excepciones" />
                  <DocItem title="Modelo de dominio" desc="26 entidades, 17 value objects, 7 servicios de dominio, 7 agregados" />
                  <DocItem title="API REST" desc="30+ endpoints documentados con DTOs, validaciones y códigos de error" />
                  <DocItem title="Seguridad" desc="Matriz RBAC, JWT, OAuth2, rate limiting, OWASP Top 10 mapeado" />
                  <DocItem title="Estructura del backend" desc="8 módulos con Clean Architecture: 4 capas por módulo" />
                </div>
              </div>
            </section>

            {/* ── Repositorio ── */}
            <section>
              <ReticleFrame color="var(--signal-amber)" size={16}>
                <div className="chamfer p-5 sm:p-8 text-center" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
                  <h2 className="text-xl sm:text-2xl font-bold uppercase tracking-wide mb-3" style={{ color: "var(--text-heading)" }}>
                    Repositorio
                  </h2>
                  <p className="text-xs sm:text-sm mb-5" style={{ color: "var(--text-muted)" }}>
                    Todo el código fuente está disponible en GitHub. Contribuciones, issues y forks son bienvenidos.
                  </p>
                  <Button asChild size="lg" className="chamfer font-mono text-xs sm:text-sm uppercase tracking-wide">
                    <a href="https://github.com/Stabaresl/PlatLab" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2">
                      <GitHubIcon />
                      github.com/Stabaresl/PlatLab
                    </a>
                  </Button>
                </div>
              </ReticleFrame>
            </section>

            <section className="mt-12 sm:mt-16 mb-4 text-center">
              <Button variant="outline" onClick={() => navigate("/")} className="chamfer font-mono text-xs sm:text-sm uppercase tracking-wide">
                ← Volver al inicio
              </Button>
            </section>
          </div>
        </main>

        <Footer />

        <motion.button
          type="button"
          onClick={scrollToTop}
          aria-label="Volver arriba"
          initial={false}
          animate={{ opacity: showScrollTop ? 1 : 0, y: showScrollTop ? 0 : 16 }}
          className="chamfer-sm fixed bottom-6 sm:bottom-8 right-4 sm:right-8 flex items-center justify-center w-10 sm:w-12 h-10 sm:h-12 cursor-pointer border z-50"
          style={{
            backgroundColor: "var(--surface)",
            borderColor: "var(--border-default)",
            color: "var(--text-muted)",
            pointerEvents: showScrollTop ? "auto" : "none",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = "var(--signal-amber)"
            e.currentTarget.style.color = "var(--signal-amber)"
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = "var(--border-default)"
            e.currentTarget.style.color = "var(--text-muted)"
          }}
        >
          <svg className="w-4 sm:w-5 h-4 sm:h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 15l7-7 7 7" />
          </svg>
        </motion.button>
      </div>
    </div>
  )
}

function SectionTitle({ children, color }: { children: ReactNode; color: string }) {
  return (
    <div className="flex items-center gap-3 mb-6 sm:mb-8">
      <span className="h-px w-6" style={{ backgroundColor: color }} />
      <h2 className="text-lg sm:text-xl font-bold uppercase tracking-widest m-0" style={{ color: "var(--text-heading)" }}>
        {children}
      </h2>
    </div>
  )
}

function GitHubIcon() {
  return (
    <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
    </svg>
  )
}

function FeatureCard({ icon, title, description }: { icon: ReactNode; title: string; description: string }) {
  return (
    <div
      className="chamfer flex flex-col p-4 sm:p-5 transition-colors"
      style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}
      onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--border-amber)" }}
      onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--border-default)" }}
    >
      <div className="chamfer-sm flex items-center justify-center w-10 h-10 mb-3 shrink-0" style={{ backgroundColor: "var(--surface-hover)", color: "var(--signal-amber)" }}>
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          {icon}
        </svg>
      </div>
      <h3 className="text-sm sm:text-base font-bold mb-1.5" style={{ color: "var(--text-heading)" }}>
        {title}
      </h3>
      <p className="text-xs sm:text-sm leading-relaxed m-0" style={{ color: "var(--text-muted)" }}>
        {description}
      </p>
    </div>
  )
}

function TechStackGroup({ title, items }: { title: string; items: { label: string; desc: string }[] }) {
  return (
    <div className="flex flex-col gap-2 sm:gap-3">
      <h4 className="text-xs sm:text-sm font-bold uppercase tracking-wide m-0" style={{ color: "var(--signal-cyan)", fontFamily: "var(--font-mono)" }}>
        {title}
      </h4>
      {items.map((item) => (
        <div key={item.label} className="flex flex-col gap-0.5">
          <span className="text-xs sm:text-sm font-medium" style={{ color: "var(--text-base)" }}>{item.label}</span>
          <span className="text-xs" style={{ color: "var(--text-muted)" }}>{item.desc}</span>
        </div>
      ))}
    </div>
  )
}

function DocItem({ title, desc }: { title: string; desc: string }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs sm:text-sm font-medium" style={{ color: "var(--text-base)" }}>{title}</span>
      <span className="text-xs leading-relaxed" style={{ color: "var(--text-muted)" }}>{desc}</span>
    </div>
  )
}
