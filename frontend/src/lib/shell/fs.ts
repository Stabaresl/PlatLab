import { normalizarRuta, type ArchivoVirtual } from "./escenario"

// Sistema de archivos en memoria a partir de un mapa ruta → archivo. Los
// directorios se infieren de las rutas (más unos básicos de Linux), así el
// instructor solo declara los archivos que importan para la práctica.

const _DIRECTORIOS_BASE = ["/", "/bin", "/etc", "/home", "/tmp", "/usr", "/usr/bin", "/var", "/var/log", "/root"]

export class SistemaArchivos {
  private archivos = new Map<string, ArchivoVirtual>()
  private directorios = new Set<string>(_DIRECTORIOS_BASE)

  constructor(archivos: Record<string, ArchivoVirtual>, home: string) {
    this.agregarDirectorio(home)
    for (const [ruta, archivo] of Object.entries(archivos)) this.escribir(ruta, archivo.contenido, archivo)
    if (!this.archivos.has("/etc/hostname")) this.archivos.set("/etc/hostname", { contenido: "lab\n" })
  }

  private agregarDirectorio(ruta: string) {
    let actual = ""
    for (const parte of normalizarRuta(ruta).split("/").filter(Boolean)) {
      actual += "/" + parte
      this.directorios.add(actual)
    }
  }

  resolver(ruta: string, cwd: string, home: string): string {
    if (!ruta || ruta === "~") return home
    if (ruta.startsWith("~/")) return normalizarRuta(home + ruta.slice(1))
    return normalizarRuta(ruta.startsWith("/") ? ruta : `${cwd}/${ruta}`)
  }

  esDirectorio(ruta: string): boolean {
    return this.directorios.has(ruta)
  }

  existe(ruta: string): boolean {
    return this.directorios.has(ruta) || this.archivos.has(ruta)
  }

  leer(ruta: string): ArchivoVirtual | undefined {
    return this.archivos.get(ruta)
  }

  escribir(ruta: string, contenido: string, meta: Partial<ArchivoVirtual> = {}, anexar = false) {
    const destino = normalizarRuta(ruta)
    const padre = destino.slice(0, destino.lastIndexOf("/")) || "/"
    this.agregarDirectorio(padre)
    const previo = this.archivos.get(destino)
    this.archivos.set(destino, {
      ...previo,
      ...meta,
      contenido: anexar && previo ? previo.contenido + contenido : contenido,
    })
  }

  /** Entradas directas de un directorio: nombre + si es directorio. */
  listar(dir: string): { nombre: string; dir: boolean; ruta: string }[] {
    const prefijo = dir === "/" ? "/" : dir + "/"
    const vistos = new Map<string, boolean>()
    for (const d of this.directorios) {
      if (d !== dir && d.startsWith(prefijo) && !d.slice(prefijo.length).includes("/")) vistos.set(d.slice(prefijo.length), true)
    }
    for (const f of this.archivos.keys()) {
      if (f.startsWith(prefijo) && !f.slice(prefijo.length).includes("/")) vistos.set(f.slice(prefijo.length), false)
    }
    return [...vistos.entries()]
      .map(([nombre, esDir]) => ({ nombre, dir: esDir, ruta: prefijo + nombre }))
      .sort((a, b) => a.nombre.localeCompare(b.nombre))
  }

  /** Todas las rutas bajo `dir` (para `find`). */
  recorrer(dir: string): string[] {
    const prefijo = dir === "/" ? "/" : dir + "/"
    const todas = [...this.directorios, ...this.archivos.keys()].filter((r) => r === dir || r.startsWith(prefijo))
    return [...new Set(todas)].sort()
  }
}
