import * as THREE from "three"

/** Lee un token de color de :root (ej. "--signal-cyan") para que las escenas 3D usen la misma paleta que el CSS. */
export function colorToken(nombre: string, respaldo = "#38d6f5"): THREE.Color {
  const valor = getComputedStyle(document.documentElement).getPropertyValue(nombre).trim()
  try {
    return new THREE.Color(valor || respaldo)
  } catch {
    return new THREE.Color(respaldo)
  }
}

export function prefiereMenosMovimiento(): boolean {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches
}

/** Libera geometrías y materiales de un objeto y sus hijos (evita fugas de memoria de WebGL). */
export function liberar(objeto: THREE.Object3D) {
  objeto.traverse((o) => {
    const malla = o as THREE.Mesh
    malla.geometry?.dispose()
    const material = malla.material as THREE.Material | THREE.Material[] | undefined
    if (Array.isArray(material)) material.forEach((m) => m.dispose())
    else material?.dispose()
  })
}

export function webglDisponible(): boolean {
  try {
    const canvas = document.createElement("canvas")
    return Boolean(canvas.getContext("webgl2") || canvas.getContext("webgl"))
  } catch {
    return false
  }
}
