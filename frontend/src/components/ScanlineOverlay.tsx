import { useEffect, useRef } from "react"
import { animate } from "animejs"
import useReducedMotion from "../hooks/useReducedMotion"

// Barrido de escaneo sobre un panel — anime.js. Recolorizado a cian (dato
// "en análisis") en vez del azul genérico anterior. Con reduced-motion se
// reemplaza por una franja estática de baja opacidad (misma lectura, sin
// movimiento).
export default function ScanlineOverlay() {
  const ref = useRef<HTMLDivElement>(null)
  const reduced = useReducedMotion()

  useEffect(() => {
    if (!ref.current || reduced) return
    const animation = animate(ref.current, {
      translateY: ["-20%", "420%"],
      opacity: [0, 0.55, 0],
      duration: 2800,
      ease: "linear",
      loop: true,
    })
    return () => {
      animation.pause()
    }
  }, [reduced])

  if (reduced) {
    return (
      <div
        className="absolute left-0 right-0 top-1/2 h-px pointer-events-none"
        style={{ backgroundColor: "rgba(56,214,245,0.25)" }}
        aria-hidden="true"
      />
    )
  }

  return (
    <div
      ref={ref}
      className="absolute left-0 right-0 h-10 pointer-events-none"
      style={{
        background: "linear-gradient(180deg, transparent, rgba(56,214,245,0.4), transparent)",
      }}
      aria-hidden="true"
    />
  )
}
