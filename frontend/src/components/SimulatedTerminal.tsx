import { useCallback, useEffect, useImperativeHandle, useMemo, useRef, useState, type KeyboardEvent, type Ref } from "react"
import type { EntornoPractica } from "../pages/api"
import { ShellSimulada, type LineaSalida } from "../lib/shell/motor"
import useReducedMotion from "../hooks/useReducedMotion"

type Linea = { tipo: "input"; prompt: string; texto: string } | { tipo: "output"; texto: string; tono?: LineaSalida["tono"] } | { tipo: "sistema"; texto: string }

export interface ConsolaHandle {
  /** Escribe y ejecuta un comando como si la persona lo hubiera tecleado (botón "Ejecutar en consola"). */
  ejecutar: (comando: string) => void
  enfocar: () => void
}

const _TONO: Record<NonNullable<LineaSalida["tono"]>, string> = {
  error: "var(--signal-red)",
  aviso: "var(--signal-amber)",
  ok: "var(--signal-green)",
}

/**
 * Consola de práctica simulada: una máquina Linux en memoria (lib/shell) con
 * archivos, red y servicios definidos por el escenario del laboratorio. No
 * ejecuta nada real; la salida aparece de forma progresiva (nmap o ping
 * tardan como de verdad) y se puede cancelar con Ctrl+C.
 */
export default function SimulatedTerminal({
  entorno,
  ref,
  onComando,
  alto = 380,
}: {
  entorno: EntornoPractica
  ref?: Ref<ConsolaHandle>
  onComando?: (comando: string) => void
  alto?: number | string
}) {
  const reduced = useReducedMotion()
  const crearShell = useCallback(
    () => new ShellSimulada({ prompt: entorno.prompt, escenario: entorno.escenario, guion: entorno.comandos }),
    [entorno],
  )
  const [shell, setShell] = useState(crearShell)
  const bienvenida = useMemo(() => shell.bienvenida(entorno.banner), [shell, entorno.banner])
  const [lineas, setLineas] = useState<Linea[]>([{ tipo: "sistema", texto: bienvenida }])
  const [valor, setValor] = useState("")
  const [prompt, setPrompt] = useState(shell.prompt)
  const [ocupado, setOcupado] = useState(false)
  const [cursorHistorial, setCursorHistorial] = useState<number | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const temporizadores = useRef<number[]>([])

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight
  }, [lineas])

  useEffect(() => () => temporizadores.current.forEach((t) => clearTimeout(t)), [])

  const cancelar = () => {
    temporizadores.current.forEach((t) => clearTimeout(t))
    temporizadores.current = []
    setOcupado(false)
  }

  const mostrarProgresivo = (salida: LineaSalida[]) => {
    if (salida.length === 0) return
    if (reduced || salida.every((l) => !l.retardoMs)) {
      setLineas((prev) => [...prev, ...salida.map((l) => ({ tipo: "output" as const, texto: l.texto, tono: l.tono }))])
      return
    }
    setOcupado(true)
    let acumulado = 0
    salida.forEach((l, i) => {
      acumulado += Math.min(l.retardoMs || 0, 1600)
      const t = window.setTimeout(() => {
        setLineas((prev) => [...prev, { tipo: "output", texto: l.texto, tono: l.tono }])
        if (i === salida.length - 1) {
          setOcupado(false)
          inputRef.current?.focus()
        }
      }, acumulado)
      temporizadores.current.push(t)
    })
  }

  const correr = (comando: string) => {
    const promptActual = shell.prompt
    setLineas((prev) => [...prev, { tipo: "input", prompt: promptActual, texto: comando }])
    const resultado = shell.ejecutar(comando)
    setPrompt(shell.prompt)
    if (resultado.limpiar) setLineas([])
    else mostrarProgresivo(resultado.lineas)
    if (comando.trim()) onComando?.(comando.trim())
  }

  useImperativeHandle(ref, () => ({
    ejecutar: (comando: string) => {
      if (ocupado) cancelar()
      correr(comando)
      inputRef.current?.focus()
    },
    enfocar: () => inputRef.current?.focus(),
  }))

  const reiniciar = () => {
    cancelar()
    const nuevo = crearShell()
    setShell(nuevo)
    setPrompt(nuevo.prompt)
    setLineas([{ tipo: "sistema", texto: nuevo.bienvenida(entorno.banner) }])
    setValor("")
    inputRef.current?.focus()
  }

  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.ctrlKey && e.key.toLowerCase() === "c") {
      e.preventDefault()
      cancelar()
      setLineas((prev) => [...prev, { tipo: "input", prompt: shell.prompt, texto: valor + "^C" }])
      setValor("")
      return
    }
    if (e.ctrlKey && e.key.toLowerCase() === "l") {
      e.preventDefault()
      setLineas([])
      return
    }
    if (ocupado) {
      e.preventDefault()
      return
    }
    const historial = shell.historial
    if (e.key === "ArrowUp") {
      e.preventDefault()
      if (historial.length === 0) return
      const next = cursorHistorial === null ? historial.length - 1 : Math.max(0, cursorHistorial - 1)
      setCursorHistorial(next)
      setValor(historial[next])
      return
    }
    if (e.key === "ArrowDown") {
      e.preventDefault()
      if (cursorHistorial === null) return
      const next = cursorHistorial + 1
      setCursorHistorial(next >= historial.length ? null : next)
      setValor(next >= historial.length ? "" : historial[next])
      return
    }
    if (e.key === "Tab") {
      e.preventDefault()
      const { linea, opciones } = shell.completar(valor)
      setValor(linea)
      if (opciones.length > 1) {
        setLineas((prev) => [...prev, { tipo: "input", prompt: shell.prompt, texto: valor }, { tipo: "output", texto: opciones.join("    ") }])
      }
      return
    }
    if (e.key !== "Enter") return
    e.preventDefault()
    setCursorHistorial(null)
    const comando = valor
    setValor("")
    if (!comando.trim()) {
      setLineas((prev) => [...prev, { tipo: "input", prompt: shell.prompt, texto: "" }])
      return
    }
    correr(comando)
  }

  const { usuario, host, ip } = shell.escenario

  return (
    <section
      aria-label="Consola de práctica simulada"
      className="chamfer flex flex-col overflow-hidden"
      style={{ backgroundColor: "var(--surface-sunken)", border: "1px solid var(--border-default)" }}
    >
      <header
        className="flex items-center gap-x-3 gap-y-1 flex-wrap px-3 py-2 text-[11px]"
        style={{ borderBottom: "1px solid var(--border-hairline)", backgroundColor: "var(--canvas-raised)", fontFamily: "var(--font-mono)" }}
      >
        <span style={{ color: "var(--signal-green)" }}>{usuario}@{host}</span>
        <span style={{ color: "var(--text-dim)" }}>{ip}</span>
        <span
          className="chamfer-sm px-1.5 py-0.5 uppercase tracking-wider text-[10px]"
          style={{ color: "var(--signal-cyan)", border: "1px solid var(--border-cyan)" }}
          title="No ejecuta comandos reales: es una máquina simulada en tu navegador"
        >
          simulada
        </span>
        <span className="ml-auto flex items-center gap-1.5">
          {ocupado && (
            <button type="button" onClick={cancelar} className="consola-btn">
              Ctrl+C
            </button>
          )}
          <button type="button" onClick={() => setLineas([])} className="consola-btn">
            Limpiar
          </button>
          <button type="button" onClick={reiniciar} className="consola-btn" title="Vuelve la máquina a su estado inicial">
            Reiniciar
          </button>
        </span>
      </header>

      <div
        ref={scrollRef}
        onClick={() => {
          if (!window.getSelection()?.toString()) inputRef.current?.focus()
        }}
        className="p-3 overflow-y-auto text-xs sm:text-[13px] leading-relaxed cursor-text"
        style={{ height: alto, fontFamily: "var(--font-mono)", color: "var(--text-base)" }}
        role="log"
        aria-live="polite"
      >
        {lineas.map((linea, i) => (
          <div key={i} className="whitespace-pre-wrap break-words">
            {linea.tipo === "input" ? (
              <span>
                <span style={{ color: "var(--signal-green)" }}>{linea.prompt}</span>{" "}
                <span style={{ color: "var(--text-heading)" }}>{linea.texto}</span>
              </span>
            ) : linea.tipo === "sistema" ? (
              <span style={{ color: "var(--text-muted)" }}>{linea.texto}</span>
            ) : (
              <span style={{ color: linea.tono ? _TONO[linea.tono] : "var(--text-base)" }}>{linea.texto}</span>
            )}
          </div>
        ))}

        <div className="flex items-center gap-1.5" style={{ opacity: ocupado ? 0.4 : 1 }}>
          <span className="shrink-0" style={{ color: "var(--signal-green)" }}>{prompt}</span>
          <input
            ref={inputRef}
            value={valor}
            onChange={(e) => setValor(e.target.value)}
            onKeyDown={onKeyDown}
            spellCheck={false}
            autoComplete="off"
            autoCapitalize="off"
            className="flex-1 min-w-0 bg-transparent border-none outline-none"
            style={{ color: "var(--text-heading)", fontFamily: "var(--font-mono)", caretColor: "var(--signal-green)" }}
            aria-label="Escribe un comando y presiona Enter"
          />
        </div>
      </div>
    </section>
  )
}
