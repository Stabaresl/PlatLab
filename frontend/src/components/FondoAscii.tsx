import { useEffect, useRef } from "react"
import { createPortal } from "react-dom"

// Mismos caracteres que la lluvia del encabezado (MatrixRain): el fondo de la
// página y la tarjeta del título se leen como la misma pantalla.
const CARACTERES = "01アイウエオカキクケコサシスセソABCDEF{}<>/\\;:$#%&*01010011"
const TAM = 15
const CADA_MS = 70
const RADIO_PUNTERO = 170

/**
 * Fondo ASCII de página completa: columnas de caracteres que caen, muy
 * tenues, con un halo más brillante alrededor del puntero.
 *
 * - Un solo canvas fijo del tamaño de la ventana (no del alto de la página):
 *   el costo no crece con páginas largas.
 * - Se apaga con la pestaña oculta; con "reducir movimiento" queda un cuadro quieto.
 * - Va en un portal a <body> con z-index 0: por encima del fondo de la página
 *   y por debajo del contenido (z-10), sin depender de transformaciones de la ruta.
 * - El centro se atenúa con una máscara para no competir con los paneles.
 */
export default function FondoAscii({ color = "255,176,32", intensidad = 1 }: { color?: string; intensidad?: number }) {
  const ref = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const lienzo = ref.current
    const ctx = lienzo?.getContext("2d")
    if (!lienzo || !ctx) return
    const quieto = window.matchMedia("(prefers-reduced-motion: reduce)").matches

    let ancho = 0
    let alto = 0
    let gotas: number[] = []
    const puntero = { x: -9999, y: -9999 }

    const ajustar = () => {
      ancho = window.innerWidth
      alto = window.innerHeight
      lienzo.width = ancho
      lienzo.height = alto
      const columnas = Math.ceil(ancho / TAM)
      gotas = Array.from({ length: columnas }, () => -Math.floor((Math.random() * alto) / TAM))
      ctx.font = `${TAM}px "JetBrains Mono", "Fira Code", monospace`
      if (quieto) cuadroQuieto()
    }

    const alfaPara = (x: number, y: number, base: number) => {
      const d = Math.hypot(x - puntero.x, y - puntero.y)
      const extra = d < RADIO_PUNTERO ? (1 - d / RADIO_PUNTERO) * 0.38 : 0
      return Math.min((base + extra) * intensidad, 0.75)
    }

    const cuadroQuieto = () => {
      ctx.clearRect(0, 0, ancho, alto)
      for (let x = 0; x < ancho; x += TAM) {
        for (let y = TAM; y < alto; y += TAM * 1.6) {
          if (Math.random() > 0.22) continue
          ctx.fillStyle = `rgba(${color}, ${(0.05 + Math.random() * 0.08) * intensidad})`
          ctx.fillText(CARACTERES[Math.floor(Math.random() * CARACTERES.length)], x, y)
        }
      }
    }

    ajustar()
    window.addEventListener("resize", ajustar)
    if (quieto) {
      return () => window.removeEventListener("resize", ajustar)
    }

    const alMover = (e: PointerEvent) => {
      puntero.x = e.clientX
      puntero.y = e.clientY
    }
    const alSalir = () => {
      puntero.x = -9999
      puntero.y = -9999
    }
    window.addEventListener("pointermove", alMover, { passive: true })
    document.addEventListener("pointerleave", alSalir)

    let raf = 0
    let previo = 0
    const dibujar = (t: number) => {
      raf = requestAnimationFrame(dibujar)
      if (document.hidden || t - previo < CADA_MS) return
      previo = t
      // Desvanece lo ya dibujado hacia transparente (no hacia un color): el
      // fondo real de la página sigue viéndose debajo.
      ctx.globalCompositeOperation = "destination-out"
      ctx.fillStyle = "rgba(0, 0, 0, 0.14)"
      ctx.fillRect(0, 0, ancho, alto)
      ctx.globalCompositeOperation = "source-over"
      for (let i = 0; i < gotas.length; i++) {
        const x = i * TAM
        const y = gotas[i] * TAM
        ctx.fillStyle = `rgba(${color}, ${alfaPara(x, y, 0.07 + Math.random() * 0.09)})`
        ctx.fillText(CARACTERES[Math.floor(Math.random() * CARACTERES.length)], x, y)
        if (y > alto && Math.random() > 0.975) gotas[i] = 0
        gotas[i]++
      }
    }
    raf = requestAnimationFrame(dibujar)

    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener("resize", ajustar)
      window.removeEventListener("pointermove", alMover)
      document.removeEventListener("pointerleave", alSalir)
    }
  }, [color, intensidad])

  return createPortal(
    <canvas
      ref={ref}
      aria-hidden="true"
      className="pointer-events-none"
      style={{
        position: "fixed",
        inset: 0,
        width: "100vw",
        height: "100vh",
        zIndex: 0,
        WebkitMaskImage: "radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0.4) 0%, rgba(0,0,0,0.75) 45%, black 80%)",
        maskImage: "radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0.4) 0%, rgba(0,0,0,0.75) 45%, black 80%)",
      }}
    />,
    document.body,
  )
}
