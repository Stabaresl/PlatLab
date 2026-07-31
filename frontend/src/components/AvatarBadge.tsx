import useReducedMotion from "../hooks/useReducedMotion"
import { getAvatarPreset } from "../lib/avatarPresets"
import { resolveMediaUrl } from "../pages/api"
import { IconGlasses, IconMask } from "./icons"
import type { PerfilJugador, RarezaCosmetico } from "../pages/api"

const RAREZA_GLOW: Record<RarezaCosmetico, string> = {
  comun: "136,146,163",
  poco_comun: "56,214,245",
  raro: "51,214,159",
  epico: "255,176,32",
  legendario: "186,85,255",
  mitico: "255,60,172",
}

// El "avatar" de GAIA — no un personaje 3D (ver decisión de alcance),
// sino una insignia de operador. El centro es la identidad elegida
// (emoji predeterminado o foto subida); lo que se equipa se dibuja
// como capas alrededor: marco = borde exterior, aura = glow pulsante,
// máscara/gafas = accesorio chico en la esquina, insignias = chips
// debajo. Mismo lenguaje visual "Tactical Ops Console" del resto de la
// plataforma (chamfer, colores señal) en vez de dibujar ropa realista.
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
  const dimension = size === "lg" ? 96 : 30
  const equipados = perfil?.cosmeticos.filter((c) => c.equipado) ?? []

  const marco = equipados.find((c) => c.tipo === "marco")
  const aura = equipados.find((c) => c.tipo === "aura")
  const mascara = equipados.find((c) => c.tipo === "mascara")
  const gafas = equipados.find((c) => c.tipo === "gafas")
  const accesorio = mascara || gafas
  const insignias = equipados.filter((c) => c.tipo === "insignia")

  const glowAura = aura ? RAREZA_GLOW[aura.rareza] : null
  const preset = perfil && perfil.avatar_tipo === "preset" ? getAvatarPreset(perfil.avatar_valor) : null
  const marcoColor = marco ? `rgb(${marco.color})` : null

  return (
    <div className="inline-flex flex-col items-center gap-2">
      <div
        className="relative chamfer flex items-center justify-center shrink-0"
        style={{
          width: dimension,
          height: dimension,
          padding: marcoColor ? 3 : 0,
          border: marcoColor ? `2px solid ${marcoColor}` : undefined,
        }}
        title={perfil ? `Nivel ${perfil.nivel} · ${perfil.xp} XP` : undefined}
      >
        <div
          className="relative chamfer-sm flex items-center justify-center w-full h-full overflow-hidden"
          style={{
            backgroundColor: "var(--surface)",
            border: "2px solid var(--border-default)",
            boxShadow: glowAura ? `0 0 ${size === "lg" ? 18 : 8}px rgba(${glowAura}, 0.65)` : undefined,
            animation: glowAura && !reduced ? "avatar-aura-pulse 2.2s ease-in-out infinite" : undefined,
          }}
        >
          {perfil?.avatar_tipo === "subido" ? (
            <img
              src={resolveMediaUrl(perfil.avatar_valor)}
              alt="Tu avatar"
              className="w-full h-full object-cover"
            />
          ) : (
            <span style={{ fontSize: dimension * 0.5, lineHeight: 1 }}>{preset?.emoji ?? "🥷"}</span>
          )}

          {accesorio && (
            <span
              title={accesorio.nombre}
              className="absolute bottom-0 right-0 flex items-center justify-center chamfer-sm"
              style={{
                width: size === "lg" ? 26 : 12,
                height: size === "lg" ? 26 : 12,
                backgroundColor: "var(--canvas-raised)",
                border: `1px solid rgb(${accesorio.color})`,
              }}
            >
              {mascara ? (
                <IconMask width={size === "lg" ? 15 : 7} height={size === "lg" ? 15 : 7} style={{ color: `rgb(${accesorio.color})` }} />
              ) : (
                <IconGlasses width={size === "lg" ? 15 : 7} height={size === "lg" ? 15 : 7} style={{ color: `rgb(${accesorio.color})` }} />
              )}
            </span>
          )}
        </div>
      </div>

      {size === "lg" && tituloNombre && (
        <span className="text-[10px] uppercase tracking-widest" style={{ color: "var(--signal-amber)", fontFamily: "var(--font-mono)" }}>
          {tituloNombre}
        </span>
      )}

      {size === "lg" && insignias.length > 0 && (
        <div className="flex gap-1 flex-wrap justify-center" style={{ maxWidth: 140 }}>
          {insignias.map((item) => (
            <span
              key={item.id}
              title={item.nombre}
              className="chamfer-sm w-3 h-3"
              style={{ backgroundColor: `rgb(${item.color})` }}
            />
          ))}
        </div>
      )}
    </div>
  )
}
