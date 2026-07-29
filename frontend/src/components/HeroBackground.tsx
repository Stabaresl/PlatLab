import grimBg from "../assets/grim.png"
import termBg from "../assets/term.png"
import MatrixRain from "./MatrixRain"
import CyberGrid from "./CyberGrid"

const IMAGES = { grim: grimBg, term: termBg }

// Fondo animado reutilizable con las imágenes hero de la Welcome (grim.png /
// term.png). Pensado para "vestir" páginas que hoy son un lienzo plano
// (Login, SignUp, About, dashboards, catálogo) sin repetir el layout del
// hero original: Ken Burns lento sobre la imagen + overlay oscuro + textura
// opcional (matrix rain / grilla) encima, todo detrás del contenido (z-index
// del contenido debe ser >= 10 y position: relative).
export default function HeroBackground({
  image = "grim",
  imageOpacity = 0.16,
  overlayOpacity = 0.82,
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
          animation: "hero-kenburns 24s ease-in-out infinite",
          willChange: "transform",
        }}
      />
      <div
        className="absolute inset-0"
        style={{ backgroundColor: "var(--bg-canvas)", opacity: overlayOpacity }}
      />
      {texture === "matrix" && <MatrixRain opacity={textureOpacity} />}
      {texture === "grid" && <CyberGrid opacity={textureOpacity} />}
    </div>
  )
}
