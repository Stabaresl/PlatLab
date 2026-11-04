import { useEffect, useRef } from "react"
import * as THREE from "three"
import { colorToken, liberar, prefiereMenosMovimiento, webglDisponible } from "./utils"

/**
 * Globo de red para el héroe de bienvenida: una esfera de puntos (hosts) con
 * enlaces que se trazan entre ellos, como paquetes cruzando la red. Pura
 * ambientación (aria-hidden); con movimiento reducido queda en un cuadro fijo.
 */
export default function RedGlobo({ alto = 460 }: { alto?: number }) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const contenedor = ref.current
    if (!contenedor || !webglDisponible()) return
    const quieto = prefiereMenosMovimiento()

    const escena = new THREE.Scene()
    const camara = new THREE.PerspectiveCamera(38, 1, 0.1, 100)
    camara.position.set(0, 0, 7.2)
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.setClearColor(0x000000, 0)
    renderer.domElement.style.display = "block"
    contenedor.appendChild(renderer.domElement)

    const cian = colorToken("--signal-cyan", "#38d6f5")
    const ambar = colorToken("--signal-amber", "#ffb020")
    const tenue = colorToken("--border-strong", "#3b4657")

    const globo = new THREE.Group()
    globo.rotation.z = 0.32
    escena.add(globo)

    // Puntos distribuidos de forma pareja (esfera de Fibonacci).
    const N = 720
    const R = 2.2
    const puntos: THREE.Vector3[] = []
    const posiciones = new Float32Array(N * 3)
    for (let i = 0; i < N; i++) {
      const y = 1 - (i / (N - 1)) * 2
      const r = Math.sqrt(1 - y * y)
      const theta = Math.PI * (3 - Math.sqrt(5)) * i
      const v = new THREE.Vector3(Math.cos(theta) * r, y, Math.sin(theta) * r).multiplyScalar(R)
      puntos.push(v)
      posiciones.set([v.x, v.y, v.z], i * 3)
    }
    const geoPuntos = new THREE.BufferGeometry()
    geoPuntos.setAttribute("position", new THREE.BufferAttribute(posiciones, 3))
    globo.add(new THREE.Points(geoPuntos, new THREE.PointsMaterial({ color: tenue, size: 0.035, transparent: true, opacity: 0.9 })))

    // Malla de latitud muy tenue para dar volumen.
    const esfera = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.IcosahedronGeometry(R * 0.995, 2)), new THREE.LineBasicMaterial({ color: tenue, transparent: true, opacity: 0.12 }))
    globo.add(esfera)

    // Arcos entre hosts: se dibujan progresivamente y se reemplazan.
    type Arco = { linea: THREE.Line; total: number; nacido: number; vida: number; nodos: THREE.Mesh[] }
    const arcos: Arco[] = []
    const geoNodo = new THREE.SphereGeometry(0.045, 10, 8)
    const crearArco = (t: number) => {
      const a = puntos[Math.floor(Math.random() * N)]
      const b = puntos[Math.floor(Math.random() * N)]
      if (a.distanceTo(b) < 1.2) return
      const medio = a.clone().add(b).multiplyScalar(0.5).normalize().multiplyScalar(R + a.distanceTo(b) * 0.38)
      const curva = new THREE.QuadraticBezierCurve3(a, medio, b)
      const geo = new THREE.BufferGeometry().setFromPoints(curva.getPoints(64))
      geo.setDrawRange(0, 0)
      const color = Math.random() < 0.22 ? ambar : cian
      const linea = new THREE.Line(geo, new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.85 }))
      const nodos = [a, b].map((p) => {
        const m = new THREE.Mesh(geoNodo, new THREE.MeshBasicMaterial({ color }))
        m.position.copy(p)
        globo.add(m)
        return m
      })
      globo.add(linea)
      arcos.push({ linea, total: 65, nacido: t, vida: 3.4 + Math.random() * 2, nodos })
    }
    for (let i = 0; i < 9; i++) crearArco(-i * 0.4)

    const dibujar = (t: number) => {
      globo.rotation.y = t * 0.07
      for (let i = arcos.length - 1; i >= 0; i--) {
        const arco = arcos[i]
        const edad = t - arco.nacido
        const avance = Math.min(edad / 1.4, 1)
        arco.linea.geometry.setDrawRange(0, Math.floor(arco.total * (quieto ? 1 : avance)))
        const desvanecer = quieto ? 1 : Math.max(0, 1 - Math.max(0, edad - arco.vida) / 0.8)
        ;(arco.linea.material as THREE.LineBasicMaterial).opacity = 0.85 * desvanecer
        if (!quieto && desvanecer <= 0) {
          globo.remove(arco.linea, ...arco.nodos)
          arco.linea.geometry.dispose()
          ;(arco.linea.material as THREE.Material).dispose()
          arco.nodos.forEach((n) => (n.material as THREE.Material).dispose())
          arcos.splice(i, 1)
        }
      }
      if (!quieto && arcos.length < 9) crearArco(t)
      renderer.render(escena, camara)
    }

    const ajustar = () => {
      const ancho = contenedor.clientWidth || 1
      renderer.setSize(ancho, alto, false)
      renderer.domElement.style.width = "100%"
      renderer.domElement.style.height = `${alto}px`
      camara.aspect = ancho / alto
      camara.position.z = ancho < 480 ? 8.6 : 7.2
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
      liberar(escena)
      geoNodo.dispose()
      renderer.dispose()
      renderer.domElement.remove()
    }
  }, [alto])

  return <div ref={ref} aria-hidden="true" className="w-full" style={{ height: alto }} />
}
