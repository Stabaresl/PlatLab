import grimBg from "../assets/grim.png"
import termBg from "../assets/term.png"
import MatrixRain from "./MatrixRain"
import CyberGrid from "./CyberGrid"

const IMAGES = { grim: grimBg, term: termBg }

// Fondo reutilizable con las imágenes de marca (grim.png / term.png) —
// Ken Burns lento + overlay OLED + textura opcional, siempre detrás del
// contenido real (z-index del contenido debe ser >= 10).
export default function HeroBackground({
  image = "grim",
  imageOpacity = 0.14,
  overlayOpacity = 0.85,
  texture = "matrix",
  textureOpacity = 0.05,
  blur = 0,
}: {
  image?: keyof typeof IMAGES
  imageOpacity?: number
  overlayOpacity?: number
  texture?: "matrix" | "grid" | "none"
  textureOpacity?: number
  blur?: number
}) {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none" aria-hidden="true">
      <div
        className="absolute inset-0"
        style={{
          backgroundImage: `url(${IMAGES[image]})`,
          backgroundSize: "cover",
          backgroundPosition: "center",
          backgroundRepeat: "no-repeat",
          opacity: imageOpacity,
          filter: blur ? `blur(${blur}px)` : undefined,
          animation: "hero-kenburns 26s ease-in-out infinite",
          willChange: "transform",
        }}
      />
      <div
        className="absolute inset-0"
        style={{ backgroundColor: "var(--canvas)", opacity: overlayOpacity }}
      />
      {texture === "matrix" && <MatrixRain opacity={textureOpacity} />}
      {texture === "grid" && <CyberGrid opacity={textureOpacity} />}
    </div>
  )
}
