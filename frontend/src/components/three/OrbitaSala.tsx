import { useEffect, useRef } from "react"
import * as THREE from "three"
import { colorToken, liberar, prefiereMenosMovimiento, webglDisponible } from "./utils"

export interface NodoOrbita {
  id: string
  porcentaje: number
  completado: boolean
  esYo: boolean
}

/**
 * Lobby 3D de una sala: el laboratorio es el núcleo y cada participante un
 * nodo en órbita. A más avance, más cerca del núcleo; quien termina queda
 * acoplado (verde) con un enlace al centro. Es decorativa (aria-hidden): el
 * tablero de al lado tiene la misma información en texto.
 */
export default function OrbitaSala({ nodos, alto = 340 }: { nodos: NodoOrbita[]; alto?: number }) {
  const contenedorRef = useRef<HTMLDivElement>(null)
  const nodosRef = useRef(nodos)
  const reconstruirRef = useRef<(() => void) | null>(null)

  useEffect(() => {
    nodosRef.current = nodos
    reconstruirRef.current?.()
  }, [nodos])

  useEffect(() => {
    const contenedor = contenedorRef.current
    if (!contenedor || !webglDisponible()) return
    const quieto = prefiereMenosMovimiento()

    const escena = new THREE.Scene()
    const camara = new THREE.PerspectiveCamera(42, 1, 0.1, 100)
    camara.position.set(0, 2.4, 9.5)
    // Mira un poco por debajo del centro: la escena sube y la franja de cifras no tapa las órbitas.
    camara.lookAt(0, -0.9, 0)
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.setClearColor(0x000000, 0)
    contenedor.appendChild(renderer.domElement)
    renderer.domElement.style.display = "block"

    const ambar = colorToken("--signal-amber", "#ffb020")
    const cian = colorToken("--signal-cyan", "#38d6f5")
    const verde = colorToken("--signal-green", "#33d69f")
    const tenue = colorToken("--border-strong", "#3b4657")

    // Núcleo: el laboratorio.
    const nucleo = new THREE.Group()
    const ico = new THREE.IcosahedronGeometry(1.05, 1)
    nucleo.add(new THREE.LineSegments(new THREE.EdgesGeometry(ico), new THREE.LineBasicMaterial({ color: ambar, transparent: true, opacity: 0.9 })))
    nucleo.add(new THREE.Mesh(new THREE.IcosahedronGeometry(0.62, 0), new THREE.MeshBasicMaterial({ color: ambar, transparent: true, opacity: 0.16 })))
    escena.add(nucleo)
    ico.dispose()

    // Anillos de órbita.
    const anillos = new THREE.Group()
    const radiosAnillo = [2.1, 3.0, 3.9]
    radiosAnillo.forEach((r, i) => {
      const curva = new THREE.EllipseCurve(0, 0, r, r, 0, Math.PI * 2)
      const geo = new THREE.BufferGeometry().setFromPoints(curva.getPoints(128).map((p) => new THREE.Vector3(p.x, 0, p.y)))
      const linea = new THREE.LineLoop(geo, new THREE.LineBasicMaterial({ color: tenue, transparent: true, opacity: 0.55 - i * 0.12 }))
      anillos.add(linea)
    })
    anillos.rotation.x = 0.12
    escena.add(anillos)

    // Participantes.
    const participantes = new THREE.Group()
    participantes.rotation.x = 0.12
    escena.add(participantes)
    type Datos = { angulo: number; radio: number; velocidad: number; alturaFase: number }
    let datos: Datos[] = []
    const geoNodo = new THREE.SphereGeometry(0.11, 16, 12)
    const geoHalo = new THREE.RingGeometry(0.18, 0.22, 24)

    const reconstruir = () => {
      liberarHijos(participantes, [geoNodo, geoHalo])
      const lista = nodosRef.current
      datos = lista.map((n, i) => {
        // Radio: de la órbita externa (0 %) a una dársena junto al núcleo (100 %).
        const radio = n.completado ? 1.45 : radiosAnillo[2] - (n.porcentaje / 100) * (radiosAnillo[2] - radiosAnillo[0])
        return { angulo: (i / Math.max(lista.length, 1)) * Math.PI * 2, radio, velocidad: 0.08 + ((i * 37) % 10) / 120, alturaFase: i * 1.7 }
      })
      lista.forEach((n) => {
        const color = n.completado ? verde : n.porcentaje > 0 ? cian : tenue
        const nodo = new THREE.Mesh(geoNodo, new THREE.MeshBasicMaterial({ color }))
        if (n.esYo) {
          const halo = new THREE.Mesh(geoHalo, new THREE.MeshBasicMaterial({ color: ambar, side: THREE.DoubleSide, transparent: true, opacity: 0.9 }))
          halo.name = "halo"
          nodo.add(halo)
          nodo.scale.setScalar(1.35)
        }
        participantes.add(nodo)
        if (n.completado) {
          const enlaceGeo = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()])
          const enlace = new THREE.Line(enlaceGeo, new THREE.LineBasicMaterial({ color: verde, transparent: true, opacity: 0.35 }))
          enlace.name = "enlace"
          participantes.add(enlace)
          nodo.userData.enlace = enlace
        }
      })
    }
    reconstruir()
    reconstruirRef.current = () => {
      reconstruir()
      if (quieto) dibujar(0)
    }

    const posicionar = (t: number) => {
      let k = 0
      participantes.children.forEach((hijo) => {
        if (hijo.name === "enlace") return
        const d = datos[k++]
        if (!d) return
        const a = d.angulo + t * d.velocidad
        hijo.position.set(Math.cos(a) * d.radio, Math.sin(t * 0.6 + d.alturaFase) * 0.18, Math.sin(a) * d.radio)
        const halo = hijo.getObjectByName("halo")
        if (halo) halo.lookAt(camara.position)
        const enlace = hijo.userData.enlace as THREE.Line | undefined
        if (enlace) {
          const pos = enlace.geometry.attributes.position as THREE.BufferAttribute
          pos.setXYZ(1, hijo.position.x, hijo.position.y, hijo.position.z)
          pos.needsUpdate = true
        }
      })
    }

    const dibujar = (t: number) => {
      nucleo.rotation.y = t * 0.25
      nucleo.rotation.x = Math.sin(t * 0.2) * 0.15
      posicionar(t)
      renderer.render(escena, camara)
    }

    const ajustar = () => {
      const ancho = contenedor.clientWidth || 1
      renderer.setSize(ancho, alto, false)
      renderer.domElement.style.width = "100%"
      renderer.domElement.style.height = `${alto}px`
      camara.aspect = ancho / alto
      // En pantallas angostas se aleja la cámara para que las órbitas quepan.
      camara.position.z = ancho < 420 ? 12.5 : 9.5
      camara.updateProjectionMatrix()
      if (quieto) dibujar(0)
    }
    const observador = new ResizeObserver(ajustar)
    observador.observe(contenedor)
    ajustar()

    let visible = true
    const intersec = new IntersectionObserver(([e]) => (visible = e.isIntersecting))
    intersec.observe(contenedor)

    let raf = 0
    const reloj = new THREE.Clock()
    const bucle = () => {
      raf = requestAnimationFrame(bucle)
      if (!visible || document.hidden) return
      dibujar(reloj.getElapsedTime())
    }
    if (quieto) dibujar(0)
    else bucle()

    return () => {
      cancelAnimationFrame(raf)
      observador.disconnect()
      intersec.disconnect()
      reconstruirRef.current = null
      liberar(escena)
      geoNodo.dispose()
      geoHalo.dispose()
      renderer.dispose()
      renderer.domElement.remove()
    }
  }, [alto])

  return <div ref={contenedorRef} aria-hidden="true" className="w-full" style={{ height: alto }} />
}

/** Quita los hijos de un grupo liberando materiales (las geometrías compartidas se conservan). */
function liberarHijos(grupo: THREE.Group, compartidas: THREE.BufferGeometry[]) {
  for (const hijo of [...grupo.children]) {
    hijo.traverse((o) => {
      const m = o as THREE.Mesh
      if (m.geometry && !compartidas.includes(m.geometry)) m.geometry.dispose()
      const mat = m.material as THREE.Material | undefined
      mat?.dispose?.()
    })
    grupo.remove(hijo)
  }
}
