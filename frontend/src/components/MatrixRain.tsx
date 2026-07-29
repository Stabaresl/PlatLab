import { useEffect, useRef } from "react"

// Fondo tipo "matrix rain" (lluvia de caracteres estilo terminal/hacking) —
// canvas + requestAnimationFrame, sin dependencias externas. Pensado como
// textura ambiental de baja opacidad detrás del contenido, no como foco de
// atención (por eso pointer-events: none y opacidad controlable por prop).
const CHARS = "01アイウエオカキクケコサシスセソABCDEF{}<>/\\;:$#%&*01010011"

export default function MatrixRain({
  opacity = 0.08,
  color = "59,130,246",
}: {
  opacity?: number
  color?: string
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext("2d")
    if (!ctx) return

    let width = 0
    let height = 0
    let columns = 0
    let drops: number[] = []
    const fontSize = 15

    const setup = () => {
      width = canvas.clientWidth
      height = canvas.clientHeight
      canvas.width = width
      canvas.height = height
      columns = Math.ceil(width / fontSize)
      drops = Array.from({ length: columns }, () => Math.floor((Math.random() * height) / fontSize) * -1)
    }
    setup()

    const resizeObserver = new ResizeObserver(setup)
    resizeObserver.observe(canvas)

    let frameId: number
    let lastTime = 0
    const interval = 60 // ms entre frames — más lento que 60fps, look más "terminal"

    const draw = (time: number) => {
      frameId = requestAnimationFrame(draw)
      if (time - lastTime < interval) return
      lastTime = time

      ctx.fillStyle = "rgba(15, 17, 23, 0.12)"
      ctx.fillRect(0, 0, width, height)

      ctx.font = `${fontSize}px "JetBrains Mono", "Fira Code", monospace`
      for (let i = 0; i < columns; i++) {
        const char = CHARS[Math.floor(Math.random() * CHARS.length)]
        const y = drops[i] * fontSize
        ctx.fillStyle = `rgba(${color}, ${Math.random() * 0.5 + 0.5})`
        ctx.fillText(char, i * fontSize, y)

        if (y > height && Math.random() > 0.975) {
          drops[i] = 0
        }
        drops[i]++
      }
    }
    frameId = requestAnimationFrame(draw)

    return () => {
      cancelAnimationFrame(frameId)
      resizeObserver.disconnect()
    }
  }, [color])

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full pointer-events-none"
      style={{ opacity }}
      aria-hidden="true"
    />
  )
}
