// Escenario de la consola simulada: describe la "máquina" del estudiante y la
// red que la rodea. Viene del backend en `EntornoPractica.escenario` (JSON
// autoría del instructor). Todo es opcional: sin escenario, la consola arma
// una máquina mínima a partir del prompt.

export interface ArchivoVirtual {
  contenido: string
  permisos?: string // ej. "-rw-r--r--"
  propietario?: string
}

export interface ServicioRed {
  puerto: number
  protocolo?: "tcp" | "udp"
  servicio: string // ssh, http, ftp...
  version?: string // se muestra con nmap -sV
  banner?: string // lo que responde al conectarse con nc
  estado?: "open" | "filtered"
}

export interface RespuestaHttp {
  ruta: string // "/login.php"
  metodo?: string // GET por defecto
  // Regex (sin delimitadores) contra los datos enviados + la query decodificada:
  // permite responder distinto según el payload (ej. inyección SQL).
  cuando?: string
  estado?: number
  cabeceras?: Record<string, string>
  cuerpo: string
}

export interface HostRed {
  ip: string
  nombre?: string
  mac?: string
  so?: string
  servicios?: ServicioRed[]
  http?: RespuestaHttp[]
}

export interface Escenario {
  usuario?: string
  host?: string
  ip?: string
  directorio?: string // directorio de trabajo inicial; por defecto el home
  archivos?: Record<string, string | ArchivoVirtual> // ruta → contenido
  red?: HostRed[]
  procesos?: string[] // líneas extra para `ps aux`
  variables?: Record<string, string>
  motd?: string
  // Efectos de comandos: si la línea coincide con `patron`, se crean estos archivos
  // (ej. `steghide extract ...` deja `secreto.txt`).
  efectos?: { patron: string; archivos: Record<string, string> }[]
}

export interface EscenarioResuelto {
  efectos: { patron: string; archivos: Record<string, string> }[]
  usuario: string
  host: string
  ip: string
  home: string
  directorio: string
  archivos: Record<string, ArchivoVirtual>
  red: HostRed[]
  procesos: string[]
  variables: Record<string, string>
  motd: string
}

const _README_POR_DEFECTO = `Bienvenido a tu máquina de práctica.

- Lee la guía de la izquierda: cada tarea trae el comando y lo que deberías ver.
- Escribe help para ver los comandos disponibles.
- Nada de lo que hagas aquí sale de tu navegador.
`

/** Toma usuario y host del prompt si no vienen en el escenario: "estudiante@labs:~$" → estudiante / labs. */
function desdePrompt(prompt: string): { usuario?: string; host?: string } {
  const m = /^([a-z_][\w-]*)@([\w.-]+)/i.exec(prompt.trim())
  return m ? { usuario: m[1], host: m[2] } : {}
}

export function resolverEscenario(escenario: Escenario | undefined | null, prompt: string): EscenarioResuelto {
  const e = escenario || {}
  const delPrompt = desdePrompt(prompt)
  const usuario = e.usuario || delPrompt.usuario || "estudiante"
  const host = e.host || delPrompt.host || "lab"
  const home = usuario === "root" ? "/root" : `/home/${usuario}`

  const archivos: Record<string, ArchivoVirtual> = {}
  const origen = e.archivos && Object.keys(e.archivos).length > 0 ? e.archivos : { "README.txt": _README_POR_DEFECTO }
  for (const [ruta, valor] of Object.entries(origen)) {
    const absoluta = ruta.startsWith("/") ? ruta : `${home}/${ruta.replace(/^~\//, "")}`
    archivos[normalizarRuta(absoluta)] = typeof valor === "string" ? { contenido: valor } : valor
  }

  return {
    usuario,
    host,
    ip: e.ip || "10.10.14.7",
    home,
    directorio: e.directorio ? normalizarRuta(e.directorio.replace(/^~/, home)) : home,
    archivos,
    red: e.red || [],
    procesos: e.procesos || [],
    variables: e.variables || {},
    motd: e.motd || "",
    efectos: e.efectos || [],
  }
}

export function normalizarRuta(ruta: string): string {
  const partes: string[] = []
  for (const p of ruta.split("/")) {
    if (!p || p === ".") continue
    if (p === "..") partes.pop()
    else partes.push(p)
  }
  return "/" + partes.join("/")
}
