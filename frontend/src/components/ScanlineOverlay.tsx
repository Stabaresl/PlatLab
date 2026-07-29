import { useEffect, useRef } from "react"
import anime from "animejs"

// Barrido tipo "escaneo de terminal" — anime.js anima translateY/opacity en
// loop sobre una franja de gradiente, dando sensación de sistema "vivo"
// sobre la card del hero (temática de escaneo/hacking).
export default function ScanlineOverlay() {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!ref.current) return
    const animation = anime({
      targets: ref.current,
      translateY: ["-20%", "420%"],
      opacity: [0, 0.6, 0],
      duration: 2800,
      easing: "linear",
      loop: true,
    })
    return () => animation.pause()
  }, [])

  return (
    <div
      ref={ref}
      className="absolute left-0 right-0 h-10 pointer-events-none"
      style={{
        background: "linear-gradient(180deg, transparent, rgba(59,130,246,0.45), transparent)",
      }}
      aria-hidden="true"
    />
  )
}
