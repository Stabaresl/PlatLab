// Grilla ciberpunk (estilo "HUD"/Tron) en movimiento continuo — CSS puro
// (dos gradientes repetidos + @keyframes cyber-grid-scroll en index.css),
// sin canvas ni librerías. Pensada como fondo decorativo de baja opacidad,
// alternativa a <MatrixRain /> para no repetir siempre el mismo efecto.
export default function CyberGrid({
  opacity = 0.35,
  color = "59,130,246",
  fade = true,
}: {
  opacity?: number
  color?: string
  fade?: boolean
}) {
  return (
    <div
      className="absolute inset-0 pointer-events-none overflow-hidden"
      aria-hidden="true"
      style={{
        opacity,
        backgroundImage: `
          linear-gradient(rgba(${color},0.5) 1px, transparent 1px),
          linear-gradient(90deg, rgba(${color},0.5) 1px, transparent 1px)
        `,
        backgroundSize: "40px 40px",
        animation: "cyber-grid-scroll 3s linear infinite",
        maskImage: fade ? "radial-gradient(ellipse at center, black 20%, transparent 75%)" : undefined,
        WebkitMaskImage: fade ? "radial-gradient(ellipse at center, black 20%, transparent 75%)" : undefined,
      }}
    />
  )
}
