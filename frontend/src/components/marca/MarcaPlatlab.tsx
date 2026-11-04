import { useEffect, useRef, useState } from "react"
import useReducedMotion from "../../hooks/useReducedMotion"
import IsoPlatlab from "./IsoPlatlab"

const TEXTO = "PLAT::LAB"
const GLIFOS = "01<>/#$%&*+=?ABCDEFGHJKLMNPQRSTUVWXYZ"
// Los dos puntos son el acento de la marca: van en ámbar.
const ACENTO = new Set([4, 5])

/**
 * Marca completa: isotipo animado + "PLAT::LAB". Al cargar, y cada vez que
 * pasa el puntero, las letras se "decodifican" de izquierda a derecha como
 * una salida de consola. El nombre real va en texto para lectores de pantalla.
 */
export default function MarcaPlatlab({
  tamano = 32,
  conTexto = true,
  textoClassName = "text-lg sm:text-xl",
}: {
  tamano?: number
  conTexto?: boolean
  textoClassName?: string
}) {
  const reducido = useReducedMotion()
  const [activo, setActivo] = useState(false)
  const [mostrado, setMostrado] = useState(TEXTO)
  const [disparo, setDisparo] = useState(0)
  const corriendo = useRef(false)

  useEffect(() => {
    if (reducido || !conTexto) return
    corriendo.current = true
    const inicio = performance.now()
    let ultimo = 0
    let raf = 0
    const paso = (ahora: number) => {
      const t = ahora - inicio
      if (ahora - ultimo > 45) {
        ultimo = ahora
        let salida = ""
        let listo = true
        for (let i = 0; i < TEXTO.length; i++) {
          if (t >= 140 + i * 60) salida += TEXTO[i]
          else {
            listo = false
            salida += GLIFOS[Math.floor(Math.random() * GLIFOS.length)]
          }
        }
        setMostrado(salida)
        if (listo) {
          corriendo.current = false
          return
        }
      }
      raf = requestAnimationFrame(paso)
    }
    raf = requestAnimationFrame(paso)
    return () => {
      cancelAnimationFrame(raf)
      corriendo.current = false
    }
  }, [disparo, reducido, conTexto])

  const entrar = () => {
    setActivo(true)
    if (!corriendo.current) setDisparo((d) => d + 1)
  }

  return (
    <span className="inline-flex items-center gap-2" onPointerEnter={entrar} onPointerLeave={() => setActivo(false)} onFocus={entrar} onBlur={() => setActivo(false)}>
      <IsoPlatlab tamano={tamano} activo={activo} />
      {conTexto && (
        <span className={`font-bold tracking-wide whitespace-nowrap ${textoClassName}`} style={{ color: "var(--text-heading)", fontFamily: "var(--font-mono)" }}>
          <span aria-hidden="true">
            {mostrado.split("").map((c, i) => (
              <span key={i} style={{ color: ACENTO.has(i) && c === TEXTO[i] ? "var(--signal-amber)" : undefined, opacity: c === TEXTO[i] ? 1 : 0.7 }}>
                {c}
              </span>
            ))}
          </span>
          <span className="sr-only">PlatLAB</span>
        </span>
      )}
    </span>
  )
}
