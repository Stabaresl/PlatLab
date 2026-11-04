import type { ComponentType, SVGProps } from "react"
import {
  IconAudifonos, IconAura, IconBackpack, IconGlasses, IconGorra, IconGuantes,
  IconHoodie, IconInsignia, IconMarco, IconMask, IconZapatos,
} from "../components/icons"
import type { RarezaCosmetico, TipoCosmetico } from "../pages/api"

/** Un ícono por tipo de pieza: el mismo en el avatar, el inventario y los logros. */
export const ICONO_COSMETICO: Record<TipoCosmetico, ComponentType<SVGProps<SVGSVGElement>>> = {
  hoodie: IconHoodie,
  gafas: IconGlasses,
  mascara: IconMask,
  aura: IconAura,
  insignia: IconInsignia,
  mochila: IconBackpack,
  guantes: IconGuantes,
  zapatos: IconZapatos,
  gorra: IconGorra,
  audifonos: IconAudifonos,
  marco: IconMarco,
}

export const TIPO_LABEL: Record<TipoCosmetico, string> = {
  hoodie: "Hoodie", gafas: "Gafas", mascara: "Máscara", aura: "Aura", insignia: "Insignia",
  mochila: "Mochila", guantes: "Guantes", zapatos: "Zapatos", gorra: "Gorra", audifonos: "Audífonos",
  marco: "Marco",
}

export const RAREZA_LABEL: Record<RarezaCosmetico, string> = {
  comun: "Común",
  poco_comun: "Poco común",
  raro: "Raro",
  epico: "Épico",
  legendario: "Legendario",
  mitico: "Mítico",
}

// Rarezas sin señal propia en el sistema (legendario/mítico) usan un color
// fijo de colección; el resto reusa las señales de la plataforma.
export const RAREZA_COLOR: Record<RarezaCosmetico, string> = {
  comun: "var(--text-muted)",
  poco_comun: "var(--signal-cyan)",
  raro: "var(--signal-green)",
  epico: "var(--signal-amber)",
  legendario: "rgb(168,85,247)",
  mitico: "rgb(236,72,153)",
}

export const ORDEN_RAREZA: RarezaCosmetico[] = ["comun", "poco_comun", "raro", "epico", "legendario", "mitico"]
