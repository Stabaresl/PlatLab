import { useEffect, useRef } from "react"
import useReducedMotion from "../../hooks/useReducedMotion"

// Geometría del isotipo, en un lienzo de 32×32.
const CX = 16
const CY = 16
const RX = 10.5
const RY = 4.2
const INCLINACION = (-28 * Math.PI) / 180
const COS_I = Math.cos(INCLINACION)
const SIN_I = Math.sin(INCLINACION)

/**
 * Isotipo de PlatLAB: un núcleo (el estudiante) con un satélite en órbita
 * (cada laboratorio), dentro del marco de esquinas cortadas de la casa. El
 * satélite pasa por delante y por detrás del núcleo; al pasar el puntero
 * por encima, acelera. Con movimiento reducido queda quieto.
 */
export default function IsoPlatlab({ tamano = 32, activo = false }: { tamano?: number; activo?: boolean }) {
  const reducido = useReducedMotion()
  const atrasRef = useRef<SVGCircleElement>(null)
  const frenteRef = useRef<SVGCircleElement>(null)
  const nucleoRef = useRef<SVGCircleElement>(null)
  const activoRef = useRef(activo)

  useEffect(() => {
    activoRef.current = activo
  }, [activo])

  useEffect(() => {
    let angulo = 0.7
    let velocidad = 0.9
    let previo = performance.now()
    let raf = 0

    const colocar = () => {
      const x0 = Math.cos(angulo) * RX
      const y0 = Math.sin(angulo) * RY
      const x = CX + x0 * COS_I - y0 * SIN_I
      const y = CY + x0 * SIN_I + y0 * COS_I
      const delante = Math.sin(angulo) >= 0
      for (const [el, visible] of [[atrasRef.current, !delante], [frenteRef.current, delante]] as const) {
        if (!el) continue
        el.setAttribute("cx", x.toFixed(2))
        el.setAttribute("cy", y.toFixed(2))
        el.style.opacity = visible ? (delante ? "1" : "0.45") : "0"
      }
      const impulso = (velocidad - 0.9) / 2.6
      nucleoRef.current?.setAttribute("r", (4.3 + impulso * 0.7).toFixed(2))
    }

    if (reducido) {
      colocar()
      return
    }
    const paso = (ahora: number) => {
      raf = requestAnimationFrame(paso)
      const dt = Math.min((ahora - previo) / 1000, 0.05)
      previo = ahora
      const objetivo = activoRef.current ? 3.5 : 0.9
      velocidad += (objetivo - velocidad) * Math.min(dt * 5, 1)
      angulo = (angulo + velocidad * dt) % (Math.PI * 2)
      colocar()
    }
    raf = requestAnimationFrame(paso)
    return () => cancelAnimationFrame(raf)
  }, [reducido])

  return (
    <svg width={tamano} height={tamano} viewBox="0 0 32 32" aria-hidden="true" className="shrink-0" style={{ overflow: "visible" }}>
      <path d="M7 1 H31 V25 L25 31 H1 V7 Z" style={{ fill: "var(--surface)", stroke: "var(--signal-amber)", strokeWidth: 1.5 }} />
      <circle ref={atrasRef} r={1.6} style={{ fill: "var(--signal-cyan)" }} />
      <ellipse
        cx={CX}
        cy={CY}
        rx={RX}
        ry={RY}
        transform={`rotate(-28 ${CX} ${CY})`}
        style={{ fill: "none", stroke: "var(--signal-cyan)", strokeWidth: 1, opacity: 0.55 }}
      />
      <circle ref={nucleoRef} cx={CX} cy={CY} r={4.3} style={{ fill: "var(--signal-amber)" }} />
      <circle ref={frenteRef} r={2} style={{ fill: "var(--signal-cyan)" }} />
    </svg>
  )
}
