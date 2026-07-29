import { useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import Navbar from "../components/Navbar"
import Footer from "../components/Footer"
import ScanlineOverlay from "../components/ScanlineOverlay"
import TerminalTyper from "../components/TerminalTyper"
import CountUpStat from "../components/CountUpStat"
import MatrixRain from "../components/MatrixRain"
import CyberGrid from "../components/CyberGrid"
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

export default function WelcomePage() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen flex flex-col" style={{ color: "var(--text-base)", backgroundColor: "var(--bg-canvas)" }}>
      {/* ═══════════════════════════════════════════
          HERO — fondo grim.png con blur
          ═══════════════════════════════════════════ */}
      <div className="relative">
        <div
          className="absolute inset-0"
          style={{
            backgroundImage: `url(${grimBg})`,
            backgroundSize: "cover",
            backgroundPosition: "center",
            backgroundRepeat: "no-repeat",
          }}
        />
        <MatrixRain opacity={0.1} />
        <div
          className="absolute inset-0"
          style={{
            backgroundColor: "rgba(15, 17, 23, 0.55)",
            backdropFilter: "blur(8px)",
            WebkitBackdropFilter: "blur(8px)",
          }}
        />

        <div className="relative z-10">
          <Navbar variant="transparent" />

          <section
            className="
              flex flex-col lg:flex-row items-center
              w-full
              px-4 sm:px-6 md:px-8 lg:px-12
              py-10 sm:py-14 md:py-20
              gap-6 sm:gap-8 md:gap-12 lg:gap-[80px]
            "
          >
            {/* Columna izquierda: texto */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="flex flex-col items-center lg:items-start w-full lg:w-1/2 gap-4 sm:gap-5 md:gap-6 lg:gap-8 text-center lg:text-left"
            >
              <span
                className="text-xs px-3 py-1 rounded-full"
                style={{
                  backgroundColor: "rgba(59,130,246,0.12)",
                  color: "var(--accent-primary)",
                  border: "1px solid rgba(59,130,246,0.3)",
                  fontFamily: "var(--font-mono)",
                }}
              >
                <TerminalTyper />
              </span>

              <h1
                className="text-3xl sm:text-4xl md:text-5xl font-semibold leading-tight"
                style={{ color: "var(--text-heading)", fontFamily: "var(--font-heading)" }}
              >
                Aprende seguridad
                <br />
                informática
              </h1>

              <p className="text-sm sm:text-base md:text-lg leading-relaxed" style={{ maxWidth: "560px", lineHeight: "1.7" }}>
                Plataforma de laboratorios interactivos de hacking ético.
                Pon a prueba tus habilidades en entornos reales controlados,
                aprende de tus errores y conviértete en un experto en
                ciberseguridad.
              </p>

              <div className="flex items-center gap-3 sm:gap-4">
                <button
                  type="button"
                  onClick={() => navigate("/login")}
                  className="px-5 sm:px-6 md:px-8 py-2 sm:py-2.5 md:py-3 rounded text-xs sm:text-sm font-semibold cursor-pointer border-none transition-opacity hover:opacity-80"
                  style={{ backgroundColor: "var(--text-heading)", color: "#0F1117", fontFamily: "var(--font-mono)" }}
                >
                  Sign In
                </button>

                <button
                  type="button"
                  onClick={() => navigate("/about")}
                  className="px-5 sm:px-6 md:px-8 py-2 sm:py-2.5 md:py-3 rounded text-xs sm:text-sm font-semibold cursor-pointer border transition-colors"
                  style={{ backgroundColor: "transparent", borderColor: "var(--ui-border-default)", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
                  onMouseEnter={(e) => { e.currentTarget.style.borderColor = "var(--text-base)"; e.currentTarget.style.color = "var(--text-base)" }}
                  onMouseLeave={(e) => { e.currentTarget.style.borderColor = "var(--ui-border-default)"; e.currentTarget.style.color = "var(--text-muted)" }}
                >
                  know more
                </button>
              </div>
            </motion.div>

            {/* Columna derecha: card con term.png + borde dorado + scanline */}
            <div className="flex-1 flex items-center justify-center w-full lg:w-auto">
              <motion.div
                initial={{ opacity: 0, scale: 0.94 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.55, ease: "easeOut", delay: 0.15 }}
                whileHover={{ scale: 1.015 }}
                className="relative overflow-hidden w-full max-w-[650px] aspect-[650/371]"
                style={{ borderRadius: "17px", border: "2px solid var(--ui-border-gold)", boxShadow: "0 0 0 1px rgba(0,0,0,0.2)" }}
              >
                <div
                  className="absolute inset-0"
                  style={{ backgroundImage: `url(${termBg})`, backgroundSize: "cover", backgroundPosition: "center", backgroundRepeat: "no-repeat" }}
                />
                <div
                  className="absolute inset-0"
                  style={{ backgroundColor: "rgba(15, 17, 23, 0.3)", backdropFilter: "blur(1px)", WebkitBackdropFilter: "blur(1px)" }}
                />
                <ScanlineOverlay />
                <div className="relative z-10 flex items-center justify-center w-full h-full px-6 sm:px-8">
                  <p
                    className="text-sm sm:text-base md:text-lg font-medium text-center"
                    style={{ color: "var(--text-heading)", fontFamily: "var(--font-heading)" }}
                  >
                    Explora, aprende y domina
                    <br />
                    la ciberseguridad
                  </p>
                </div>
              </motion.div>
            </div>
          </section>
        </div>
      </div>

      {/* ═══════════════════════════════════════════
          EN NÚMEROS
          ═══════════════════════════════════════════ */}
      <section className="w-full px-4 sm:px-6 md:px-8 lg:px-12 py-10 sm:py-14" style={{ borderTop: "1px solid var(--ui-border-default)", borderBottom: "1px solid var(--ui-border-default)" }}>
        <div className="mx-auto grid grid-cols-2 sm:grid-cols-4 gap-6 sm:gap-8" style={{ maxWidth: "1000px" }}>
          <CountUpStat value={3} label="Roles con RBAC" delay={0} />
          <CountUpStat value={8} label="Módulos del backend" delay={100} />
          <CountUpStat value={100} suffix="%" label="Progreso guardado" delay={200} />
          <CountUpStat value={10} label="OWASP Top cubierto" delay={300} />
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          CÓMO FUNCIONA
          ═══════════════════════════════════════════ */}
      <section className="w-full px-4 sm:px-6 md:px-8 lg:px-12 py-12 sm:py-20">
        <div className="mx-auto" style={{ maxWidth: "1100px" }}>
          <h2
            className="text-2xl sm:text-3xl font-semibold mb-8 sm:mb-12 text-center"
            style={{ color: "var(--text-heading)", fontFamily: "var(--font-heading)" }}
          >
            Cómo funciona
          </h2>
          <div className="grid gap-4 sm:gap-6" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))" }}>
            {STEPS.map((step, i) => (
              <motion.div
                key={step.n}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-60px" }}
                transition={{ duration: 0.4, delay: i * 0.08 }}
                className="flex flex-col gap-2 p-5 rounded-lg"
                style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--ui-border-default)" }}
              >
                <span className="text-xs font-bold" style={{ color: "var(--ui-border-gold)", fontFamily: "var(--font-mono)" }}>
                  {step.n}
                </span>
                <h3 className="text-base font-semibold m-0" style={{ color: "var(--text-heading)", fontFamily: "var(--font-heading)" }}>
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

      {/* ═══════════════════════════════════════════
          CARACTERÍSTICAS
          ═══════════════════════════════════════════ */}
      <section className="w-full px-4 sm:px-6 md:px-8 lg:px-12 py-12 sm:py-20" style={{ backgroundColor: "var(--bg-surface)" }}>
        <div className="mx-auto" style={{ maxWidth: "1100px" }}>
          <h2
            className="text-2xl sm:text-3xl font-semibold mb-8 sm:mb-12 text-center"
            style={{ color: "var(--text-heading)", fontFamily: "var(--font-heading)" }}
          >
            Por qué GAIA
          </h2>
          <div className="grid gap-4 sm:gap-6" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))" }}>
            {FEATURES.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-60px" }}
                transition={{ duration: 0.4, delay: i * 0.08 }}
                className="flex flex-col p-5 rounded-lg"
                style={{ backgroundColor: "var(--bg-canvas)", border: "1px solid var(--ui-border-default)" }}
              >
                <div
                  className="flex items-center justify-center w-10 h-10 rounded-lg mb-3 shrink-0"
                  style={{ backgroundColor: "var(--bg-surface-hover)", color: "var(--accent-primary)" }}
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    {f.icon}
                  </svg>
                </div>
                <h3 className="text-sm sm:text-base font-medium mb-1.5" style={{ color: "var(--text-heading)", fontFamily: "var(--font-heading)" }}>
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

      {/* ═══════════════════════════════════════════
          CTA FINAL
          ═══════════════════════════════════════════ */}
      <section className="w-full px-4 sm:px-6 md:px-8 lg:px-12 py-12 sm:py-20">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-60px" }}
          transition={{ duration: 0.4 }}
          className="relative overflow-hidden mx-auto flex flex-col items-center gap-4 p-8 sm:p-12 rounded-lg text-center"
          style={{ maxWidth: "800px", backgroundColor: "var(--bg-surface)", border: "1px solid var(--ui-border-gold)" }}
        >
          <CyberGrid opacity={0.25} />
          <h2 className="relative z-10 text-xl sm:text-2xl font-semibold m-0" style={{ color: "var(--text-heading)", fontFamily: "var(--font-heading)" }}>
            ¿Listo para poner a prueba tus habilidades?
          </h2>
          <p className="relative z-10 text-sm m-0" style={{ color: "var(--text-muted)" }}>
            Creá tu cuenta gratis y empezá a resolver laboratorios reales hoy mismo.
          </p>
          <button
            type="button"
            onClick={() => navigate("/signup")}
            className="relative z-10 px-6 sm:px-8 py-2.5 sm:py-3 rounded text-sm font-semibold cursor-pointer border-none transition-opacity hover:opacity-85"
            style={{ backgroundColor: "var(--text-heading)", color: "#0F1117", fontFamily: "var(--font-mono)" }}
          >
            Crear cuenta gratis
          </button>
        </motion.div>
      </section>

      <Footer />
    </div>
  )
}
