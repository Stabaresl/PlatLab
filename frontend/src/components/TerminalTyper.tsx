import { useEffect, useState } from "react"

const PHRASES = [
  "> escaneando puertos abiertos...",
  "> inyectando payload de prueba...",
  "> flag capturada: OK",
  "> laboratorio completado ✓",
]

// Efecto máquina de escribir tipo terminal, cicla frases temáticas de
// hacking ético. Puramente decorativo (badge del hero de WelcomePage).
export default function TerminalTyper() {
  const [text, setText] = useState("")

  useEffect(() => {
    let phraseIndex = 0
    let charIndex = 0
    let deleting = false
    let timeout: ReturnType<typeof setTimeout>

    const tick = () => {
      const phrase = PHRASES[phraseIndex]
      if (!deleting) {
        charIndex++
        setText(phrase.slice(0, charIndex))
        if (charIndex === phrase.length) {
          deleting = true
          timeout = setTimeout(tick, 1500)
          return
        }
      } else {
        charIndex--
        setText(phrase.slice(0, charIndex))
        if (charIndex === 0) {
          deleting = false
          phraseIndex = (phraseIndex + 1) % PHRASES.length
        }
      }
      timeout = setTimeout(tick, deleting ? 25 : 40)
    }

    timeout = setTimeout(tick, 500)
    return () => clearTimeout(timeout)
  }, [])

  return (
    <span>
      {text}
      <span style={{ animation: "blink 1s step-start infinite" }}>▌</span>
    </span>
  )
}
