import { motion } from "framer-motion"
import useReducedMotion from "../hooks/useReducedMotion"
import AvatarPersonaje from "./avatar/AvatarPersonaje"
import { piezasPuestas } from "../lib/cosmeticos"
import { resolveMediaUrl } from "../pages/api"
import type { PerfilJugador, RarezaCosmetico } from "../pages/api"

const RAREZA_GLOW: Record<RarezaCosmetico, string> = {
  comun: "136,146,163",
  poco_comun: "56,214,245",
  raro: "51,214,159",
  epico: "255,176,32",
  legendario: "186,85,255",
  mitico: "255,60,172",
}

// El avatar de PlatLAB: un personaje ilustrado (AvatarPersonaje) con todo lo
// equipado puesto en el cuerpo. En la barra de navegación se ve solo la
// cabeza; en el perfil, el cuerpo entero con el título debajo.
export default function AvatarBadge({
  perfil,
  size = "lg",
  tituloNombre,
}: {
  perfil: PerfilJugador | null
  size?: "sm" | "lg"
  tituloNombre?: string | null
}) {
  const reduced = useReducedMotion()
  const piezas = piezasPuestas(perfil)
  const preset = perfil?.avatar_tipo === "preset" ? perfil.avatar_valor : null
  const foto = perfil?.avatar_tipo === "subido" ? resolveMediaUrl(perfil.avatar_valor) : null
  const aura = perfil?.cosmeticos.find((c) => c.equipado && c.tipo === "aura")
  const marco = perfil?.cosmeticos.find((c) => c.equipado && c.tipo === "marco")
  const titulo = perfil ? `Nivel ${perfil.nivel} · ${perfil.xp} XP` : undefined

  if (size === "sm") {
    return (
      <span
        className="chamfer-sm flex items-center justify-center overflow-hidden shrink-0"
        title={titulo}
        style={{
          width: 30,
          height: 30,
          backgroundColor: "var(--surface)",
          border: `1px solid ${marco ? `rgb(${marco.color})` : "var(--border-default)"}`,
          boxShadow: aura ? `0 0 8px rgba(${RAREZA_GLOW[aura.rareza]}, 0.6)` : undefined,
        }}
      >
        <AvatarPersonaje preset={preset} foto={foto} piezas={piezas.filter((p) => p.tipo !== "marco")} ancho={30} vista="cabeza" animado={false} />
      </span>
    )
  }

  return (
    <div className="inline-flex flex-col items-center gap-2">
      <div
        className="chamfer flex items-end justify-center"
        title={titulo}
        style={{
          width: 156,
          height: 196,
          padding: "10px 12px 8px",
          background: "radial-gradient(circle at 50% 38%, var(--surface-raised), var(--surface-sunken) 72%)",
          border: "1px solid var(--border-default)",
        }}
      >
        <AvatarPersonaje preset={preset} foto={foto} piezas={piezas} ancho={132} animado={!reduced} titulo="Tu avatar con el equipo puesto" />
      </div>
      {tituloNombre && (
        <motion.span
          key={tituloNombre}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-[10px] uppercase tracking-widest"
          style={{ color: "var(--signal-amber)", fontFamily: "var(--font-mono)" }}
        >
          {tituloNombre}
        </motion.span>
      )}
    </div>
  )
}
