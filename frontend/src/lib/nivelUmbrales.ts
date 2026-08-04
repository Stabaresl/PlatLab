// Espejo de `modules/gamification/domain/entities.py::NIVEL_UMBRALES` —
// mismo criterio que `avatarPresets.ts`: el perfil ya trae `xp` y
// `xp_para_siguiente_nivel` (el umbral de arriba), pero para dibujar una
// barra de progreso hace falta también el umbral de abajo (dónde
// arrancó el nivel actual), que la API no expone — más simple duplicar
// la tabla fija acá que agregar un campo nuevo solo para esto.
export const NIVEL_UMBRALES = [0, 100, 250, 450, 700, 1000, 1400, 1900, 2500, 3200, 4000]

export function xpProgress(xp: number, xpParaSiguienteNivel: number | null): { percent: number; umbralActual: number } {
  if (xpParaSiguienteNivel === null) {
    return { percent: 100, umbralActual: NIVEL_UMBRALES[NIVEL_UMBRALES.length - 1] }
  }
  const idx = NIVEL_UMBRALES.indexOf(xpParaSiguienteNivel)
  const umbralActual = idx > 0 ? NIVEL_UMBRALES[idx - 1] : 0
  const rango = xpParaSiguienteNivel - umbralActual
  const percent = rango > 0 ? Math.round(((xp - umbralActual) / rango) * 100) : 100
  return { percent: Math.min(100, Math.max(0, percent)), umbralActual }
}
