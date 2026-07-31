// Espejo de `modules/gamification/domain/entities.py::AVATAR_PRESETS` —
// dato de catálogo fijo (no configurable en v1), igual que el backend
// nunca cambia esta lista sin tocar código en ambos lados. Se podría
// pedir a `GET /gamification/avatar-presets/` en vez de duplicarlo,
// pero como `AvatarBadge` necesita el emoji/color de forma síncrona en
// cualquier parte de la app (Navbar incluido) sin depender de un fetch
// adicional, mantenerlo como constante local es más simple.
export interface AvatarPreset {
  clave: string
  nombre: string
  emoji: string
  color: string
}

export const AVATAR_PRESETS: AvatarPreset[] = [
  { clave: "operador_nocturno", nombre: "Operador Nocturno", emoji: "🥷", color: "56,214,245" },
  { clave: "ingeniera_red", nombre: "Ingeniera de Red", emoji: "👩‍💻", color: "51,214,159" },
  { clave: "ingeniero_sistemas", nombre: "Ingeniero de Sistemas", emoji: "👨‍💻", color: "255,176,32" },
  { clave: "analista_soc", nombre: "Analista SOC", emoji: "🕵️", color: "255,71,87" },
  { clave: "unidad_autonoma", nombre: "Unidad Autónoma", emoji: "🤖", color: "136,146,163" },
  { clave: "vector_amenaza", nombre: "Vector de Amenaza", emoji: "👾", color: "186,85,255" },
  { clave: "explorador_digital", nombre: "Explorador Digital", emoji: "🧑‍🚀", color: "236,72,153" },
  { clave: "fantasma_red", nombre: "Fantasma de la Red", emoji: "👻", color: "230,230,230" },
]

const _POR_CLAVE = new Map(AVATAR_PRESETS.map((p) => [p.clave, p]))

export function getAvatarPreset(clave: string): AvatarPreset {
  return _POR_CLAVE.get(clave) || AVATAR_PRESETS[0]
}
