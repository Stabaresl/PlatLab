import type { CSSProperties } from "react"
import { AnimatePresence, motion } from "framer-motion"
import useReducedMotion from "../hooks/useReducedMotion"
import { getAvatarPreset } from "../lib/avatarPresets"
import { ICONO_COSMETICO, TIPO_LABEL } from "../lib/cosmeticos"
import { resolveMediaUrl } from "../pages/api"
import type { CosmeticoPerfilItem, PerfilJugador, RarezaCosmetico, TipoCosmetico } from "../pages/api"

const RAREZA_GLOW: Record<RarezaCosmetico, string> = {
  comun: "136,146,163",
  poco_comun: "56,214,245",
  raro: "51,214,159",
  epico: "255,176,32",
  legendario: "186,85,255",
  mitico: "255,60,172",
}

// Dónde va cada pieza alrededor de la insignia (tamaño grande). La gorra
// arriba, lo de las manos y la espalda a los lados, los zapatos abajo:
// se lee como un "equipo" sin dibujar un personaje.
const RANURAS: { tipo: TipoCosmetico; pos: CSSProperties }[] = [
  { tipo: "gorra", pos: { top: -15, left: "50%", marginLeft: -14 } },
  { tipo: "audifonos", pos: { top: 14, left: -17 } },
  { tipo: "guantes", pos: { top: 58, left: -17 } },
  { tipo: "mochila", pos: { top: 14, right: -17 } },
  { tipo: "hoodie", pos: { top: 58, right: -17 } },
  { tipo: "zapatos", pos: { bottom: -15, left: "50%", marginLeft: -14 } },
]

// El "avatar" de PlatLAB — no un personaje 3D (ver decisión de alcance),
// sino una insignia de operador. El centro es la identidad elegida
// (emoji predeterminado o foto subida); cada pieza equipada se ve:
// marco = borde exterior, aura = glow pulsante, hoodie = tinte de la
// parte baja, gafas/máscara = accesorio en la esquina, el resto = fichas
// alrededor que flotan, insignias = chips debajo.
export default function AvatarBadge({
  perfil,
  size = "lg",
  tituloNombre,
  ranurasVacias = false,
}: {
  perfil: PerfilJugador | null
  size?: "sm" | "lg"
  tituloNombre?: string | null
  // En el perfil se dibujan también las ranuras libres, para ver qué se puede equipar.
  ranurasVacias?: boolean
}) {
  const reduced = useReducedMotion()
  const grande = size === "lg"
  const dimension = grande ? 112 : 30
  const equipados = perfil?.cosmeticos.filter((c) => c.equipado) ?? []
  const porTipo = (tipo: TipoCosmetico) => equipados.find((c) => c.tipo === tipo)

  const marco = porTipo("marco")
  const aura = porTipo("aura")
  const hoodie = porTipo("hoodie")
  const accesorio = porTipo("mascara") || porTipo("gafas")
  const insignias = equipados.filter((c) => c.tipo === "insignia")

  const glowAura = aura ? RAREZA_GLOW[aura.rareza] : null
  const preset = perfil && perfil.avatar_tipo === "preset" ? getAvatarPreset(perfil.avatar_valor) : null
  const marcoColor = marco ? `rgb(${marco.color})` : null
  const IconoAccesorio = accesorio ? ICONO_COSMETICO[accesorio.tipo] : null

  return (
    <div className="inline-flex flex-col items-center gap-2" style={{ padding: grande ? "16px 18px 12px" : 0 }}>
      {/* Las ranuras van en este envoltorio sin clip-path: dentro de `.chamfer` quedarían recortadas. */}
      <div className="relative shrink-0" style={{ width: dimension, height: dimension }}>
      <div
        className="relative chamfer flex items-center justify-center w-full h-full"
        style={{
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
            boxShadow: glowAura ? `0 0 ${grande ? 22 : 8}px rgba(${glowAura}, 0.65)` : undefined,
            animation: glowAura && !reduced ? "avatar-aura-pulse 2.2s ease-in-out infinite" : undefined,
          }}
        >
          {hoodie && (
            <span
              aria-hidden="true"
              className="absolute inset-x-0 bottom-0"
              style={{ height: "45%", background: `linear-gradient(to top, rgba(${hoodie.color}, 0.55), transparent)` }}
            />
          )}
          {perfil?.avatar_tipo === "subido" ? (
            <img src={resolveMediaUrl(perfil.avatar_valor)} alt="Tu avatar" className="relative w-full h-full object-cover" />
          ) : (
            <span className="relative" style={{ fontSize: dimension * 0.5, lineHeight: 1 }}>{preset?.emoji ?? "🥷"}</span>
          )}

          {accesorio && IconoAccesorio && (
            <span
              title={accesorio.nombre}
              className="absolute bottom-0 right-0 flex items-center justify-center chamfer-sm"
              style={{
                width: grande ? 28 : 12,
                height: grande ? 28 : 12,
                backgroundColor: "var(--canvas-raised)",
                border: `1px solid rgb(${accesorio.color})`,
              }}
            >
              <IconoAccesorio width={grande ? 16 : 7} height={grande ? 16 : 7} style={{ color: `rgb(${accesorio.color})` }} />
            </span>
          )}
        </div>
      </div>

        {grande &&
          RANURAS.map(({ tipo, pos }, i) => (
            <Ranura key={tipo} tipo={tipo} pieza={porTipo(tipo)} pos={pos} indice={i} mostrarVacia={ranurasVacias} />
          ))}
      </div>

      {grande && tituloNombre && (
        <motion.span
          key={tituloNombre}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-[10px] uppercase tracking-widest mt-1"
          style={{ color: "var(--signal-amber)", fontFamily: "var(--font-mono)" }}
        >
          {tituloNombre}
        </motion.span>
      )}

      {grande && insignias.length > 0 && (
        <div className="flex gap-1 flex-wrap justify-center" style={{ maxWidth: 150 }}>
          {insignias.map((item) => (
            <span key={item.id} title={item.nombre} className="chamfer-sm w-3 h-3" style={{ backgroundColor: `rgb(${item.color})` }} />
          ))}
        </div>
      )}
    </div>
  )
}

function Ranura({
  tipo,
  pieza,
  pos,
  indice,
  mostrarVacia,
}: {
  tipo: TipoCosmetico
  pieza: CosmeticoPerfilItem | undefined
  pos: CSSProperties
  indice: number
  mostrarVacia: boolean
}) {
  const Icono = ICONO_COSMETICO[tipo]
  return (
    <AnimatePresence>
      {pieza ? (
        <motion.span
          key={pieza.id}
          title={pieza.nombre}
          className="absolute"
          style={pos}
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.5 }}
          transition={{ duration: 0.3, ease: [0.19, 1, 0.22, 1] }}
        >
          <span
            className="flotar chamfer-sm flex items-center justify-center"
            style={{
              width: 28,
              height: 28,
              backgroundColor: "var(--canvas-raised)",
              border: `1px solid rgb(${pieza.color})`,
              boxShadow: `0 0 10px rgba(${pieza.color}, 0.35)`,
              animationDelay: `${indice * 0.45}s`,
            }}
          >
            <Icono width={16} height={16} style={{ color: `rgb(${pieza.color})` }} />
          </span>
        </motion.span>
      ) : mostrarVacia ? (
        <span
          key="vacia"
          title={`${TIPO_LABEL[tipo]}: sin equipar`}
          className="absolute chamfer-sm flex items-center justify-center"
          style={{ ...pos, width: 28, height: 28, border: "1px dashed var(--border-strong)", backgroundColor: "var(--canvas)" }}
        >
          <Icono width={14} height={14} style={{ color: "var(--text-dim)" }} />
        </span>
      ) : null}
    </AnimatePresence>
  )
}
