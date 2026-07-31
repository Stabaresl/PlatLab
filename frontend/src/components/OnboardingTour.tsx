import { useEffect, useState } from "react"
import { createPortal } from "react-dom"
import { useLocation } from "react-router-dom"
import { motion, AnimatePresence } from "framer-motion"
import useReducedMotion from "../hooks/useReducedMotion"
import { Button } from "./ui/button"

interface TourStep {
  target: string
  title: string
  body: string
  // Si se define, el paso solo se muestra cuando el rol activo coincide.
  roleRequerido?: string
}

const STEPS: TourStep[] = [
  {
    target: "logo",
    title: "¡Bienvenido a GAIA!",
    body: "Te mostramos rápido dónde está todo — son unos segundos, y podés saltarlo cuando quieras.",
  },
  {
    target: "nav-laboratorios",
    title: "Catálogo de Laboratorios",
    body: "Todos los laboratorios disponibles para practicar, con filtro por dificultad y búsqueda por tema.",
  },
  {
    target: "nav-roadmap",
    title: "Roadmap",
    body: "Un camino guiado de laboratorios curados por el equipo de GAIA, del más fácil al más difícil — completá uno para desbloquear el siguiente.",
  },
  {
    target: "nav-bell",
    title: "Notificaciones",
    body: "Acá te avisamos invitaciones a laboratorios, cambios de estado, y logros que vayas desbloqueando.",
  },
  {
    target: "nav-avatar",
    title: "Tu Perfil",
    body: "Ganás XP y desbloqueás logros, títulos y cosméticos completando laboratorios. Personalizá tu avatar acá.",
    roleRequerido: "estudiante",
  },
  {
    target: "nav-dashboard",
    title: "Tu Dashboard",
    body: "El punto de partida según tu rol — laboratorios, estudiantes, o el estado general de la plataforma.",
  },
]

const FLAG_JUST_REGISTERED = "just_registered"
const FLAG_ONBOARDING_SEEN = "onboarding_seen"

function waitForElement(selector: string, onFound: (el: Element) => void, intentos = 20) {
  const el = document.querySelector(selector)
  if (el) {
    onFound(el)
    return
  }
  if (intentos <= 0) return
  setTimeout(() => waitForElement(selector, onFound, intentos - 1), 100)
}

// Tour de bienvenida — burbujas ancladas a elementos reales del Navbar
// (vía atributos `data-tour`, compartidos en toda la app ya que el
// Navbar se monta en cada página) con un backdrop que resalta el
// elemento activo. Se dispara una única vez, justo después de que
// `SignUpPage.tsx` deja la marca `just_registered` en localStorage —
// sin librería de tour nueva, framer-motion (ya instalado) alcanza,
// mismo criterio que usamos para el drag-and-drop del roadmap.
export default function OnboardingTour() {
  const location = useLocation()
  const reduced = useReducedMotion()
  const [active, setActive] = useState(false)
  const [stepIndex, setStepIndex] = useState(0)
  const [rect, setRect] = useState<DOMRect | null>(null)

  const role = localStorage.getItem("role")
  const steps = STEPS.filter((s) => !s.roleRequerido || s.roleRequerido === role)

  useEffect(() => {
    if (localStorage.getItem(FLAG_JUST_REGISTERED)) {
      localStorage.removeItem(FLAG_JUST_REGISTERED)
      setStepIndex(0)
      setActive(true)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname])

  useEffect(() => {
    if (!active) return
    const step = steps[stepIndex]
    if (!step) return
    setRect(null)
    waitForElement(`[data-tour="${step.target}"]`, (el) => setRect(el.getBoundingClientRect()))
  }, [active, stepIndex, steps])

  useEffect(() => {
    if (!active) return
    const onReposition = () => {
      const step = steps[stepIndex]
      if (!step) return
      const el = document.querySelector(`[data-tour="${step.target}"]`)
      if (el) setRect(el.getBoundingClientRect())
    }
    window.addEventListener("resize", onReposition)
    return () => window.removeEventListener("resize", onReposition)
  }, [active, stepIndex, steps])

  const finish = () => {
    localStorage.setItem(FLAG_ONBOARDING_SEEN, "true")
    setActive(false)
  }

  const next = () => {
    if (stepIndex >= steps.length - 1) finish()
    else setStepIndex((i) => i + 1)
  }
  const prev = () => setStepIndex((i) => Math.max(0, i - 1))

  if (!active || steps.length === 0) return null

  const step = steps[stepIndex]
  const bubbleTop = rect ? Math.min(rect.bottom + 14, window.innerHeight - 200) : window.innerHeight / 2 - 80
  const bubbleLeft = rect
    ? Math.max(16, Math.min(rect.left, window.innerWidth - 336))
    : Math.max(16, window.innerWidth / 2 - 160)

  return createPortal(
    <div style={{ position: "fixed", inset: 0, zIndex: 2000 }}>
      <div
        onClick={finish}
        aria-hidden="true"
        style={{ position: "fixed", inset: 0, backgroundColor: "rgba(5,6,8,0.72)" }}
      />

      {rect && (
        <motion.div
          initial={reduced ? { opacity: 0 } : { opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.2 }}
          style={{
            position: "fixed",
            top: rect.top - 6,
            left: rect.left - 6,
            width: rect.width + 12,
            height: rect.height + 12,
            border: "2px solid var(--signal-amber)",
            boxShadow: "0 0 16px rgba(255,176,32,0.5)",
            pointerEvents: "none",
          }}
        />
      )}

      <AnimatePresence mode="wait">
        <motion.div
          key={stepIndex}
          initial={reduced ? { opacity: 0 } : { opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="chamfer p-4 sm:p-5"
          style={{
            position: "fixed",
            top: bubbleTop,
            left: bubbleLeft,
            width: 320,
            maxWidth: "calc(100vw - 32px)",
            backgroundColor: "var(--canvas-raised)",
            border: "1px solid var(--border-amber)",
            boxShadow: "0 16px 40px rgba(0,0,0,0.6)",
          }}
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex gap-1">
              {steps.map((_, i) => (
                <span
                  key={i}
                  className="w-1.5 h-1.5"
                  style={{ backgroundColor: i === stepIndex ? "var(--signal-amber)" : "var(--border-default)" }}
                />
              ))}
            </div>
            <button
              type="button"
              onClick={finish}
              className="text-[10px] uppercase tracking-wide cursor-pointer border-none bg-transparent px-0"
              style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}
            >
              Saltar
            </button>
          </div>

          <h3 className="text-sm font-bold uppercase tracking-wide mb-1.5 m-0" style={{ color: "var(--text-heading)" }}>
            {step.title}
          </h3>
          <p className="text-xs leading-relaxed mb-4" style={{ color: "var(--text-muted)" }}>
            {step.body}
          </p>

          <div className="flex items-center justify-between gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={stepIndex === 0}
              onClick={prev}
              className="chamfer-sm font-mono text-[10px] uppercase tracking-wide"
            >
              Anterior
            </Button>
            <Button type="button" size="sm" onClick={next} className="chamfer-sm font-mono text-[10px] uppercase tracking-wide">
              {stepIndex >= steps.length - 1 ? "Listo" : "Siguiente"}
            </Button>
          </div>
        </motion.div>
      </AnimatePresence>
    </div>,
    document.body,
  )
}
