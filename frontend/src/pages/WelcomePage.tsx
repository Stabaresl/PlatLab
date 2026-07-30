import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import Navbar from "../components/Navbar"
import Footer from "../components/Footer"
import ScanlineOverlay from "../components/ScanlineOverlay"
import TerminalTyper from "../components/TerminalTyper"
import CountUpStat from "../components/CountUpStat"
import CyberGrid from "../components/CyberGrid"
import ReticleFrame from "../components/ReticleFrame"
import MouseGlow, { trackGlow, untrackGlow } from "../components/MouseGlow"
import StatusDot from "../components/StatusDot"
import { Button } from "../components/ui/button"
import grimBg from "../assets/grim.png"
import termBg from "../assets/term.png"

const STEPS = [
  {
    n: "01",
    title: "Registrate",
    desc: "Creá tu cuenta como estudiante en segundos, o pedí que te inviten como instructor.",
  },
  {
    n: "02",
    title: "Elegí un laboratorio",
    desc: "Explorá el catálogo por dificultad y tema, o aceptá una invitación de tu instructor.",
  },
  {
    n: "03",
    title: "Resolvé desafíos reales",
    desc: "Avanzá sección por sección, capturá flags y pedí pistas progresivas si te trabás.",
  },
  {
    n: "04",
    title: "Rendí el examen",
    desc: "Al completar todas las secciones se habilita el examen final con corrección automática.",
  },
]

const FEATURES = [
  {
    title: "Laboratorios interactivos",
    desc: "Entornos controlados con secciones teóricas y prácticas, flags que validan cada paso.",
    icon: (
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
    ),
  },
  {
    title: "Pistas progresivas",
    desc: "Pista tras 5 intentos fallidos, paso a paso completo tras 15. Aprendés, no te frustrás.",
    icon: <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />,
  },
  {
    title: "Roles con permisos claros",
    desc: "Estudiante, Instructor y Administrador, cada uno con su propio panel y capacidades.",
    icon: (
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
    ),
  },
  {
    title: "Progreso automático",
    desc: "Todo se guarda al instante. Retomá cualquier laboratorio exactamente donde lo dejaste.",
    icon: (
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
    ),
  },
]

const TICKER = "SISTEMA: OPERATIVO // 3 ROLES ACTIVOS // 8 MÓDULOS CARGADOS // PROGRESO: PERSISTENTE // OWASP TOP 10 CUBIERTO //"

export default function WelcomePage() {
  const navigate = useNavigate()
  const [authed, setAuthed] = useState(false)

  useEffect(() => {
    setAuthed(!!localStorage.getItem("token"))
  }, [])

  return (
    <div className="min-h-screen flex flex-col" style={{ color: "var(--text-base)", backgroundColor: "var(--canvas)" }}>
      {/* ═══ Ticker de estado ═══ */}
      <div
        className="w-full overflow-hidden whitespace-nowrap select-none"
        style={{ backgroundColor: "var(--canvas-raised)", borderBottom: "1px solid var(--border-hairline)" }}
        aria-hidden="true"
      >
        <div
          className="inline-block py-1.5 text-[10px] tracking-widest"
          style={{ fontFamily: "var(--font-mono)", color: "var(--signal-amber)", animation: "grid-drift 26s linear infinite" }}
        >
          <span className="px-4">{TICKER}</span>
          <span className="px-4">{TICKER}</span>
        </div>
      </div>

      {/* ═══ HERO ═══ */}
      <div className="relative">
        <div
          className="absolute inset-0"
          style={{ backgroundImage: `url(${grimBg})`, backgroundSize: "cover", backgroundPosition: "center", backgroundRepeat: "no-repeat", opacity: 0.5 }}
        />
        <div className="absolute inset-0" style={{ backgroundColor: "rgba(8,9,12,0.62)", backdropFilter: "blur(8px)", WebkitBackdropFilter: "blur(8px)" }} />
        <CyberGrid opacity={0.16} color="255,176,32" />

        <div className="relative z-10">
          <Navbar variant="transparent" />

          <section
            onMouseMove={trackGlow}
            onMouseLeave={untrackGlow}
            className="relative flex flex-col lg:flex-row items-center w-full px-4 sm:px-6 md:px-8 lg:px-12 py-10 sm:py-14 md:py-20 gap-6 sm:gap-8 md:gap-12 lg:gap-[80px]"
          >
            <MouseGlow color="255,176,32" size={520} opacity={0.14} />

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="relative z-10 flex flex-col items-center lg:items-start w-full lg:w-1/2 gap-4 sm:gap-5 md:gap-6 lg:gap-8 text-center lg:text-left"
            >
              <span
                className="text-[11px] sm:text-xs px-3 py-1.5 chamfer-sm"
                style={{ backgroundColor: "rgba(56,214,245,0.08)", color: "var(--signal-cyan)", border: "1px solid var(--border-cyan)", fontFamily: "var(--font-mono)" }}
              >
                <TerminalTyper />
              </span>

              <h1 className="text-display text-3xl sm:text-4xl md:text-5xl font-black uppercase leading-tight" style={{ color: "var(--text-heading)", letterSpacing: "0.02em" }}>
                Aprende seguridad
                <br />
                informática
              </h1>

              <p className="text-sm sm:text-base md:text-lg leading-relaxed" style={{ maxWidth: "560px", lineHeight: "1.7" }}>
                Plataforma de laboratorios interactivos de hacking ético.
                Poné a prueba tus habilidades en entornos reales controlados,
                aprendé de tus errores y convertite en un experto en
                ciberseguridad.
              </p>

              <div className="flex items-center gap-3 sm:gap-4">
                {authed ? (
                  <Button size="lg" onClick={() => navigate("/dashboard")} className="chamfer font-mono text-xs sm:text-sm uppercase tracking-wide px-6 sm:px-8">
                    Ir a mi Dashboard
                  </Button>
                ) : (
                  <Button size="lg" onClick={() => navigate("/login")} className="chamfer font-mono text-xs sm:text-sm uppercase tracking-wide px-6 sm:px-8">
                    Iniciar sesión
                  </Button>
                )}
                <Button size="lg" variant="outline" onClick={() => navigate("/about")} className="chamfer font-mono text-xs sm:text-sm uppercase tracking-wide px-6 sm:px-8">
                  Conocé más
                </Button>
              </div>
            </motion.div>

            <div className="relative z-10 flex-1 flex items-center justify-center w-full lg:w-auto">
              <motion.div
                initial={{ opacity: 0, scale: 0.94 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.55, ease: "easeOut", delay: 0.15 }}
                className="w-full max-w-[650px]"
              >
                <ReticleFrame color="var(--signal-amber)" size={20} thickness={2}>
                  <div className="relative overflow-hidden w-full aspect-[650/371]" style={{ border: "1px solid var(--border-default)" }}>
                    <div
                      className="absolute inset-0"
                      style={{ backgroundImage: `url(${termBg})`, backgroundSize: "cover", backgroundPosition: "center", backgroundRepeat: "no-repeat" }}
                    />
                    <div className="absolute inset-0" style={{ backgroundColor: "rgba(8,9,12,0.35)" }} />
                    <ScanlineOverlay />
                    <div className="absolute top-0 left-0 right-0 flex items-center gap-1.5 px-3 py-2" style={{ backgroundColor: "rgba(8,9,12,0.55)", borderBottom: "1px solid var(--border-hairline)" }}>
                      <span className="w-2 h-2" style={{ backgroundColor: "var(--signal-red)" }} />
                      <span className="w-2 h-2" style={{ backgroundColor: "var(--signal-amber)" }} />
                      <span className="w-2 h-2" style={{ backgroundColor: "var(--signal-green)" }} />
                      <span className="ml-2 text-[10px]" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>lab_session --status</span>
                    </div>
                    <div className="relative z-10 flex items-center justify-center w-full h-full px-6 sm:px-8">
                      <p className="text-sm sm:text-base md:text-lg font-medium text-center" style={{ color: "var(--text-heading)", fontFamily: "var(--font-mono)" }}>
                        Explorá, aprendé y dominá
                        <br />
                        la ciberseguridad
                      </p>
                    </div>
                  </div>
                </ReticleFrame>
              </motion.div>
            </div>
          </section>
        </div>
      </div>

      {/* ═══ EN NÚMEROS ═══ */}
      <section className="w-full px-4 sm:px-6 md:px-8 lg:px-12 py-10 sm:py-14" style={{ borderTop: "1px solid var(--border-default)", borderBottom: "1px solid var(--border-default)" }}>
        <div className="mx-auto grid grid-cols-2 sm:grid-cols-4 gap-6 sm:gap-8" style={{ maxWidth: "1000px" }}>
          <CountUpStat value={3} label="Roles con RBAC" delay={0} />
          <CountUpStat value={8} label="Módulos del backend" delay={100} />
          <CountUpStat value={100} suffix="%" label="Progreso guardado" delay={200} />
          <CountUpStat value={10} label="OWASP Top cubierto" delay={300} />
        </div>
      </section>

      {/* ═══ CÓMO FUNCIONA ═══ */}
      <section
        onMouseMove={trackGlow}
        onMouseLeave={untrackGlow}
        className="relative w-full px-4 sm:px-6 md:px-8 lg:px-12 py-12 sm:py-20"
      >
        <MouseGlow color="255,176,32" size={480} opacity={0.08} />
        <div className="relative z-10 mx-auto" style={{ maxWidth: "1100px" }}>
          <div className="flex items-center gap-3 mb-8 sm:mb-12 justify-center">
            <span className="h-px w-8" style={{ backgroundColor: "var(--signal-amber)" }} />
            <h2 className="text-xl sm:text-2xl font-bold uppercase tracking-widest text-center" style={{ color: "var(--text-heading)" }}>
              Cómo funciona
            </h2>
            <span className="h-px w-8" style={{ backgroundColor: "var(--signal-amber)" }} />
          </div>
          <div className="grid gap-4 sm:gap-6" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
            {STEPS.map((step, i) => (
              <motion.div
                key={step.n}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-60px" }}
                transition={{ duration: 0.4, delay: i * 0.08 }}
                className="chamfer flex flex-col gap-2 p-5"
                style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}
              >
                <span className="text-display text-xs font-bold" style={{ color: "var(--signal-amber)" }}>
                  {step.n}
                </span>
                <h3 className="text-base font-bold m-0" style={{ color: "var(--text-heading)" }}>
                  {step.title}
                </h3>
                <p className="text-xs sm:text-sm leading-relaxed m-0" style={{ color: "var(--text-muted)" }}>
                  {step.desc}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ CARACTERÍSTICAS ═══ */}
      <section
        onMouseMove={trackGlow}
        onMouseLeave={untrackGlow}
        className="relative w-full px-4 sm:px-6 md:px-8 lg:px-12 py-12 sm:py-20"
        style={{ backgroundColor: "var(--surface)" }}
      >
        <MouseGlow color="56,214,245" size={480} opacity={0.08} />
        <div className="relative z-10 mx-auto" style={{ maxWidth: "1100px" }}>
          <div className="flex items-center gap-3 mb-8 sm:mb-12 justify-center">
            <span className="h-px w-8" style={{ backgroundColor: "var(--signal-cyan)" }} />
            <h2 className="text-xl sm:text-2xl font-bold uppercase tracking-widest text-center" style={{ color: "var(--text-heading)" }}>
              Por qué GAIA
            </h2>
            <span className="h-px w-8" style={{ backgroundColor: "var(--signal-cyan)" }} />
          </div>
          <div className="grid gap-4 sm:gap-6" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))" }}>
            {FEATURES.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-60px" }}
                transition={{ duration: 0.4, delay: i * 0.08 }}
                className="chamfer flex flex-col p-5"
                style={{ backgroundColor: "var(--canvas)", border: "1px solid var(--border-default)" }}
              >
                <div className="chamfer-sm flex items-center justify-center w-10 h-10 mb-3 shrink-0" style={{ backgroundColor: "var(--surface-hover)", color: "var(--signal-cyan)" }}>
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    {f.icon}
                  </svg>
                </div>
                <h3 className="text-sm sm:text-base font-bold mb-1.5" style={{ color: "var(--text-heading)" }}>
                  {f.title}
                </h3>
                <p className="text-xs sm:text-sm leading-relaxed m-0" style={{ color: "var(--text-muted)" }}>
                  {f.desc}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ CTA FINAL ═══ */}
      <section className="w-full px-4 sm:px-6 md:px-8 lg:px-12 py-12 sm:py-20">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-60px" }}
          transition={{ duration: 0.4 }}
          className="mx-auto"
          style={{ maxWidth: "800px" }}
        >
          <ReticleFrame color="var(--signal-amber)" size={18}>
            <div
              onMouseMove={trackGlow}
              onMouseLeave={untrackGlow}
              className="relative overflow-hidden flex flex-col items-center gap-4 p-8 sm:p-12 text-center"
              style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}
            >
              <CyberGrid opacity={0.2} />
              <MouseGlow color="255,176,32" size={420} opacity={0.16} />
              {authed ? (
                <>
                  <StatusDot variant="active" label="Sesión activa" pulse className="relative z-10" />
                  <h2 className="relative z-10 text-xl sm:text-2xl font-bold uppercase tracking-wide m-0" style={{ color: "var(--text-heading)" }}>
                    ¿Listo para el próximo laboratorio?
                  </h2>
                  <p className="relative z-10 text-sm m-0" style={{ color: "var(--text-muted)" }}>
                    Explorá el catálogo completo y elegí tu siguiente desafío.
                  </p>
                  <Button size="lg" onClick={() => navigate("/laboratorios")} className="relative z-10 chamfer font-mono text-xs sm:text-sm uppercase tracking-wide px-6 sm:px-8">
                    Ver catálogo de laboratorios
                  </Button>
                </>
              ) : (
                <>
                  <StatusDot variant="active" label="Registro abierto" pulse className="relative z-10" />
                  <h2 className="relative z-10 text-xl sm:text-2xl font-bold uppercase tracking-wide m-0" style={{ color: "var(--text-heading)" }}>
                    ¿Listo para poner a prueba tus habilidades?
                  </h2>
                  <p className="relative z-10 text-sm m-0" style={{ color: "var(--text-muted)" }}>
                    Creá tu cuenta gratis y empezá a resolver laboratorios reales hoy mismo.
                  </p>
                  <Button size="lg" onClick={() => navigate("/signup")} className="relative z-10 chamfer font-mono text-xs sm:text-sm uppercase tracking-wide px-6 sm:px-8">
                    Crear cuenta gratis
                  </Button>
                </>
              )}
            </div>
          </ReticleFrame>
        </motion.div>
      </section>

      <Footer />
    </div>
  )
}
