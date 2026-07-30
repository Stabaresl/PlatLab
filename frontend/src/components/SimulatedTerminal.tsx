import { useEffect, useRef, useState, type KeyboardEvent } from "react"
import type { EntornoPractica } from "../pages/api"
import useReducedMotion from "../hooks/useReducedMotion"

type Linea = { tipo: "input" | "output" | "sistema"; texto: string }

// Consola interactiva "guionada" (estilo HackerRank/TryHackMe): no ejecuta
// nada real — compara el comando tipeado contra el guion que autoría el
// instructor (`EntornoPractica.comandos`) y devuelve la salida asociada.
// "help"/"clear" son builtins del frontend, siempre disponibles sin
// importar el guion, para que la consola nunca se sienta "trabada".
export default function SimulatedTerminal({ entorno }: { entorno: EntornoPractica }) {
  const [lineas, setLineas] = useState<Linea[]>(
    entorno.banner ? [{ tipo: "sistema", texto: entorno.banner }] : [],
  )
  const [valor, setValor] = useState("")
  const [historialCmd, setHistorialCmd] = useState<string[]>([])
  const [cursorHistorial, setCursorHistorial] = useState<number | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const reduced = useReducedMotion()

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight
  }, [lineas])

  const resolverComando = (raw: string): string => {
    const cmd = raw.trim()
    const cmdLower = cmd.toLowerCase()
    if (cmdLower === "clear" || cmdLower === "cls") {
      setLineas([])
      return ""
    }
    if (cmdLower === "help" || cmdLower === "?") {
      const disponibles = entorno.comandos.map((c) => c.comando)
      return disponibles.length > 0
        ? `Comandos sugeridos:\n${disponibles.map((c) => `  ${c}`).join("\n")}`
        : "No hay comandos sugeridos para esta sección — explora con lo que sepas."
    }
    const match = entorno.comandos.find((c) => c.comando.trim().toLowerCase() === cmdLower)
    if (match) return match.salida
    return `bash: ${cmd}: comando no encontrado`
  }

  const ejecutar = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowUp") {
      e.preventDefault()
      if (historialCmd.length === 0) return
      const next = cursorHistorial === null ? historialCmd.length - 1 : Math.max(0, cursorHistorial - 1)
      setCursorHistorial(next)
      setValor(historialCmd[next])
      return
    }
    if (e.key === "ArrowDown") {
      e.preventDefault()
      if (cursorHistorial === null) return
      const next = cursorHistorial + 1
      if (next >= historialCmd.length) {
        setCursorHistorial(null)
        setValor("")
      } else {
        setCursorHistorial(next)
        setValor(historialCmd[next])
      }
      return
    }
    if (e.key !== "Enter") return
    const cmd = valor
    if (!cmd.trim()) return

    const salida = resolverComando(cmd)
    setLineas((prev) => {
      const conInput: Linea[] = [...prev, { tipo: "input", texto: cmd }]
      return salida ? [...conInput, { tipo: "output", texto: salida }] : conInput
    })
    setHistorialCmd((prev) => [...prev, cmd])
    setCursorHistorial(null)
    setValor("")
  }

  return (
    <div
      className="chamfer overflow-hidden"
      style={{ backgroundColor: "#050608", border: "1px solid var(--border-default)" }}
      onClick={() => inputRef.current?.focus()}
    >
      <div className="flex items-center gap-1.5 px-3 py-2" style={{ borderBottom: "1px solid var(--border-hairline)", backgroundColor: "var(--canvas-raised)" }}>
        <span className="w-2 h-2" style={{ backgroundColor: "var(--signal-red)" }} />
        <span className="w-2 h-2" style={{ backgroundColor: "var(--signal-amber)" }} />
        <span className="w-2 h-2" style={{ backgroundColor: "var(--signal-green)" }} />
        <span className="ml-2 text-[10px]" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
          practica --consola-simulada
        </span>
      </div>

      <div
        ref={scrollRef}
        className="p-3 overflow-y-auto text-xs sm:text-[13px] leading-relaxed"
        style={{ height: 280, fontFamily: "var(--font-mono)", color: "var(--signal-green)" }}
        role="log"
        aria-live="polite"
        aria-label="Consola de práctica simulada"
      >
        {lineas.map((linea, i) => (
          <div key={i} className="whitespace-pre-wrap break-words mb-1">
            {linea.tipo === "input" ? (
              <span>
                <span style={{ color: "var(--signal-cyan)" }}>{entorno.prompt}</span>{" "}
                <span style={{ color: "var(--text-heading)" }}>{linea.texto}</span>
              </span>
            ) : linea.tipo === "sistema" ? (
              <span style={{ color: "var(--text-muted)" }}>{linea.texto}</span>
            ) : (
              <span>{linea.texto}</span>
            )}
          </div>
        ))}

        <div className="flex items-center gap-1.5">
          <span style={{ color: "var(--signal-cyan)" }}>{entorno.prompt}</span>
          <input
            ref={inputRef}
            value={valor}
            onChange={(e) => setValor(e.target.value)}
            onKeyDown={ejecutar}
            spellCheck={false}
            autoComplete="off"
            className="flex-1 bg-transparent border-none outline-none"
            style={{ color: "var(--text-heading)", fontFamily: "var(--font-mono)" }}
            aria-label="Escribe un comando"
          />
          {!reduced && (
            <span aria-hidden="true" className="inline-block w-1.5 h-3.5" style={{ backgroundColor: "var(--signal-green)", animation: "blink 1s step-start infinite" }} />
          )}
        </div>
      </div>
    </div>
  )
}
