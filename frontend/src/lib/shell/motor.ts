import { resolverEscenario, type Escenario, type EscenarioResuelto } from "./escenario"
import { SistemaArchivos } from "./fs"
import { md5 } from "./md5"
import { buscarHost, curl, nc, nmap, ping, type LineaSalida } from "./red"

// Intérprete de la consola simulada. No ejecuta nada real: interpreta una
// línea estilo bash contra una máquina en memoria (archivos, red, procesos)
// y devuelve líneas de salida. Primero se prueban los comandos del guion del
// instructor (texto exacto o patrón); si ninguno coincide, se resuelve con
// los comandos genéricos de abajo.

export type { LineaSalida }

export interface ComandoGuion {
  comando: string
  salida: string
  patron?: string | null
}

export interface ResultadoEjecucion {
  lineas: LineaSalida[]
  limpiar?: boolean
}

interface Ctx {
  entrada: string | null
}

type Builtin = (args: string[], ctx: Ctx) => { salida: string; error?: string; codigo?: number; lineas?: LineaSalida[] }

const _AYUDA: Record<string, string> = {
  ls: "lista archivos (-l detalle, -a ocultos)",
  cd: "cambia de directorio",
  pwd: "muestra el directorio actual",
  cat: "muestra el contenido de un archivo",
  head: "primeras líneas (-n N)",
  tail: "últimas líneas (-n N)",
  grep: "busca texto (-i, -v, -n, -c, -A N, -B N, -r)",
  find: "busca archivos (-name patrón, -type f|d)",
  wc: "cuenta líneas, palabras y bytes (-l, -w, -c)",
  sort: "ordena líneas (-r, -n)",
  uniq: "quita repetidas consecutivas (-c)",
  cut: "corta columnas (-d separador -f campo)",
  tr: "traduce caracteres (tr 'a-z' 'A-Z', -d)",
  base64: "codifica o decodifica (-d)",
  md5sum: "hash MD5 de un archivo o de la entrada",
  echo: "imprime texto (con > archivo lo guarda)",
  whoami: "tu usuario",
  id: "usuario y grupos",
  uname: "información del sistema (-a)",
  ps: "procesos en ejecución (aux)",
  ip: "interfaces y rutas (ip a, ip route)",
  ping: "prueba si un host responde (-c N)",
  nmap: "escanea puertos (-p-, -p 22,80, -sV, -sn)",
  nc: "se conecta a un puerto y muestra el banner",
  curl: "hace peticiones HTTP (-i, -I, -d, -X)",
  nslookup: "resuelve un nombre de la red del laboratorio",
  history: "comandos que ejecutaste",
  clear: "limpia la pantalla (o Ctrl+L)",
}

function partirLineas(texto: string): string[] {
  const lineas = texto.split("\n")
  if (lineas.length > 1 && lineas[lineas.length - 1] === "") lineas.pop()
  return lineas
}

function regexSeguro(patron: string, flags = ""): RegExp {
  try {
    return new RegExp(patron, flags)
  } catch {
    return new RegExp(patron.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), flags)
  }
}

/** Expande rangos de `tr`: "a-z" → "abc…z". */
function expandirSet(set: string): string {
  let out = ""
  for (let i = 0; i < set.length; i++) {
    if (set[i + 1] === "-" && i + 2 < set.length) {
      const a = set.charCodeAt(i)
      const b = set.charCodeAt(i + 2)
      for (let c = a; c <= b; c++) out += String.fromCharCode(c)
      i += 2
    } else out += set[i]
  }
  return out
}

function globARegex(glob: string): RegExp {
  return new RegExp("^" + glob.replace(/[.+^${}()|[\]\\]/g, "\\$&").replace(/\*/g, ".*").replace(/\?/g, ".") + "$")
}

function normalizarComando(c: string): string {
  return c.trim().replace(/\s+/g, " ")
}

type Token = { tipo: "palabra"; valor: string } | { tipo: "op"; valor: "|" | "&&" | ";" | ">" | ">>" }

export class ShellSimulada {
  readonly escenario: EscenarioResuelto
  private fs: SistemaArchivos
  private cwd: string
  private env: Record<string, string>
  readonly historial: string[] = []
  private guion: ComandoGuion[]
  private builtins: Record<string, Builtin>

  constructor(opciones: { prompt: string; escenario?: Escenario | null; guion?: ComandoGuion[] }) {
    this.escenario = resolverEscenario(opciones.escenario, opciones.prompt)
    this.fs = new SistemaArchivos(this.escenario.archivos, this.escenario.home)
    this.cwd = this.escenario.directorio
    this.guion = opciones.guion || []
    this.env = {
      USER: this.escenario.usuario,
      HOME: this.escenario.home,
      SHELL: "/bin/bash",
      PATH: "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
      LANG: "es_CO.UTF-8",
      HOSTNAME: this.escenario.host,
      ...this.escenario.variables,
    }
    this.builtins = this.crearBuiltins()
  }

  get prompt(): string {
    const { usuario, host, home } = this.escenario
    const dir = this.cwd === home ? "~" : this.cwd.startsWith(home + "/") ? "~" + this.cwd.slice(home.length) : this.cwd
    return `${usuario}@${host}:${dir}${usuario === "root" ? "#" : "$"}`
  }

  bienvenida(banner: string): string {
    const lineas = [
      `Linux ${this.escenario.host} 6.6.15-amd64 #1 SMP PREEMPT_DYNAMIC x86_64 GNU/Linux`,
      "",
      this.escenario.motd || "Máquina de práctica de PlatLAB. Nada de lo que hagas aquí sale de tu navegador.",
      banner ? `\n${banner}` : "",
      "",
      `Última conexión: ${new Date(Date.now() - 3_600_000).toLocaleString("es-CO")} desde 10.10.14.1`,
      "Escribe help para ver los comandos. Tab completa nombres; ↑ ↓ recorre el historial.",
    ]
    return lineas.filter((l, i) => l !== "" || i < lineas.length - 1).join("\n")
  }

  ejecutar(lineaCruda: string): ResultadoEjecucion {
    const linea = lineaCruda.trim()
    if (!linea) return { lineas: [] }
    this.historial.push(linea)

    this.aplicarEfectos(linea)
    const delGuion = this.buscarEnGuion(linea)
    if (delGuion !== null) return { lineas: [{ texto: delGuion, retardoMs: 250 }] }

    if (linea === "clear" || linea === "cls" || linea === "reset") return { lineas: [], limpiar: true }

    let tokens: Token[]
    try {
      tokens = this.tokenizar(linea)
    } catch (e) {
      return { lineas: [{ texto: `bash: ${(e as Error).message}`, tono: "error" }] }
    }

    const salidaTotal: LineaSalida[] = []
    // Separar por ; y && (sin subshells ni ||: alcanza para la práctica).
    const secuencias: { tokens: Token[]; condicional: boolean }[] = [{ tokens: [], condicional: false }]
    for (const t of tokens) {
      if (t.tipo === "op" && (t.valor === ";" || t.valor === "&&")) secuencias.push({ tokens: [], condicional: t.valor === "&&" })
      else secuencias[secuencias.length - 1].tokens.push(t)
    }
    let ultimoCodigo = 0
    for (const s of secuencias) {
      if (s.tokens.length === 0) continue
      if (s.condicional && ultimoCodigo !== 0) break
      const { lineas, codigo } = this.ejecutarTuberia(s.tokens)
      salidaTotal.push(...lineas)
      ultimoCodigo = codigo
    }
    return { lineas: salidaTotal }
  }

  /** Efectos del escenario: un comando que "produce" archivos (ej. extraer datos ocultos). */
  private aplicarEfectos(linea: string) {
    const normal = normalizarComando(linea)
    for (const efecto of this.escenario.efectos) {
      if (!regexSeguro(`^(?:${efecto.patron})$`, "i").test(normal)) continue
      for (const [ruta, contenido] of Object.entries(efecto.archivos)) this.fs.escribir(this.ruta(ruta), contenido)
    }
  }

  private buscarEnGuion(linea: string): string | null {
    const normal = normalizarComando(linea)
    for (const c of this.guion) {
      if (c.patron) {
        if (regexSeguro(`^(?:${c.patron})$`, "i").test(normal)) return c.salida
      } else if (normalizarComando(c.comando).toLowerCase() === normal.toLowerCase()) {
        return c.salida
      }
    }
    return null
  }

  private tokenizar(linea: string): Token[] {
    const tokens: Token[] = []
    let actual = ""
    let tieneActual = false
    let i = 0
    const empujar = () => {
      if (tieneActual) tokens.push({ tipo: "palabra", valor: actual })
      actual = ""
      tieneActual = false
    }
    const expandir = (desde: number): [string, number] => {
      // $VAR o ${VAR}
      if (linea[desde + 1] === "{") {
        const fin = linea.indexOf("}", desde)
        if (fin < 0) return ["$", desde + 1]
        return [this.env[linea.slice(desde + 2, fin)] ?? "", fin + 1]
      }
      const m = /^[A-Za-z_]\w*|^\?/.exec(linea.slice(desde + 1))
      if (!m) return ["$", desde + 1]
      return [m[0] === "?" ? "0" : this.env[m[0]] ?? "", desde + 1 + m[0].length]
    }
    while (i < linea.length) {
      const c = linea[i]
      if (c === "'") {
        const fin = linea.indexOf("'", i + 1)
        if (fin < 0) throw new Error("error de sintaxis: comilla ' sin cerrar")
        actual += linea.slice(i + 1, fin)
        tieneActual = true
        i = fin + 1
      } else if (c === '"') {
        let j = i + 1
        tieneActual = true
        while (j < linea.length && linea[j] !== '"') {
          if (linea[j] === "\\" && j + 1 < linea.length) {
            actual += linea[j + 1]
            j += 2
          } else if (linea[j] === "$") {
            const [valor, sig] = expandir(j)
            actual += valor
            j = sig
          } else {
            actual += linea[j]
            j++
          }
        }
        if (j >= linea.length) throw new Error('error de sintaxis: comilla " sin cerrar')
        i = j + 1
      } else if (c === "\\" && i + 1 < linea.length) {
        actual += linea[i + 1]
        tieneActual = true
        i += 2
      } else if (c === "$") {
        const [valor, sig] = expandir(i)
        actual += valor
        tieneActual = true
        i = sig
      } else if (c === " " || c === "\t") {
        empujar()
        i++
      } else if (c === "|" || c === ";" || c === ">" || (c === "&" && linea[i + 1] === "&")) {
        empujar()
        if (c === "&") {
          tokens.push({ tipo: "op", valor: "&&" })
          i += 2
        } else if (c === ">" && linea[i + 1] === ">") {
          tokens.push({ tipo: "op", valor: ">>" })
          i += 2
        } else {
          tokens.push({ tipo: "op", valor: c as "|" | ";" | ">" })
          i++
        }
      } else if (c === "~" && !tieneActual && (linea[i + 1] === undefined || linea[i + 1] === "/" || linea[i + 1] === " ")) {
        actual += this.escenario.home
        tieneActual = true
        i++
      } else {
        actual += c
        tieneActual = true
        i++
      }
    }
    empujar()
    return tokens
  }

  private ejecutarTuberia(tokens: Token[]): { lineas: LineaSalida[]; codigo: number } {
    // Redirección final: cmd > archivo | cmd >> archivo
    let redireccion: { ruta: string; anexar: boolean } | null = null
    const idxRed = tokens.findIndex((t) => t.tipo === "op" && (t.valor === ">" || t.valor === ">>"))
    if (idxRed >= 0) {
      const destino = tokens[idxRed + 1]
      if (!destino || destino.tipo !== "palabra") {
        return { lineas: [{ texto: "bash: error sintáctico cerca del elemento inesperado `newline'", tono: "error" }], codigo: 2 }
      }
      redireccion = { ruta: destino.valor, anexar: (tokens[idxRed] as { valor: string }).valor === ">>" }
      tokens = tokens.slice(0, idxRed)
    }

    const comandos: string[][] = [[]]
    for (const t of tokens) {
      if (t.tipo === "op" && t.valor === "|") comandos.push([])
      else if (t.tipo === "palabra") comandos[comandos.length - 1].push(t.valor)
    }

    let entrada: string | null = null
    let lineasFinales: LineaSalida[] = []
    const errores: LineaSalida[] = []
    let codigo = 0
    for (let n = 0; n < comandos.length; n++) {
      const [nombre, ...args] = comandos[n]
      if (!nombre) {
        return { lineas: [{ texto: "bash: error sintáctico cerca del elemento inesperado `|'", tono: "error" }], codigo: 2 }
      }
      const r = this.ejecutarUno(nombre, args, entrada)
      codigo = r.codigo ?? 0
      if (r.error) errores.push({ texto: r.error, tono: "error" })
      if (r.lineas) {
        entrada = r.lineas.map((l) => l.texto).join("\n")
        lineasFinales = r.lineas
      } else {
        entrada = r.salida
        lineasFinales = r.salida ? [{ texto: r.salida.replace(/\n$/, "") }] : []
      }
    }

    if (redireccion) {
      const ruta = this.fs.resolver(redireccion.ruta, this.cwd, this.escenario.home)
      if (this.fs.esDirectorio(ruta)) return { lineas: [...errores, { texto: `bash: ${redireccion.ruta}: Es un directorio`, tono: "error" }], codigo: 1 }
      const contenido = (entrada ?? "") + (entrada && !entrada.endsWith("\n") ? "\n" : "")
      this.fs.escribir(ruta, contenido, {}, redireccion.anexar)
      return { lineas: errores, codigo }
    }
    return { lineas: [...errores, ...lineasFinales], codigo }
  }

  private ejecutarUno(nombre: string, args: string[], entrada: string | null) {
    // Asignación suelta VAR=valor
    if (/^[A-Za-z_]\w*=/.test(nombre) && args.length === 0) {
      const [k, ...v] = nombre.split("=")
      this.env[k] = v.join("=")
      return { salida: "" }
    }
    const comando = this.builtins[nombre]
    if (!comando) {
      return { salida: "", error: `bash: ${nombre}: orden no encontrada`, codigo: 127 }
    }
    try {
      return comando(args, { entrada })
    } catch (e) {
      return { salida: "", error: `${nombre}: ${(e as Error).message}`, codigo: 1 }
    }
  }

  // --- utilidades de archivos ------------------------------------------------

  private ruta(r: string) {
    return this.fs.resolver(r, this.cwd, this.escenario.home)
  }

  private leerTexto(nombreCmd: string, archivo: string): string {
    const ruta = this.ruta(archivo)
    if (this.fs.esDirectorio(ruta)) throw new Error(`${archivo}: Es un directorio`)
    const a = this.fs.leer(ruta)
    if (!a) throw new Error(`${archivo}: No existe el archivo o el directorio`)
    void nombreCmd
    return a.contenido
  }

  /** Texto de entrada de un filtro: archivos si se pasaron, si no la tubería. */
  private entradaDe(cmd: string, archivos: string[], ctx: Ctx): string {
    if (archivos.length === 0) return ctx.entrada ?? ""
    return archivos.map((a) => (a === "-" ? ctx.entrada ?? "" : this.leerTexto(cmd, a))).join("")
  }

  private separarFlags(args: string[], conValor: string[] = []) {
    const flags = new Set<string>()
    const valores: Record<string, string> = {}
    const resto: string[] = []
    for (let i = 0; i < args.length; i++) {
      const a = args[i]
      if (conValor.includes(a)) {
        valores[a] = args[++i] ?? ""
      } else if (a.startsWith("--")) {
        flags.add(a)
      } else if (a.startsWith("-") && a.length > 1 && !/^-\d+$/.test(a)) {
        for (const ch of a.slice(1)) flags.add(ch)
      } else resto.push(a)
    }
    return { flags, valores, resto }
  }

  // --- comandos --------------------------------------------------------------

  private crearBuiltins(): Record<string, Builtin> {
    const e = this.escenario
    const fecha = () => new Date().toLocaleString("es-CO", { weekday: "short", year: "numeric", month: "short", day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit" })

    const b: Record<string, Builtin> = {
      help: () => {
        const scripted = this.guion.map((c) => c.comando).filter(Boolean)
        const generales = Object.entries(_AYUDA).map(([k, v]) => `  ${k.padEnd(9)} ${v}`).join("\n")
        return {
          salida:
            `Comandos disponibles:\n${generales}` +
            (scripted.length ? `\n\nSugeridos para esta práctica:\n${scripted.map((c) => `  ${c}`).join("\n")}` : "") +
            "\n\nAtajos: Tab completa · ↑ ↓ historial · Ctrl+C cancela · Ctrl+L limpia",
        }
      },
      pwd: () => ({ salida: this.cwd }),
      cd: (args) => {
        const destino = this.ruta(args[0] || "~")
        if (args[0] === "-") return { salida: this.cwd }
        if (!this.fs.existe(destino)) return { salida: "", error: `bash: cd: ${args[0]}: No existe el archivo o el directorio`, codigo: 1 }
        if (!this.fs.esDirectorio(destino)) return { salida: "", error: `bash: cd: ${args[0]}: No es un directorio`, codigo: 1 }
        this.cwd = destino
        this.env.PWD = destino
        return { salida: "" }
      },
      ls: (args) => {
        const { flags, resto } = this.separarFlags(args)
        const largo = flags.has("l")
        const todos = flags.has("a")
        const objetivos = resto.length ? resto : ["."]
        const bloques: string[] = []
        for (const objetivo of objetivos) {
          const ruta = this.ruta(objetivo)
          if (!this.fs.existe(ruta)) return { salida: bloques.join("\n"), error: `ls: no se puede acceder a '${objetivo}': No existe el archivo o el directorio`, codigo: 2 }
          let entradas = this.fs.esDirectorio(ruta) ? this.fs.listar(ruta) : [{ nombre: objetivo, dir: false, ruta }]
          if (!todos) entradas = entradas.filter((x) => !x.nombre.startsWith("."))
          if (todos && this.fs.esDirectorio(ruta)) entradas = [{ nombre: ".", dir: true, ruta }, { nombre: "..", dir: true, ruta }, ...entradas]
          const cuerpo = largo
            ? [`total ${entradas.length * 4}`, ...entradas.map((x) => this.filaLs(x.nombre, x.dir, x.ruta))].join("\n")
            : entradas.map((x) => (x.dir ? `${x.nombre}/` : x.nombre)).join("  ")
          bloques.push(objetivos.length > 1 ? `${objetivo}:\n${cuerpo}` : cuerpo)
        }
        return { salida: bloques.join("\n\n") }
      },
      cat: (args, ctx) => {
        const { flags, resto } = this.separarFlags(args)
        const texto = this.entradaDe("cat", resto, ctx)
        if (flags.has("n")) return { salida: partirLineas(texto).map((l, i) => `${String(i + 1).padStart(6)}\t${l}`).join("\n") }
        return { salida: texto }
      },
      head: (args, ctx) => this.headTail(args, ctx, true),
      tail: (args, ctx) => this.headTail(args, ctx, false),
      grep: (args, ctx) => this.grep(args, ctx),
      wc: (args, ctx) => {
        const { flags, resto } = this.separarFlags(args)
        const texto = this.entradaDe("wc", resto, ctx)
        const l = (texto.match(/\n/g) || []).length
        const w = texto.split(/\s+/).filter(Boolean).length
        const c = new TextEncoder().encode(texto).length
        const partes = flags.size ? [flags.has("l") && l, flags.has("w") && w, flags.has("c") && c].filter((x) => x !== false) : [l, w, c]
        return { salida: `${partes.map((n) => String(n).padStart(flags.size === 1 ? 0 : 7)).join(" ")}${resto[0] ? " " + resto[0] : ""}`.trim() }
      },
      sort: (args, ctx) => {
        const { flags, resto } = this.separarFlags(args)
        const lineas = partirLineas(this.entradaDe("sort", resto, ctx))
        lineas.sort(flags.has("n") ? (a, b) => parseFloat(a) - parseFloat(b) : (a, b) => a.localeCompare(b))
        if (flags.has("r")) lineas.reverse()
        return { salida: lineas.join("\n") }
      },
      uniq: (args, ctx) => {
        const { flags, resto } = this.separarFlags(args)
        const lineas = partirLineas(this.entradaDe("uniq", resto, ctx))
        const out: [string, number][] = []
        for (const l of lineas) {
          if (out.length && out[out.length - 1][0] === l) out[out.length - 1][1]++
          else out.push([l, 1])
        }
        return { salida: out.map(([l, n]) => (flags.has("c") ? `${String(n).padStart(7)} ${l}` : l)).join("\n") }
      },
      cut: (args, ctx) => {
        const { valores, resto } = this.separarFlags(args, ["-d", "-f"])
        const sep = valores["-d"] ?? "\t"
        const campos = (valores["-f"] || "1").split(",").map((n) => parseInt(n, 10) - 1)
        const lineas = partirLineas(this.entradaDe("cut", resto, ctx))
        return { salida: lineas.map((l) => campos.map((f) => l.split(sep)[f] ?? "").join(sep)).join("\n") }
      },
      tr: (args, ctx) => {
        const { flags, resto } = this.separarFlags(args)
        const texto = ctx.entrada ?? ""
        if (flags.has("d")) {
          const quitar = new Set(expandirSet(resto[0] || ""))
          return { salida: [...texto].filter((ch) => !quitar.has(ch)).join("") }
        }
        const de = expandirSet(resto[0] || "")
        const a = expandirSet(resto[1] || "")
        const mapa = new Map<string, string>()
        for (let i = 0; i < de.length; i++) mapa.set(de[i], a[Math.min(i, a.length - 1)] ?? de[i])
        return { salida: [...texto].map((ch) => mapa.get(ch) ?? ch).join("") }
      },
      rev: (args, ctx) => ({ salida: partirLineas(this.entradaDe("rev", args, ctx)).map((l) => [...l].reverse().join("")).join("\n") }),
      base64: (args, ctx) => {
        const { flags, resto } = this.separarFlags(args)
        const texto = this.entradaDe("base64", resto, ctx)
        if (flags.has("d") || flags.has("--decode")) {
          try {
            const bin = atob(texto.replace(/\s+/g, ""))
            return { salida: new TextDecoder().decode(Uint8Array.from(bin, (ch) => ch.charCodeAt(0))) }
          } catch {
            return { salida: "", error: "base64: entrada no válida", codigo: 1 }
          }
        }
        const bytes = new TextEncoder().encode(texto)
        return { salida: btoa(String.fromCharCode(...bytes)) }
      },
      md5sum: (args, ctx) => {
        const archivos = args.filter((a) => !a.startsWith("-"))
        if (archivos.length === 0) return { salida: `${md5(ctx.entrada ?? "")}  -` }
        return { salida: archivos.map((a) => `${md5(this.leerTexto("md5sum", a))}  ${a}`).join("\n") }
      },
      echo: (args) => {
        const sinSalto = args[0] === "-n"
        const texto = (sinSalto ? args.slice(1) : args.filter((a) => a !== "-e")).join(" ")
        return { salida: sinSalto ? texto : texto + "\n" }
      },
      touch: (args) => {
        for (const a of args) {
          const r = this.ruta(a)
          if (!this.fs.existe(r)) this.fs.escribir(r, "")
        }
        return { salida: "" }
      },
      mkdir: (args) => {
        for (const a of args.filter((x) => !x.startsWith("-"))) this.fs.escribir(this.ruta(a) + "/.keep", "")
        return { salida: "" }
      },
      rm: (args) => {
        const objetivo = args.filter((a) => !a.startsWith("-"))[0]
        if (!objetivo) return { salida: "", error: "rm: falta un operando", codigo: 1 }
        if (this.ruta(objetivo) === "/") return { salida: "", error: "rm: es peligroso operar recursivamente en '/'", codigo: 1 }
        return { salida: "", error: `rm: no se puede borrar '${objetivo}': Sistema de archivos de solo lectura en esta práctica`, codigo: 1 }
      },
      find: (args) => {
        const { valores, resto } = this.separarFlags(args, ["-name", "-type", "-iname"])
        const base = this.ruta(resto[0] || ".")
        const patron = valores["-name"] || valores["-iname"]
        const re = patron ? globARegex(patron) : null
        const tipo = valores["-type"]
        const mostrar = (r: string) => (resto[0] ? r : "." + r.slice(this.cwd.length === 1 ? 0 : this.cwd.length))
        const filas = this.fs
          .recorrer(base)
          .filter((r) => !tipo || (tipo === "d" ? this.fs.esDirectorio(r) : !this.fs.esDirectorio(r)))
          .filter((r) => !re || re.test(r.split("/").pop() || "") || (valores["-iname"] && globARegex(patron!.toLowerCase()).test((r.split("/").pop() || "").toLowerCase())))
          .map((r) => (r === base && !resto[0] ? "." : mostrar(r)))
        return { salida: filas.join("\n") }
      },
      file: (args) => ({
        salida: args
          .map((a) => {
            const r = this.ruta(a)
            if (this.fs.esDirectorio(r)) return `${a}: directory`
            const f = this.fs.leer(r)
            if (!f) return `${a}: cannot open '${a}' (No such file or directory)`
            if (/^\x89PNG/.test(f.contenido) || a.endsWith(".png")) return `${a}: PNG image data`
            if (a.endsWith(".jpg") || a.endsWith(".jpeg")) return `${a}: JPEG image data, JFIF standard 1.01`
            return `${a}: ${f.contenido.trim() === "" ? "empty" : "ASCII text"}`
          })
          .join("\n"),
      }),
      strings: (args, ctx) => ({
        salida: (this.entradaDe("strings", args, ctx).match(/[\x20-\x7e]{4,}/g) || []).join("\n"),
      }),
      whoami: () => ({ salida: e.usuario }),
      id: () => ({
        salida: e.usuario === "root" ? "uid=0(root) gid=0(root) groups=0(root)" : `uid=1000(${e.usuario}) gid=1000(${e.usuario}) groups=1000(${e.usuario}),27(sudo)`,
      }),
      hostname: (args) => ({ salida: args.includes("-I") ? e.ip : e.host }),
      uname: (args) => ({ salida: args.includes("-a") ? `Linux ${e.host} 6.6.15-amd64 #1 SMP PREEMPT_DYNAMIC Debian 6.6.15-2 (2024-04-09) x86_64 GNU/Linux` : "Linux" }),
      date: () => ({ salida: fecha() }),
      uptime: () => ({ salida: ` ${new Date().toLocaleTimeString("es-CO")} up 2:14,  1 user,  load average: 0.08, 0.03, 0.01` }),
      ps: () => ({
        salida: [
          "USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND",
          "root           1  0.0  0.1 167700 11300 ?        Ss   08:02   0:01 /sbin/init",
          "root         412  0.0  0.0  15420  6200 ?        Ss   08:02   0:00 sshd: /usr/sbin/sshd -D",
          ...e.procesos,
          `${e.usuario.padEnd(12)} 1337  0.0  0.0   8964  5300 pts/0    Ss   10:11   0:00 -bash`,
          `${e.usuario.padEnd(12)} 1402  0.0  0.0  11084  4400 pts/0    R+   10:14   0:00 ps aux`,
        ].join("\n"),
      }),
      ip: (args) => {
        const sub = args[0] || "a"
        const red = e.ip.split(".").slice(0, 3).join(".")
        if (sub.startsWith("r")) return { salida: `default via ${red}.1 dev eth0 proto dhcp metric 100\n${red}.0/24 dev eth0 proto kernel scope link src ${e.ip}${this.subredesRed(red)}` }
        return {
          salida: `1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN\n    inet 127.0.0.1/8 scope host lo\n2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP\n    link/ether 02:42:0a:0a:0e:07 brd ff:ff:ff:ff:ff:ff\n    inet ${e.ip}/24 brd ${red}.255 scope global dynamic eth0`,
        }
      },
      ifconfig: () => ({
        salida: `eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500\n        inet ${e.ip}  netmask 255.255.255.0  broadcast ${e.ip.split(".").slice(0, 3).join(".")}.255\n        ether 02:42:0a:0a:0e:07  txqueuelen 0  (Ethernet)\n\nlo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536\n        inet 127.0.0.1  netmask 255.0.0.0`,
      }),
      arp: () => ({
        salida: e.red
          .filter((h) => h.mac)
          .map((h) => `${h.nombre || "?"} (${h.ip}) at ${h.mac!.toLowerCase()} [ether] on eth0`)
          .join("\n"),
      }),
      env: () => ({ salida: Object.entries(this.env).map(([k, v]) => `${k}=${v}`).join("\n") }),
      printenv: (args) => ({ salida: args[0] ? this.env[args[0]] ?? "" : Object.entries(this.env).map(([k, v]) => `${k}=${v}`).join("\n") }),
      export: (args) => {
        for (const a of args) {
          const [k, ...v] = a.split("=")
          if (k && v.length) this.env[k] = v.join("=")
        }
        return { salida: "" }
      },
      history: () => ({ salida: this.historial.map((c, i) => `${String(i + 1).padStart(5)}  ${c}`).join("\n") }),
      which: (args) => ({
        salida: args.map((a) => (this.builtins[a] ? `/usr/bin/${a}` : "")).filter(Boolean).join("\n"),
        codigo: args.every((a) => this.builtins[a]) ? 0 : 1,
      }),
      man: (args) => {
        const desc = _AYUDA[args[0] || ""]
        return desc ? { salida: `${args[0].toUpperCase()}(1)\n\nNOMBRE\n       ${args[0]} - ${desc}\n\n(Versión abreviada: la consola simulada incluye un resumen por comando.)` } : { salida: "", error: `No hay entrada de manual para ${args[0] || "(nada)"}`, codigo: 16 }
      },
      sudo: () => ({ salida: "", error: `[sudo] contraseña para ${e.usuario}: \nLo siento, ${e.usuario} no está en el archivo sudoers. Este incidente será reportado.`, codigo: 1 }),
      su: () => ({ salida: "", error: "su: Fallo de autenticación", codigo: 1 }),
      ssh: (args) => {
        const destino = args.filter((a) => !a.startsWith("-")).pop() || ""
        const host = buscarHost(e.red, destino.split("@").pop() || "")
        if (!host) return { salida: "", error: `ssh: Could not resolve hostname ${destino}: Name or service not known`, codigo: 255 }
        if (!host.servicios?.some((s) => s.puerto === 22)) return { salida: "", error: `ssh: connect to host ${host.ip} port 22: Connection refused`, codigo: 255 }
        return { salida: "", error: `${destino}: Permission denied (publickey,password).`, codigo: 255 }
      },
      nslookup: (args) => {
        const host = buscarHost(e.red, args[0] || "")
        if (!host) return { salida: "", error: `** server can't find ${args[0]}: NXDOMAIN`, codigo: 1 }
        return { salida: `Server:\t\t10.10.14.1\nAddress:\t10.10.14.1#53\n\nName:\t${host.nombre || args[0]}\nAddress: ${host.ip}` }
      },
      exit: () => ({ salida: "logout\n(La sesión simulada sigue abierta: puedes continuar.)" }),
      nano: () => ({ salida: "", error: "Esta consola no trae editor. Para crear un archivo usa: echo 'texto' > archivo.txt", codigo: 1 }),
      python3: () => ({ salida: "", error: "python3 no está disponible en la consola simulada. Si el laboratorio trae consola real, úsala ahí.", codigo: 127 }),
      ping: (args) => ({ salida: "", lineas: ping(e.red, args) }),
      nmap: (args) => ({ salida: "", lineas: nmap(e.red, args) }),
      nc: (args) => ({ salida: "", lineas: nc(e.red, args) }),
      curl: (args) => ({ salida: "", lineas: curl(e.red, args) }),
    }
    b.dir = b.ls
    b.more = b.cat
    b.less = b.cat
    b.vi = b.nano
    b.vim = b.nano
    b.python = b.python3
    b.ncat = b.nc
    b.netcat = b.nc
    b.host = b.nslookup
    b.dig = b.nslookup
    b.logout = b.exit
    return b
  }

  private subredesRed(propia: string): string {
    const subredes = new Set(this.escenario.red.map((h) => h.ip.split(".").slice(0, 3).join(".")))
    subredes.delete(propia)
    return [...subredes].map((s) => `\n${s}.0/24 via ${propia}.1 dev eth0`).join("")
  }

  private filaLs(nombre: string, dir: boolean, ruta: string): string {
    const meta = this.fs.leer(ruta)
    const permisos = meta?.permisos || (dir ? "drwxr-xr-x" : "-rw-r--r--")
    const dueno = (meta?.propietario || (ruta.startsWith(this.escenario.home) || nombre === "." ? this.escenario.usuario : "root")).padEnd(10)
    const tam = String(dir ? 4096 : new TextEncoder().encode(meta?.contenido || "").length).padStart(6)
    const d = new Date()
    const mes = d.toLocaleString("en-US", { month: "short" })
    return `${permisos} 1 ${dueno} ${dueno} ${tam} ${mes} ${String(d.getDate()).padStart(2)} 10:12 ${nombre}`
  }

  private headTail(args: string[], ctx: Ctx, inicio: boolean) {
    const nArg = args.find((a) => /^-\d+$/.test(a))
    const { valores, resto } = this.separarFlags(args.filter((a) => a !== nArg), ["-n"])
    const n = nArg ? parseInt(nArg.slice(1), 10) : parseInt(valores["-n"] || "10", 10)
    const lineas = partirLineas(this.entradaDe(inicio ? "head" : "tail", resto, ctx))
    return { salida: (inicio ? lineas.slice(0, n) : lineas.slice(-n)).join("\n") }
  }

  private grep(args: string[], ctx: Ctx) {
    // -A3 equivale a -A 3 (forma que casi todo el mundo escribe).
    const normalizados = args.flatMap((a) => {
      const m = /^-([ABC])(\d+)$/.exec(a)
      return m ? [`-${m[1]}`, m[2]] : [a]
    })
    const { flags, valores, resto } = this.separarFlags(normalizados, ["-A", "-B", "-C", "-e"])
    const patron = valores["-e"] ?? resto.shift()
    if (patron === undefined) return { salida: "", error: "Modo de empleo: grep [OPCIÓN]... PATRONES [ARCHIVO]...", codigo: 2 }
    const re = regexSeguro(patron, flags.has("i") ? "i" : "")
    const despues = parseInt(valores["-A"] || valores["-C"] || "0", 10)
    const antes = parseInt(valores["-B"] || valores["-C"] || "0", 10)

    let fuentes: { nombre: string | null; texto: string }[]
    if (flags.has("r") || flags.has("R")) {
      const base = this.ruta(resto[0] || ".")
      fuentes = this.fs
        .recorrer(base)
        .filter((r) => !this.fs.esDirectorio(r))
        .map((r) => ({ nombre: r.startsWith(this.cwd + "/") ? r.slice(this.cwd.length + 1) : r, texto: this.fs.leer(r)?.contenido || "" }))
    } else if (resto.length) {
      fuentes = resto.map((a) => ({ nombre: resto.length > 1 ? a : null, texto: this.leerTexto("grep", a) }))
    } else {
      fuentes = [{ nombre: null, texto: ctx.entrada ?? "" }]
    }

    const salida: string[] = []
    let total = 0
    for (const f of fuentes) {
      const lineas = partirLineas(f.texto)
      const incluir = new Set<number>()
      lineas.forEach((l, i) => {
        const coincide = re.test(l) !== flags.has("v")
        if (!coincide) return
        total++
        for (let k = Math.max(0, i - antes); k <= Math.min(lineas.length - 1, i + despues); k++) incluir.add(k)
      })
      if (flags.has("c")) {
        salida.push(`${f.nombre ? f.nombre + ":" : ""}${lineas.filter((l) => re.test(l) !== flags.has("v")).length}`)
        continue
      }
      let previo = -2
      for (const i of [...incluir].sort((a, b) => a - b)) {
        if ((despues || antes) && previo >= 0 && i > previo + 1) salida.push("--")
        const pref = `${f.nombre ? f.nombre + ":" : ""}${flags.has("n") ? i + 1 + ":" : ""}`
        salida.push(pref + lineas[i])
        previo = i
      }
    }
    return { salida: salida.join("\n"), codigo: total > 0 || flags.has("c") ? 0 : 1 }
  }

  // --- autocompletado --------------------------------------------------------

  completar(linea: string): { linea: string; opciones: string[] } {
    const partes = linea.split(/(\s+)/)
    const ultima = partes[partes.length - 1] || ""
    const esPrimera = partes.filter((p) => p.trim()).length <= 1 && !/\s$/.test(linea)
    let candidatos: string[]
    if (esPrimera) {
      candidatos = Object.keys(this.builtins).filter((c) => c.startsWith(ultima)).sort()
    } else {
      const corte = ultima.lastIndexOf("/")
      const dirTxt = corte >= 0 ? ultima.slice(0, corte + 1) : ""
      const prefijo = corte >= 0 ? ultima.slice(corte + 1) : ultima
      const dir = this.ruta(dirTxt || ".")
      candidatos = this.fs.esDirectorio(dir)
        ? this.fs
            .listar(dir)
            .filter((x) => x.nombre.startsWith(prefijo) && (prefijo.startsWith(".") || !x.nombre.startsWith(".")))
            .map((x) => dirTxt + x.nombre + (x.dir ? "/" : ""))
        : []
      // Hosts de la red como argumento (nmap, ping, curl...).
      for (const h of this.escenario.red) {
        for (const v of [h.ip, h.nombre].filter(Boolean) as string[]) if (v.startsWith(ultima)) candidatos.push(v)
      }
    }
    if (candidatos.length === 0) return { linea, opciones: [] }
    const base = partes.slice(0, -1).join("")
    if (candidatos.length === 1) {
      const c = candidatos[0]
      return { linea: base + c + (c.endsWith("/") ? "" : " "), opciones: [] }
    }
    let comun = candidatos[0]
    for (const c of candidatos) while (!c.startsWith(comun)) comun = comun.slice(0, -1)
    return { linea: base + (comun.length > ultima.length ? comun : ultima), opciones: candidatos }
  }
}
