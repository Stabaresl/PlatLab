export const NIVEL_LABEL: Record<string, string> = {
  basico: "Básico",
  intermedio: "Intermedio",
  avanzado: "Avanzado",
}

/** "hace 3 min" a partir de una fecha ISO — para "última actividad" del tablero. */
export function haceCuanto(iso: string | null): string {
  if (!iso) return "—"
  const s = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 1000))
  if (s < 60) return "ahora"
  if (s < 3600) return `hace ${Math.floor(s / 60)} min`
  if (s < 86_400) return `hace ${Math.floor(s / 3600)} h`
  return `hace ${Math.floor(s / 86_400)} d`
}
