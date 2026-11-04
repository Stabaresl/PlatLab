import { motion } from "framer-motion"
import { EASE_TACTICO } from "./curvas"

/**
 * Barra que se llena al entrar en pantalla (scaleX desde la izquierda).
 * Con `segmentos`, se dibuja como tramos que se encienden uno tras otro
 * (útil para "3 de 5": cada tramo es un elemento real, no un porcentaje).
 */
export default function BarraLlenado({
  valor,
  max = 100,
  color = "var(--signal-cyan)",
  alto = 4,
  segmentos = false,
  etiqueta,
  retraso = 0,
}: {
  valor: number
  max?: number
  color?: string
  alto?: number
  segmentos?: boolean
  etiqueta: string
  retraso?: number
}) {
  const total = Math.max(max, 0)
  const lleno = Math.max(0, Math.min(valor, total))
  const fraccion = total > 0 ? lleno / total : 0

  if (segmentos && total > 0) {
    return (
      <div
        role="progressbar"
        aria-label={etiqueta}
        aria-valuemin={0}
        aria-valuemax={total}
        aria-valuenow={lleno}
        className="flex w-full gap-1"
      >
        {Array.from({ length: total }).map((_, i) => (
          <span key={i} className="relative flex-1 overflow-hidden" style={{ height: alto, backgroundColor: "var(--surface-hover)" }}>
            {i < lleno && (
              <motion.span
                className="absolute inset-0"
                style={{ backgroundColor: color, transformOrigin: "left" }}
                initial={{ scaleX: 0 }}
                whileInView={{ scaleX: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.35, delay: retraso + i * 0.09, ease: EASE_TACTICO }}
              />
            )}
          </span>
        ))}
      </div>
    )
  }

  return (
    <div
      role="progressbar"
      aria-label={etiqueta}
      aria-valuemin={0}
      aria-valuemax={total}
      aria-valuenow={lleno}
      className="relative w-full overflow-hidden"
      style={{ height: alto, backgroundColor: "var(--surface-hover)" }}
    >
      <motion.span
        className="absolute inset-0"
        style={{ backgroundColor: color, transformOrigin: "left" }}
        initial={{ scaleX: 0 }}
        whileInView={{ scaleX: fraccion }}
        viewport={{ once: true }}
        transition={{ duration: 1.1, delay: retraso, ease: EASE_TACTICO }}
      />
    </div>
  )
}
