import { useEffect, useRef, type CSSProperties } from "react"
import { animate, useInView, useReducedMotion } from "framer-motion"
import { EASE_TACTICO } from "./curvas"

/**
 * Cifra que cuenta desde 0 hasta su valor cuando entra en pantalla. El valor
 * real va en un texto solo para lectores de pantalla; lo animado es aria-hidden.
 */
export default function NumeroAnimado({
  valor,
  sufijo = "",
  duracion = 1.2,
  className,
  style,
}: {
  valor: number
  sufijo?: string
  duracion?: number
  className?: string
  style?: CSSProperties
}) {
  const ref = useRef<HTMLSpanElement>(null)
  const visto = useInView(ref, { once: true })
  const reducido = useReducedMotion()

  useEffect(() => {
    const el = ref.current
    if (!el || !visto) return
    if (reducido) {
      el.textContent = `${valor}${sufijo}`
      return
    }
    const control = animate(0, valor, {
      duration: duracion,
      ease: EASE_TACTICO,
      onUpdate: (v) => {
        el.textContent = `${Math.round(v)}${sufijo}`
      },
    })
    return () => control.stop()
  }, [visto, valor, sufijo, duracion, reducido])

  return (
    <span className={className} style={style}>
      <span ref={ref} aria-hidden="true">{reducido ? `${valor}${sufijo}` : `0${sufijo}`}</span>
      <span className="sr-only">{`${valor}${sufijo}`}</span>
    </span>
  )
}
