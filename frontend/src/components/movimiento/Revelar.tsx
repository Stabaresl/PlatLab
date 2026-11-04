import type { CSSProperties, ReactNode } from "react"
import { motion } from "framer-motion"
import { EASE_TACTICO } from "./curvas"

type Desde = "abajo" | "izquierda" | "derecha" | "escala"

const INICIAL: Record<Desde, { opacity: number; x?: number; y?: number; scale?: number }> = {
  abajo: { opacity: 0, y: 18 },
  izquierda: { opacity: 0, x: -18 },
  derecha: { opacity: 0, x: 18 },
  escala: { opacity: 0, scale: 0.94 },
}

/**
 * Entrada al hacer scroll: el bloque aparece una sola vez cuando entra en
 * pantalla (fundido + desplazamiento corto, sin rebote). Con movimiento
 * reducido, MotionConfig de main.tsx lo deja solo en fundido.
 */
export default function Revelar({
  children,
  desde = "abajo",
  retraso = 0,
  como = "div",
  className,
  style,
}: {
  children: ReactNode
  desde?: Desde
  retraso?: number
  como?: "div" | "section"
  className?: string
  style?: CSSProperties
}) {
  const Elemento = como === "section" ? motion.section : motion.div
  return (
    <Elemento
      initial={INICIAL[desde]}
      whileInView={{ opacity: 1, x: 0, y: 0, scale: 1 }}
      viewport={{ once: true, margin: "0px 0px -48px 0px" }}
      transition={{ duration: 0.55, delay: retraso, ease: EASE_TACTICO }}
      className={className}
      style={style}
    >
      {children}
    </Elemento>
  )
}
