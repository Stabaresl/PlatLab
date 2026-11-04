import { useEffect, useRef } from "react"
import * as THREE from "three"
import { colorToken, liberar, prefiereMenosMovimiento, webglDisponible } from "./utils"

export type EstadoEsfera = "integrado" | "en_curso" | "pendiente" | "vencido"

export interface EsferaProgreso {
  id: string
  estado: EstadoEsfera
  seccionesTotal: number
  seccionesCompletadas: number
}

/**
 * Núcleo de progreso del estudiante. El núcleo es el estudiante; cada
 * laboratorio asignado es una esfera más pequeña en órbita, con una luna por
 * sección (encendida si está completada). A más secciones hechas, más cerca
 * del núcleo orbita. Al terminar el laboratorio, la esfera se integra: viaja
 * en espiral hasta acoplarse a la superficie y el núcleo crece.
 *
 * `nuevas` son las esferas integradas desde la última visita: esas se ven
 * llegar. Es decorativa (aria-hidden); el panel de al lado dice lo mismo en texto.
 */
export default function NucleoProgreso({
  esferas,
  nuevas,
  alto = 320,
}: {
  esferas: EsferaProgreso[]
  nuevas: string[]
  alto?: number
}) {
  const contenedorRef = useRef<HTMLDivElement>(null)
  // La escena se arma una vez por combinación de datos: así un cambio de
  // estado (aceptar una invitación) la rehace sin depender de identidades de arrays.
  const firma = JSON.stringify([esferas, nuevas])

  useEffect(() => {
    const contenedor = contenedorRef.current
    if (!contenedor || !webglDisponible()) return
    const [lista, recien] = JSON.parse(firma) as [EsferaProgreso[], string[]]
    const quieto = prefiereMenosMovimiento()

    const escena = new THREE.Scene()
    const camara = new THREE.PerspectiveCamera(38, 1, 0.1, 100)
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.setClearColor(0x000000, 0)
    renderer.domElement.style.display = "block"
    contenedor.appendChild(renderer.domElement)

    const ambar = colorToken("--signal-amber", "#ffb020")
    const cian = colorToken("--signal-cyan", "#38d6f5")
    const verde = colorToken("--signal-green", "#33d69f")
    const rojo = colorToken("--signal-red", "#ff4757")
    const tenue = colorToken("--border-strong", "#3b4657")
    const apagado = colorToken("--text-dim", "#5b6677")

    escena.add(new THREE.AmbientLight(0xffffff, 0.45))
    const luzClave = new THREE.DirectionalLight(0xffffff, 1.7)
    luzClave.position.set(3, 4, 5)
    escena.add(luzClave)
    const luzBorde = new THREE.DirectionalLight(cian, 1.4)
    luzBorde.position.set(-5, 1.5, -3)
    escena.add(luzBorde)

    // Todo cuelga de `raiz`, que se inclina un poco hacia el puntero.
    const raiz = new THREE.Group()
    escena.add(raiz)

    const integradas = lista.filter((e) => e.estado === "integrado")
    const enOrbita = lista.filter((e) => e.estado !== "integrado")
    const nuevasSet = new Set(quieto ? [] : recien.filter((id) => integradas.some((e) => e.id === id)))
    const vacio = lista.length === 0

    // ── Núcleo ─────────────────────────────────────────────────────────
    const escalaPara = (n: number) => Math.min(0.62 + n * 0.08, 1.3)
    let escalaObjetivo = escalaPara(integradas.length - nuevasSet.size)
    let escalaActual = escalaObjetivo
    let impulso = 0

    const nucleo = new THREE.Group()
    raiz.add(nucleo)
    const geoNucleo = new THREE.SphereGeometry(1, 48, 32)
    const matNucleo = new THREE.MeshStandardMaterial({
      color: vacio ? tenue : ambar,
      emissive: vacio ? tenue : ambar,
      emissiveIntensity: vacio ? 0.15 : 0.32,
      roughness: 0.38,
      metalness: 0.15,
    })
    nucleo.add(new THREE.Mesh(geoNucleo, matNucleo))
    const geoCascara = new THREE.IcosahedronGeometry(1.24, 1)
    const cascara = new THREE.LineSegments(
      new THREE.EdgesGeometry(geoCascara),
      new THREE.LineBasicMaterial({ color: vacio ? apagado : ambar, transparent: true, opacity: 0.32 }),
    )
    geoCascara.dispose()
    nucleo.add(cascara)

    const texturaHalo = crearHalo(vacio ? apagado : ambar)
    const halo = new THREE.Sprite(new THREE.SpriteMaterial({ map: texturaHalo, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true }))
    raiz.add(halo)

    // Onda que sale del núcleo cada vez que se integra una esfera.
    const onda = new THREE.Mesh(
      new THREE.RingGeometry(1, 1.05, 72),
      new THREE.MeshBasicMaterial({ color: verde, transparent: true, opacity: 0, side: THREE.DoubleSide, depthWrite: false }),
    )
    raiz.add(onda)
    let ondaT = -1

    // ── Esferas integradas: acopladas a la superficie y girando con ella ──
    const giro = new THREE.Group()
    raiz.add(giro)
    const geoAcoplada = new THREE.SphereGeometry(0.17, 24, 16)
    const matAcoplada = new THREE.MeshStandardMaterial({ color: verde, emissive: verde, emissiveIntensity: 0.45, roughness: 0.3 })
    type Acoplada = { malla: THREE.Mesh; dir: THREE.Vector3; id: string }
    const acopladas: Acoplada[] = integradas.map((e, i) => {
      const malla = new THREE.Mesh(geoAcoplada, matAcoplada)
      malla.visible = !nuevasSet.has(e.id)
      giro.add(malla)
      return { malla, dir: puntoFibonacci(i, integradas.length), id: e.id }
    })

    // ── Esferas en órbita: laboratorios sin terminar ────────────────────
    const geoPlaneta = new THREE.SphereGeometry(0.25, 24, 16)
    const geoLuna = new THREE.SphereGeometry(0.08, 12, 8)
    type Orbital = { plano: THREE.Group; planeta: THREE.Mesh; lunas: THREE.Mesh[]; radio: number; fase: number; velocidad: number }
    const orbitales: Orbital[] = enOrbita.map((e, i) => {
      const avance = e.seccionesTotal > 0 ? e.seccionesCompletadas / e.seccionesTotal : 0
      const radio = e.estado === "pendiente" ? 4.3 : e.estado === "vencido" ? 4.0 : 3.9 - avance * 1.5
      const color = e.estado === "en_curso" ? cian : e.estado === "vencido" ? rojo : apagado

      const plano = new THREE.Group()
      plano.rotation.x = 0.18 + ((i * 53) % 7) * 0.06
      plano.rotation.z = (((i * 31) % 9) - 4) * 0.07
      raiz.add(plano)

      const curva = new THREE.EllipseCurve(0, 0, radio, radio, 0, Math.PI * 2)
      const geoOrbita = new THREE.BufferGeometry().setFromPoints(curva.getPoints(128).map((p) => new THREE.Vector3(p.x, 0, p.y)))
      plano.add(new THREE.LineLoop(geoOrbita, new THREE.LineBasicMaterial({ color: tenue, transparent: true, opacity: e.estado === "en_curso" ? 0.55 : 0.3 })))

      const planeta = new THREE.Mesh(
        geoPlaneta,
        new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: e.estado === "pendiente" ? 0.05 : 0.35, roughness: 0.4 }),
      )
      plano.add(planeta)

      const lunas = Array.from({ length: e.seccionesTotal }, (_, s) => {
        const hecha = s < e.seccionesCompletadas
        const luna = new THREE.Mesh(
          geoLuna,
          new THREE.MeshBasicMaterial({ color: hecha ? cian : tenue, transparent: !hecha, opacity: hecha ? 1 : 0.7 }),
        )
        planeta.add(luna)
        return luna
      })

      return { plano, planeta, lunas, radio, fase: (i / Math.max(enOrbita.length, 1)) * Math.PI * 2, velocidad: 0.16 + (4.4 - radio) * 0.05 }
    })

    // ── Polvo de fondo ──────────────────────────────────────────────────
    const geoPolvo = new THREE.BufferGeometry()
    const posPolvo = new Float32Array(220 * 3)
    for (let i = 0; i < 220; i++) {
      const a = pseudoAzar(i) * Math.PI * 2
      const r = 2.4 + pseudoAzar(i + 500) * 3.4
      posPolvo.set([Math.cos(a) * r, (pseudoAzar(i + 900) - 0.5) * 0.9, Math.sin(a) * r], i * 3)
    }
    geoPolvo.setAttribute("position", new THREE.BufferAttribute(posPolvo, 3))
    const polvo = new THREE.Points(geoPolvo, new THREE.PointsMaterial({ color: cian, size: 0.03, transparent: true, opacity: 0.35, depthWrite: false }))
    polvo.rotation.x = 0.2
    raiz.add(polvo)

    // ── Vuelos de integración ───────────────────────────────────────────
    type Vuelo = {
      acoplada: Acoplada
      malla: THREE.Mesh
      estela: THREE.Line
      inicio: number
      anguloInicial: number
      hecho: boolean
      rastro: THREE.Vector3[]
      // Ángulo del destino del cuadro anterior (desenrollado, sin saltos de 2π) y barrido total.
      angPrevio: number | null
      ang0: number
      barrido: number
    }
    const geoVuelo = new THREE.SphereGeometry(0.2, 24, 16)
    const LARGO_ESTELA = 26
    const vuelos: Vuelo[] = acopladas
      .filter((a) => nuevasSet.has(a.id))
      .map((acoplada, i) => {
        const malla = new THREE.Mesh(geoVuelo, matAcoplada)
        malla.visible = false
        raiz.add(malla)
        const geoEstela = new THREE.BufferGeometry()
        geoEstela.setAttribute("position", new THREE.BufferAttribute(new Float32Array(LARGO_ESTELA * 3), 3))
        const colores = new Float32Array(LARGO_ESTELA * 3)
        for (let k = 0; k < LARGO_ESTELA; k++) {
          const f = 1 - k / LARGO_ESTELA
          colores.set([verde.r * f, verde.g * f, verde.b * f], k * 3)
        }
        geoEstela.setAttribute("color", new THREE.BufferAttribute(colores, 3))
        const estela = new THREE.Line(geoEstela, new THREE.LineBasicMaterial({ vertexColors: true, blending: THREE.AdditiveBlending, transparent: true, depthWrite: false }))
        estela.visible = false
        raiz.add(estela)
        return {
          acoplada, malla, estela,
          inicio: 1.0 + i * 0.8,
          anguloInicial: -0.6 + i * 2.1,
          hecho: false,
          rastro: [],
          angPrevio: null,
          ang0: 0,
          barrido: 0,
        }
      })
    const DURACION_VUELO = 1.9
    const destino = new THREE.Vector3()

    // ── Bucle ───────────────────────────────────────────────────────────
    const puntero = { x: 0, y: 0 }
    const alMover = (ev: PointerEvent) => {
      const r = contenedor.getBoundingClientRect()
      puntero.x = ((ev.clientX - r.left) / r.width) * 2 - 1
      puntero.y = ((ev.clientY - r.top) / r.height) * 2 - 1
    }
    const alSalir = () => {
      puntero.x = 0
      puntero.y = 0
    }
    if (!quieto) {
      contenedor.addEventListener("pointermove", alMover)
      contenedor.addEventListener("pointerleave", alSalir)
    }

    let previo = 0
    const dibujar = (t: number) => {
      const dt = Math.min(t - previo, 0.05)
      previo = t

      raiz.rotation.y += (puntero.x * 0.3 - raiz.rotation.y) * 0.05
      raiz.rotation.x += (puntero.y * 0.15 - raiz.rotation.x) * 0.05

      // Núcleo: crece hacia su objetivo y late un poco al recibir una esfera.
      escalaActual += (escalaObjetivo - escalaActual) * Math.min(dt * 4, 1)
      impulso *= Math.pow(0.02, dt)
      const respiro = vacio ? 1 + Math.sin(t * 1.4) * 0.03 : 1 + Math.sin(t * 1.1) * 0.012
      const escala = escalaActual * respiro * (1 + impulso)
      nucleo.scale.setScalar(escala)
      nucleo.rotation.y = t * 0.18
      cascara.rotation.y = -t * 0.32
      cascara.rotation.x = Math.sin(t * 0.3) * 0.2
      halo.scale.setScalar(escala * 4.4)
      giro.rotation.y = t * 0.18
      giro.rotation.x = Math.sin(t * 0.15) * 0.12
      polvo.rotation.y = t * 0.02

      for (const a of acopladas) a.malla.position.copy(a.dir).multiplyScalar(escala + 0.07)

      for (const o of orbitales) {
        const ang = o.fase + t * o.velocidad
        o.planeta.position.set(Math.cos(ang) * o.radio, Math.sin(t * 0.7 + o.fase) * 0.08, Math.sin(ang) * o.radio)
        o.lunas.forEach((luna, s) => {
          const al = t * 1.6 + (s / o.lunas.length) * Math.PI * 2
          luna.position.set(Math.cos(al) * 0.5, Math.sin(al) * 0.16, Math.sin(al) * 0.5)
        })
      }

      for (const v of vuelos) {
        if (v.hecho || t < v.inicio) continue
        const u = Math.min((t - v.inicio) / DURACION_VUELO, 1)
        const k = suave(u)
        // Destino: la posición actual del acople (gira con el núcleo), en coordenadas de `raiz`.
        destino.copy(v.acoplada.dir).multiplyScalar(escala + 0.07).applyEuler(giro.rotation)
        const rFin = Math.hypot(destino.x, destino.z)
        let angFin = Math.atan2(destino.z, destino.x)
        if (v.angPrevio === null) {
          // Primer cuadro: barrido hacia adelante de algo más de una vuelta hasta el destino.
          v.ang0 = angFin
          v.barrido = (((angFin - v.anguloInicial) % TAU) + TAU) % TAU + TAU
        } else {
          while (angFin - v.angPrevio > Math.PI) angFin -= TAU
          while (angFin - v.angPrevio < -Math.PI) angFin += TAU
        }
        v.angPrevio = angFin
        const radio = 4.2 + (rFin - 4.2) * k
        // En k = 1 coincide con angFin (módulo 2π): llega justo al acople aunque el núcleo gire.
        const ang = v.anguloInicial + (angFin - v.ang0 + v.barrido) * k
        const y = 1.2 * (1 - k) + destino.y * k
        v.malla.visible = true
        v.malla.position.set(Math.cos(ang) * radio, y, Math.sin(ang) * radio)
        v.malla.scale.setScalar(1 - 0.15 * k)

        v.rastro.unshift(v.malla.position.clone())
        if (v.rastro.length > LARGO_ESTELA) v.rastro.pop()
        const pos = v.estela.geometry.attributes.position as THREE.BufferAttribute
        for (let i = 0; i < LARGO_ESTELA; i++) {
          const p = v.rastro[Math.min(i, v.rastro.length - 1)]
          pos.setXYZ(i, p.x, p.y, p.z)
        }
        pos.needsUpdate = true
        v.estela.visible = true

        if (u >= 1) {
          v.hecho = true
          v.malla.visible = false
          v.estela.visible = false
          v.acoplada.malla.visible = true
          escalaObjetivo += 0.08
          impulso = 0.14
          ondaT = t
        }
      }

      if (ondaT >= 0) {
        const p = (t - ondaT) / 0.9
        if (p >= 1) {
          ondaT = -1
          ;(onda.material as THREE.MeshBasicMaterial).opacity = 0
        } else {
          onda.scale.setScalar(escala * (1.1 + p * 1.9))
          ;(onda.material as THREE.MeshBasicMaterial).opacity = 0.75 * (1 - p)
        }
      }
      onda.lookAt(camara.position)

      renderer.render(escena, camara)
    }

    const ajustar = () => {
      const ancho = contenedor.clientWidth || 1
      renderer.setSize(ancho, alto, false)
      renderer.domElement.style.width = "100%"
      renderer.domElement.style.height = `${alto}px`
      camara.aspect = ancho / alto
      camara.position.set(0, 2.3, ancho < 420 ? 13 : 10.5)
      camara.lookAt(0, 0, 0)
      camara.updateProjectionMatrix()
      if (quieto) dibujar(previo)
    }
    const observador = new ResizeObserver(ajustar)
    observador.observe(contenedor)
    ajustar()

    let visible = true
    const intersec = new IntersectionObserver(([e]) => (visible = e.isIntersecting))
    intersec.observe(contenedor)

    let raf = 0
    const reloj = new THREE.Clock()
    let tiempo = 0
    const bucle = () => {
      raf = requestAnimationFrame(bucle)
      const dt = reloj.getDelta()
      // El tiempo de la escena solo corre mientras se ve: los vuelos no se
      // "gastan" con la pestaña oculta o el panel fuera de pantalla.
      if (!visible || document.hidden) return
      tiempo += Math.min(dt, 0.05)
      dibujar(tiempo)
    }
    if (quieto) dibujar(2)
    else bucle()

    return () => {
      cancelAnimationFrame(raf)
      observador.disconnect()
      intersec.disconnect()
      contenedor.removeEventListener("pointermove", alMover)
      contenedor.removeEventListener("pointerleave", alSalir)
      liberar(escena)
      texturaHalo.dispose()
      renderer.dispose()
      renderer.domElement.remove()
    }
  }, [firma, alto])

  return <div ref={contenedorRef} aria-hidden="true" className="w-full" style={{ height: alto }} />
}

const TAU = Math.PI * 2

/** Reparte n puntos de forma pareja sobre una esfera unitaria (espiral de Fibonacci). */
function puntoFibonacci(i: number, n: number): THREE.Vector3 {
  const y = 1 - ((i + 0.5) / n) * 2
  const r = Math.sqrt(1 - y * y)
  const theta = i * Math.PI * (3 - Math.sqrt(5))
  return new THREE.Vector3(Math.cos(theta) * r, y, Math.sin(theta) * r)
}

function suave(u: number): number {
  return u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2
}

/** Azar determinista: la misma nube de polvo en cada render. */
function pseudoAzar(i: number): number {
  const x = Math.sin(i * 12.9898) * 43758.5453
  return x - Math.floor(x)
}

function crearHalo(color: THREE.Color): THREE.CanvasTexture {
  const lienzo = document.createElement("canvas")
  lienzo.width = lienzo.height = 128
  const ctx = lienzo.getContext("2d")!
  const c = { r: 0, g: 0, b: 0 }
  color.getRGB(c, THREE.SRGBColorSpace)
  const rgb = `${Math.round(c.r * 255)},${Math.round(c.g * 255)},${Math.round(c.b * 255)}`
  const grad = ctx.createRadialGradient(64, 64, 0, 64, 64, 64)
  grad.addColorStop(0, `rgba(${rgb},0.55)`)
  grad.addColorStop(0.35, `rgba(${rgb},0.18)`)
  grad.addColorStop(1, `rgba(${rgb},0)`)
  ctx.fillStyle = grad
  ctx.fillRect(0, 0, 128, 128)
  const textura = new THREE.CanvasTexture(lienzo)
  textura.colorSpace = THREE.SRGBColorSpace
  return textura
}
