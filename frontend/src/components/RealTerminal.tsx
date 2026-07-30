import { useEffect, useRef } from "react"
import { Terminal } from "@xterm/xterm"
import { FitAddon } from "@xterm/addon-fit"
import "@xterm/xterm/css/xterm.css"
import { labEnvironmentTerminalUrl } from "../pages/api"
import useReducedMotion from "../hooks/useReducedMotion"

// Terminal REAL (xterm.js) conectada por WebSocket a una sesión `docker
// exec -it bash` de un `EntornoActivo` (lab_environments) — a diferencia
// de <SimulatedTerminal>, acá los comandos se ejecutan de verdad dentro
// de un contenedor descartable y aislado del estudiante.
export default function RealTerminal({
  entornoId,
  onEstadoConexion,
}: {
  entornoId: string
  onEstadoConexion?: (estado: "conectando" | "conectado" | "cerrado" | "error") => void
}) {
  const containerRef = useRef<HTMLDivElement>(null)
  const reduced = useReducedMotion()

  useEffect(() => {
    if (!containerRef.current) return

    const term = new Terminal({
      cursorBlink: !reduced,
      fontFamily: '"JetBrains Mono", "Fira Code", monospace',
      fontSize: 13,
      theme: {
        background: "#050608",
        foreground: "#c9d2de",
        cursor: "#ffb020",
        selectionBackground: "rgba(56,214,245,0.3)",
        black: "#08090c",
        red: "#ff4757",
        green: "#33d69f",
        yellow: "#ffb020",
        blue: "#38d6f5",
        magenta: "#ffb020",
        cyan: "#38d6f5",
        white: "#c9d2de",
        brightBlack: "#565f6d",
        brightRed: "#ff4757",
        brightGreen: "#33d69f",
        brightYellow: "#ffc966",
        brightBlue: "#38d6f5",
        brightMagenta: "#ffc966",
        brightCyan: "#38d6f5",
        brightWhite: "#f4f7fb",
      },
    })
    const fitAddon = new FitAddon()
    term.loadAddon(fitAddon)
    term.open(containerRef.current)
    fitAddon.fit()

    const handleResize = () => fitAddon.fit()
    window.addEventListener("resize", handleResize)

    onEstadoConexion?.("conectando")
    const ws = new WebSocket(labEnvironmentTerminalUrl(entornoId))
    ws.binaryType = "arraybuffer"

    ws.onopen = () => {
      onEstadoConexion?.("conectado")
      term.writeln("\x1b[36m[ conectado a la consola real — comandos ejecutan de verdad ]\x1b[0m")
    }
    ws.onmessage = (event) => {
      if (typeof event.data === "string") {
        term.write(event.data)
      } else {
        term.write(new Uint8Array(event.data))
      }
    }
    ws.onclose = () => {
      onEstadoConexion?.("cerrado")
      term.writeln("\r\n\x1b[31m[ conexión cerrada ]\x1b[0m")
    }
    ws.onerror = () => {
      onEstadoConexion?.("error")
    }

    const dataDisposable = term.onData((data) => {
      if (ws.readyState === WebSocket.OPEN) ws.send(data)
    })

    return () => {
      window.removeEventListener("resize", handleResize)
      dataDisposable.dispose()
      ws.close()
      term.dispose()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entornoId])

  return (
    <div className="chamfer overflow-hidden" style={{ border: "1px solid var(--border-default)" }}>
      <div className="flex items-center gap-1.5 px-3 py-2" style={{ borderBottom: "1px solid var(--border-hairline)", backgroundColor: "var(--canvas-raised)" }}>
        <span className="w-2 h-2" style={{ backgroundColor: "var(--signal-red)" }} />
        <span className="w-2 h-2" style={{ backgroundColor: "var(--signal-amber)" }} />
        <span className="w-2 h-2" style={{ backgroundColor: "var(--signal-green)" }} />
        <span className="ml-2 text-[10px]" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
          entorno-real --terminal
        </span>
      </div>
      <div ref={containerRef} style={{ height: 320, padding: 6, backgroundColor: "#050608" }} />
    </div>
  )
}
