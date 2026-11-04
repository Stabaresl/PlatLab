/**
 * ¿El navegador puede dibujar WebGL? Vive fuera de components/three para que
 * las páginas decidan si cargan una escena sin arrastrar three.js a su chunk.
 */
export function webglDisponible(): boolean {
  try {
    const canvas = document.createElement("canvas")
    return Boolean(canvas.getContext("webgl2") || canvas.getContext("webgl"))
  } catch {
    return false
  }
}
