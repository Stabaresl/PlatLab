/**
 * Rasgos de cada personaje predeterminado (lib/avatarPresets.ts) para la
 * ilustración SVG de AvatarPersonaje. Es la paleta de la ilustración (piel,
 * cabello, ropa base), no de la interfaz: vive aquí, en un solo lugar, igual
 * que los colores de los cosméticos vienen del catálogo del backend.
 */

export type TipoCabeza = "humana" | "robot" | "alien" | "fantasma"
export type Peinado = "corto" | "largo" | "ninja" | "sombrero" | "ninguno"

export interface Rasgos {
  cabeza: TipoCabeza
  piel: string
  cabello: string
  peinado: Peinado
  casco: boolean
  // Acento de la ropa base (cuello y cremallera): el color del personaje.
  acento: string
}

export const PALETA = {
  ropaBase: "#252b38",
  ropaSombra: "#1b2029",
  pantalon: "#171b24",
  zapatoBase: "#3a4150",
  suela: "#d8dde6",
  ojos: "#141820",
  tela: "#1e222b",
  metal: "#9aa3b5",
  metalSombra: "#6b7385",
  fantasma: "#eef1f6",
  vidrio: "#dfe6ee",
  sombrero: "#3a3f4b",
} as const

const PIEL = { clara: "#f1c7a5", media: "#d9a07a", morena: "#a8704c" }
const CABELLO = { negro: "#1d1d24", castano: "#5b3a24", rubio: "#d6b25e" }

const RASGOS: Record<string, Rasgos> = {
  operador_nocturno: { cabeza: "humana", piel: PIEL.media, cabello: CABELLO.negro, peinado: "ninja", casco: false, acento: "56,214,245" },
  ingeniera_red: { cabeza: "humana", piel: PIEL.morena, cabello: CABELLO.castano, peinado: "largo", casco: false, acento: "51,214,159" },
  ingeniero_sistemas: { cabeza: "humana", piel: PIEL.clara, cabello: CABELLO.negro, peinado: "corto", casco: false, acento: "255,176,32" },
  analista_soc: { cabeza: "humana", piel: PIEL.media, cabello: CABELLO.negro, peinado: "sombrero", casco: false, acento: "255,71,87" },
  unidad_autonoma: { cabeza: "robot", piel: PALETA.metal, cabello: CABELLO.negro, peinado: "ninguno", casco: false, acento: "136,146,163" },
  vector_amenaza: { cabeza: "alien", piel: "#9b6cf0", cabello: CABELLO.negro, peinado: "ninguno", casco: false, acento: "186,85,255" },
  explorador_digital: { cabeza: "humana", piel: PIEL.clara, cabello: CABELLO.rubio, peinado: "corto", casco: true, acento: "236,72,153" },
  fantasma_red: { cabeza: "fantasma", piel: PALETA.fantasma, cabello: CABELLO.negro, peinado: "ninguno", casco: false, acento: "230,230,230" },
}

export function rasgosDe(clave: string | null | undefined): Rasgos {
  return (clave && RASGOS[clave]) || RASGOS.operador_nocturno
}
