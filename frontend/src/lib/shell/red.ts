import type { HostRed, RespuestaHttp, ServicioRed } from "./escenario"

// Herramientas de red contra los hosts del escenario. No hay red real: todo
// sale de `escenario.red`. Las salidas imitan el formato de las herramientas
// de verdad para que lo aprendido sirva fuera de la plataforma.

export interface LineaSalida {
  texto: string
  retardoMs?: number
  tono?: "error" | "aviso" | "ok"
}

// Puertos que nmap revisa sin -p (subconjunto realista del top 1000).
const _PUERTOS_COMUNES = new Set([
  20, 21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 443, 445, 993, 995, 1433, 1521, 2049, 3000, 3306, 3389, 5000, 5432,
  5900, 6379, 8000, 8080, 8443, 8888, 9000, 9090, 27017,
])

function fechaNmap(): string {
  const d = new Date()
  const p = (n: number) => String(n).padStart(2, "0")
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())} -05`
}

export function buscarHost(red: HostRed[], objetivo: string): HostRed | undefined {
  const limpio = objetivo.replace(/^\w+:\/\//, "").split(/[/:]/)[0].toLowerCase()
  return red.find((h) => h.ip === limpio || (h.nombre || "").toLowerCase() === limpio)
}

function etiquetaHost(h: HostRed): string {
  return h.nombre ? `${h.nombre} (${h.ip})` : h.ip
}

function rangoPuertos(spec: string | undefined, todos: boolean): (p: number) => boolean {
  if (todos) return () => true
  if (!spec) return (p) => _PUERTOS_COMUNES.has(p)
  const permitidos: [number, number][] = spec.split(",").map((t) => {
    const [a, b] = t.split("-").map((n) => parseInt(n, 10))
    return [a, Number.isNaN(b) ? a : b]
  })
  return (p) => permitidos.some(([a, b]) => p >= a && p <= b)
}

function enSubred(ip: string, cidr: string): boolean {
  const [base, bits] = cidr.split("/")
  if (bits !== "24") return ip === base
  return ip.split(".").slice(0, 3).join(".") === base.split(".").slice(0, 3).join(".")
}

export function nmap(red: HostRed[], args: string[]): LineaSalida[] {
  const objetivos = args.filter((a) => !a.startsWith("-") && !/^\d+(-\d+)?(,\d+(-\d+)?)*$/.test(a))
  const flags = args.filter((a) => a.startsWith("-"))
  const iP = args.indexOf("-p")
  const specPuertos = iP >= 0 ? args[iP + 1] : flags.find((f) => f.startsWith("-p") && f !== "-p" && f !== "-p-")?.slice(2)
  const todos = flags.includes("-p-")
  const conVersion = flags.some((f) => f === "-sV" || f === "-A")
  const soloPing = flags.includes("-sn")
  const objetivosReales = objetivos.filter((o) => o !== specPuertos)
  const t0 = performance.now()

  if (objetivosReales.length === 0) {
    return [{ texto: "Nmap 7.94SVN ( https://nmap.org )\nUsage: nmap [Scan Type(s)] [Options] {target specification}\nEjemplo: nmap -sV 192.168.56.20", tono: "aviso" }]
  }

  const salida: LineaSalida[] = [{ texto: `Starting Nmap 7.94SVN ( https://nmap.org ) at ${fechaNmap()}` }]
  let arriba = 0
  let total = 0
  for (const objetivo of objetivosReales) {
    const hosts = objetivo.includes("/") ? red.filter((h) => enSubred(h.ip, objetivo)) : [buscarHost(red, objetivo)].filter(Boolean) as HostRed[]
    total += objetivo.includes("/") ? 256 : 1
    if (hosts.length === 0 && !objetivo.includes("/")) {
      salida.push({ texto: `Note: Host seems down. If it is really up, but blocking our ping probes, try -Pn`, retardoMs: 900 })
      continue
    }
    for (const h of hosts) {
      arriba += 1
      salida.push({ texto: `Nmap scan report for ${etiquetaHost(h)}`, retardoMs: 500 })
      salida.push({ texto: `Host is up (0.00${Math.floor(Math.random() * 80 + 10)}s latency).` })
      if (soloPing) {
        if (h.mac) salida.push({ texto: `MAC Address: ${h.mac.toUpperCase()}` })
        continue
      }
      const filtro = rangoPuertos(specPuertos, todos)
      const abiertos = (h.servicios || []).filter((s) => filtro(s.puerto)).sort((a, b) => a.puerto - b.puerto)
      const revisados = todos ? 65535 : specPuertos ? abiertos.length : 1000
      if (abiertos.length === 0) {
        salida.push({ texto: `All ${revisados} scanned ports on ${etiquetaHost(h)} are in ignored states.` })
        continue
      }
      if (revisados > abiertos.length) salida.push({ texto: `Not shown: ${revisados - abiertos.length} closed tcp ports (reset)` })
      salida.push({ texto: conVersion ? "PORT      STATE SERVICE  VERSION" : "PORT      STATE SERVICE" })
      for (const s of abiertos) salida.push({ texto: filaPuerto(s, conVersion), retardoMs: todos ? 220 : 60 })
      if (h.mac) salida.push({ texto: `MAC Address: ${h.mac.toUpperCase()}` })
      if (conVersion && h.so) salida.push({ texto: `Service Info: OS: ${h.so}` })
    }
  }
  const segundos = ((performance.now() - t0) / 1000 + (todos ? 14.2 : conVersion ? 6.8 : 1.6)).toFixed(2)
  salida.push({ texto: `Nmap done: ${total} IP address${total === 1 ? "" : "es"} (${arriba} host${arriba === 1 ? "" : "s"} up) scanned in ${segundos} seconds`, retardoMs: todos ? 1600 : 500 })
  return salida
}

function filaPuerto(s: ServicioRed, conVersion: boolean): string {
  const puerto = `${s.puerto}/${s.protocolo || "tcp"}`.padEnd(10)
  const estado = (s.estado || "open").padEnd(6)
  const servicio = s.servicio.padEnd(9)
  return conVersion && s.version ? `${puerto}${estado}${servicio}${s.version}` : `${puerto}${estado}${s.servicio}`
}

export function ping(red: HostRed[], args: string[]): LineaSalida[] {
  const objetivo = args.filter((a) => !a.startsWith("-") && !/^\d+$/.test(a))[0]
  if (!objetivo) return [{ texto: "ping: uso: ping [-c cantidad] destino", tono: "aviso" }]
  const iC = args.indexOf("-c")
  const cantidad = Math.min(Math.max(iC >= 0 ? parseInt(args[iC + 1], 10) || 4 : 4, 1), 10)
  const host = buscarHost(red, objetivo)
  const esIp = /^\d+\.\d+\.\d+\.\d+$/.test(objetivo)
  if (!host && !esIp) return [{ texto: `ping: ${objetivo}: Nombre o servicio desconocido`, tono: "error" }]
  const ip = host?.ip || objetivo
  const salida: LineaSalida[] = [{ texto: `PING ${host?.nombre || ip} (${ip}) 56(84) bytes of data.` }]
  if (!host) {
    for (let i = 1; i <= cantidad; i++) salida.push({ texto: `From 10.10.14.1 icmp_seq=${i} Destination Host Unreachable`, retardoMs: 700, tono: "error" })
    salida.push({ texto: `\n--- ${ip} ping statistics ---\n${cantidad} packets transmitted, 0 received, +${cantidad} errors, 100% packet loss` })
    return salida
  }
  const tiempos: number[] = []
  for (let i = 1; i <= cantidad; i++) {
    const t = 0.3 + Math.random() * 0.9
    tiempos.push(t)
    salida.push({ texto: `64 bytes from ${ip}: icmp_seq=${i} ttl=64 time=${t.toFixed(3)} ms`, retardoMs: 650 })
  }
  const min = Math.min(...tiempos).toFixed(3)
  const max = Math.max(...tiempos).toFixed(3)
  const avg = (tiempos.reduce((a, b) => a + b, 0) / tiempos.length).toFixed(3)
  salida.push({ texto: `\n--- ${host.nombre || ip} ping statistics ---\n${cantidad} packets transmitted, ${cantidad} received, 0% packet loss\nrtt min/avg/max/mdev = ${min}/${avg}/${max}/0.112 ms` })
  return salida
}

export function nc(red: HostRed[], args: string[]): LineaSalida[] {
  const limpios = args.filter((a) => !a.startsWith("-"))
  const [objetivo, puertoTxt] = limpios
  if (!objetivo || !puertoTxt) return [{ texto: "uso: nc [-nv] host puerto", tono: "aviso" }]
  const host = buscarHost(red, objetivo)
  const puerto = parseInt(puertoTxt, 10)
  const servicio = host?.servicios?.find((s) => s.puerto === puerto)
  if (!host || !servicio) {
    return [{ texto: `(UNKNOWN) [${host?.ip || objetivo}] ${puerto} (?) : Connection refused`, tono: "error", retardoMs: 300 }]
  }
  const verboso = args.some((a) => a.includes("v"))
  const salida: LineaSalida[] = []
  if (verboso) salida.push({ texto: `${host.nombre || host.ip} [${host.ip}] ${puerto} (${servicio.servicio}) open` })
  salida.push({ texto: servicio.banner || `${servicio.version || servicio.servicio}`, retardoMs: 400 })
  return salida
}

function decodificar(valor: string): string {
  try {
    return decodeURIComponent(valor.replace(/\+/g, " "))
  } catch {
    return valor
  }
}

export interface PeticionCurl {
  url: string
  metodo: string
  datos: string
  incluirCabeceras: boolean
  soloCabeceras: boolean
  silencioso: boolean
}

export function parsearCurl(args: string[]): PeticionCurl | null {
  let url = ""
  let metodo = ""
  const datos: string[] = []
  let incluirCabeceras = false
  let soloCabeceras = false
  let silencioso = false
  for (let i = 0; i < args.length; i++) {
    const a = args[i]
    if (a === "-X" || a === "--request") metodo = (args[++i] || "GET").toUpperCase()
    else if (a === "-d" || a === "--data" || a === "--data-raw" || a === "--data-urlencode") datos.push(args[++i] || "")
    else if (a === "-H" || a === "--header" || a === "-A" || a === "-b" || a === "-o") i++
    else if (a === "-i" || a === "--include") incluirCabeceras = true
    else if (a === "-I" || a === "--head") soloCabeceras = true
    else if (a.startsWith("-") && /s/.test(a) && !a.startsWith("--")) silencioso = true
    else if (!a.startsWith("-")) url = a
  }
  if (!url) return null
  return {
    url: url.includes("://") ? url : `http://${url}`,
    metodo: metodo || (datos.length ? "POST" : soloCabeceras ? "HEAD" : "GET"),
    datos: datos.join("&"),
    incluirCabeceras,
    soloCabeceras,
    silencioso,
  }
}

export function curl(red: HostRed[], args: string[]): LineaSalida[] {
  const p = parsearCurl(args)
  if (!p) return [{ texto: "curl: try 'curl --help' for more information", tono: "aviso" }]
  let url: URL
  try {
    url = new URL(p.url)
  } catch {
    return [{ texto: `curl: (3) URL rejected: Malformed input to a URL function`, tono: "error" }]
  }
  const host = buscarHost(red, url.hostname)
  const puerto = url.port ? parseInt(url.port, 10) : url.protocol === "https:" ? 443 : 80
  if (!host) return [{ texto: `curl: (6) Could not resolve host: ${url.hostname}`, tono: "error", retardoMs: 400 }]
  const servicio = host.servicios?.find((s) => s.puerto === puerto)
  if (!servicio) {
    return [{ texto: `curl: (7) Failed to connect to ${url.hostname} port ${puerto} after 3 ms: Couldn't connect to server`, tono: "error", retardoMs: 300 }]
  }
  const consulta = decodificar(url.search.replace(/^\?/, ""))
  const enviado = `${decodificar(p.datos)}\n${consulta}`
  const metodoBase = p.metodo === "HEAD" ? "GET" : p.metodo
  const candidatas = (host.http || []).filter((r) => r.ruta === url.pathname && (r.metodo || "GET").toUpperCase() === metodoBase)
  const elegida: RespuestaHttp | undefined =
    candidatas.find((r) => r.cuando && safeRegex(r.cuando)?.test(enviado)) || candidatas.find((r) => !r.cuando)
  const respuesta: RespuestaHttp = elegida || {
    ruta: url.pathname,
    estado: 404,
    cuerpo: `<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">\n<html><head><title>404 Not Found</title></head><body>\n<h1>Not Found</h1>\n<p>The requested URL was not found on this server.</p>\n</body></html>`,
  }
  // {{param}} en el cuerpo refleja lo que mandó el cliente (query o datos), sin escapar:
  // así se ve en la consola un XSS reflejado tal como lo devolvería el servidor.
  const datosForm = new URLSearchParams(p.datos)
  const cuerpo = respuesta.cuerpo.replace(/\{\{(\w+)\}\}/g, (_, k: string) => url.searchParams.get(k) ?? datosForm.get(k) ?? "")
  const estado = respuesta.estado || 200
  const cabeceras = {
    Date: new Date().toUTCString(),
    Server: servicio.version || "Apache/2.4.52 (Ubuntu)",
    "Content-Type": "text/html; charset=UTF-8",
    ...(respuesta.cabeceras || {}),
  }
  const lineaEstado = `HTTP/1.1 ${estado} ${estado === 200 ? "OK" : estado === 302 ? "Found" : estado === 403 ? "Forbidden" : estado === 404 ? "Not Found" : estado === 500 ? "Internal Server Error" : ""}`
  const bloqueCabeceras = [lineaEstado, ...Object.entries(cabeceras).map(([k, v]) => `${k}: ${v}`)].join("\n")
  if (p.soloCabeceras) return [{ texto: bloqueCabeceras, retardoMs: 350 }]
  const texto = p.incluirCabeceras ? `${bloqueCabeceras}\n\n${cuerpo}` : cuerpo
  return [{ texto, retardoMs: 350 }]
}

function safeRegex(patron: string): RegExp | null {
  try {
    return new RegExp(patron, "i")
  } catch {
    return null
  }
}
