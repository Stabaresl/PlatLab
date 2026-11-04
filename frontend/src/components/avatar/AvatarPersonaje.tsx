import { useId } from "react"
import { PALETA, rasgosDe, type Rasgos } from "../../lib/avatarRasgos"
import type { TipoCosmetico } from "../../pages/api"

/** Lo mínimo de una pieza para dibujarla puesta. */
export interface PiezaPuesta {
  tipo: TipoCosmetico
  color: string // triplete "r,g,b" como lo manda el catálogo
  nombre: string
}

const rgb = (c: string, a = 1) => (a === 1 ? `rgb(${c})` : `rgba(${c}, ${a})`)
const sombra = (c: string) => `color-mix(in srgb, rgb(${c}) 62%, black)`

/**
 * Personaje ilustrado (SVG) con el equipo puesto: cada tipo de cosmético se
 * dibuja en su lugar del cuerpo —gorra en la cabeza, gafas en la cara, guantes
 * en las manos, mochila a la espalda—, no como una ficha al lado.
 *
 * `vista="cabeza"` recorta solo la cabeza (barra de navegación, selector).
 * Con foto subida, la foto ocupa la cara y el equipo se dibuja encima.
 * Decorativo para lectores de pantalla salvo por el `titulo`.
 */
export default function AvatarPersonaje({
  preset,
  foto,
  piezas,
  ancho = 132,
  vista = "completo",
  animado = true,
  titulo,
}: {
  preset: string | null
  foto?: string | null
  piezas: PiezaPuesta[]
  ancho?: number
  vista?: "completo" | "cabeza"
  animado?: boolean
  titulo?: string
}) {
  const id = useId().replace(/:/g, "")
  const r = rasgosDe(preset)
  const de = (tipo: TipoCosmetico) => piezas.find((p) => p.tipo === tipo)
  const hoodie = de("hoodie")
  const gafas = de("gafas")
  const mascara = de("mascara")
  const aura = de("aura")
  const mochila = de("mochila")
  const guantes = de("guantes")
  const zapatos = de("zapatos")
  const gorra = de("gorra")
  const audifonos = de("audifonos")
  const marco = de("marco")
  const insignias = piezas.filter((p) => p.tipo === "insignia").slice(0, 3)

  const cabeza = vista === "cabeza"
  const viewBox = cabeza ? "24 6 72 72" : "0 0 120 160"
  const alto = cabeza ? ancho : Math.round((ancho * 160) / 120)
  const fantasma = r.cabeza === "fantasma"
  const ropa = hoodie ? rgb(hoodie.color) : PALETA.ropaBase
  const ropaSombra = hoodie ? sombra(hoodie.color) : PALETA.ropaSombra
  const piel = r.piel

  return (
    <svg
      width={ancho}
      height={alto}
      viewBox={viewBox}
      role={titulo ? "img" : undefined}
      aria-label={titulo}
      aria-hidden={titulo ? undefined : true}
      className={animado ? "avatar-vivo" : undefined}
      style={{ overflow: cabeza ? "hidden" : "visible", display: "block" }}
    >
      <defs>
        <radialGradient id={`aura-${id}`}>
          <stop offset="0%" stopColor={aura ? rgb(aura.color, 0.55) : "transparent"} />
          <stop offset="70%" stopColor={aura ? rgb(aura.color, 0.12) : "transparent"} />
          <stop offset="100%" stopColor="transparent" />
        </radialGradient>
        <clipPath id={`cara-${id}`}>
          <circle cx="60" cy="46" r="22" />
        </clipPath>
      </defs>

      {/* 1. Aura */}
      {aura && !cabeza && (
        <g>
          <circle cx="60" cy="82" r="62" fill={`url(#aura-${id})`} />
          <circle className="avatar-aura-anillo" cx="60" cy="82" r="56" fill="none" stroke={rgb(aura.color, 0.55)} strokeWidth="1.2" strokeDasharray="3 7" />
        </g>
      )}

      <g className="avatar-cuerpo">
        {/* 2. Mochila (espalda) */}
        {mochila && !cabeza && (
          <g>
            <rect x="29" y="73" width="62" height="42" rx="9" fill={sombra(mochila.color)} />
            <rect x="52" y="66" width="16" height="8" rx="3" fill="none" stroke={sombra(mochila.color)} strokeWidth="3" />
          </g>
        )}

        {/* 3. Capucha detrás de la cabeza */}
        {hoodie && <ellipse cx="60" cy="54" rx="30" ry="27" fill={sombra(hoodie.color)} />}

        {/* 4. Cabello largo (detrás) */}
        {r.peinado === "largo" && !foto && (
          <path d="M36 46 Q34 20 60 20 Q86 20 84 46 L86 76 Q74 72 72 62 L48 62 Q46 72 34 76 Z" fill={r.cabello} />
        )}

        {/* El fantasma es una sábana: cabeza y cuerpo en una sola pieza, en las dos vistas. */}
        {fantasma && !foto && (
          <path
            d="M36 50 Q36 22 60 22 Q84 22 84 50 L86 138 Q80 132 74 138 Q68 132 60 138 Q52 132 46 138 Q40 132 34 138 Z"
            fill={PALETA.fantasma}
          />
        )}

        {!cabeza && (
          <>
            {/* 5. Piernas y zapatos */}
            {!fantasma && (
              <>
                <rect x="42" y="114" width="15" height="30" rx="4" fill={PALETA.pantalon} />
                <rect x="63" y="114" width="15" height="30" rx="4" fill={PALETA.pantalon} />
              </>
            )}
            <Zapato x={37} color={zapatos?.color} />
            <Zapato x={61} color={zapatos?.color} />

            {/* 6. Torso, brazos y manos */}
            {(!fantasma || hoodie) && (
              <>
                <rect x="23" y="76" width="13" height="36" rx="6.5" fill={ropaSombra} transform="rotate(8 29 76)" />
                <rect x="84" y="76" width="13" height="36" rx="6.5" fill={ropaSombra} transform="rotate(-8 91 76)" />
                <path d="M34 82 Q34 72 45 72 L75 72 Q86 72 86 82 L84 118 L36 118 Z" fill={ropa} />
              </>
            )}
            {!hoodie && !fantasma && (
              <>
                <path d="M50 72 L60 82 L70 72" fill="none" stroke={rgb(r.acento)} strokeWidth="2.4" strokeLinejoin="round" />
                <line x1="60" y1="82" x2="60" y2="116" stroke={rgb(r.acento, 0.55)} strokeWidth="1.4" />
              </>
            )}
            <Mano cx={25} color={guantes?.color} piel={fantasma ? PALETA.fantasma : piel} />
            <Mano cx={95} color={guantes?.color} piel={fantasma ? PALETA.fantasma : piel} />

            {/* 7. Tirantes de la mochila */}
            {mochila && (
              <>
                <rect x="43" y="72" width="6" height="34" rx="2" fill={rgb(mochila.color)} />
                <rect x="71" y="72" width="6" height="34" rx="2" fill={rgb(mochila.color)} />
              </>
            )}

            {/* 8. Detalles del hoodie */}
            {hoodie && (
              <>
                <line x1="55" y1="74" x2="54" y2="92" stroke={sombra(hoodie.color)} strokeWidth="1.6" strokeLinecap="round" />
                <line x1="65" y1="74" x2="66" y2="92" stroke={sombra(hoodie.color)} strokeWidth="1.6" strokeLinecap="round" />
                <rect x="46" y="100" width="28" height="12" rx="4" fill={sombra(hoodie.color)} />
              </>
            )}

            {/* 9. Insignias en el pecho */}
            {insignias.map((p, i) => (
              <path
                key={i}
                transform={`translate(${72 - i * 9} 84) scale(0.32)`}
                d="M12 2l9 4v6c0 6-4 10-9 12-5-2-9-6-9-12V6l9-4z"
                fill={rgb(p.color)}
                stroke={sombra(p.color)}
                strokeWidth="2"
              />
            ))}

            {/* Cuello */}
            {!fantasma && <rect x="54" y="64" width="12" height="10" rx="3" fill={piel} />}
          </>
        )}

        {/* 10. Cabeza */}
        <Cabeza r={r} foto={foto} idClip={`cara-${id}`} sinSombrero={!!gorra} conHoodie={!!hoodie} />

        {/* 11. Máscara */}
        {mascara && (
          <g>
            <path d="M40 40 Q40 28 60 28 Q80 28 80 40 Q80 62 60 68 Q40 62 40 40 Z" fill={rgb(mascara.color)} stroke={sombra(mascara.color)} strokeWidth="1.2" />
            <path d="M46 44 Q51 40 56 44 Q51 47 46 44 Z M64 44 Q69 40 74 44 Q69 47 64 44 Z" fill={PALETA.ojos} />
            <path d="M50 56 Q55 52 60 55 Q65 52 70 56 Q65 55 60 58 Q55 55 50 56 Z" fill={sombra(mascara.color)} />
          </g>
        )}

        {/* 12. Gafas */}
        {gafas && (
          <g>
            <rect x="43" y="41" width="14" height="10" rx="3.5" fill={rgb(gafas.color, 0.35)} stroke={rgb(gafas.color)} strokeWidth="1.8" />
            <rect x="63" y="41" width="14" height="10" rx="3.5" fill={rgb(gafas.color, 0.35)} stroke={rgb(gafas.color)} strokeWidth="1.8" />
            <line x1="57" y1="45" x2="63" y2="45" stroke={rgb(gafas.color)} strokeWidth="1.8" />
            <line x1="45" y1="43.5" x2="49" y2="43.5" stroke="white" strokeOpacity="0.7" strokeWidth="1" />
          </g>
        )}

        {/* Casco de astronauta */}
        {r.casco && (
          <g>
            <circle cx="60" cy="46" r="29" fill={PALETA.vidrio} fillOpacity="0.08" stroke={PALETA.vidrio} strokeOpacity="0.85" strokeWidth="2.6" />
            <path d="M42 34 Q48 24 58 22" fill="none" stroke="white" strokeOpacity="0.6" strokeWidth="2" strokeLinecap="round" />
          </g>
        )}

        {/* 13. Audífonos */}
        {audifonos && (
          <g>
            <path d="M34 48 Q33 15 60 15 Q87 15 86 48" fill="none" stroke={sombra(audifonos.color)} strokeWidth="4" strokeLinecap="round" />
            <rect x="29" y="40" width="9" height="16" rx="3.5" fill={rgb(audifonos.color)} />
            <rect x="82" y="40" width="9" height="16" rx="3.5" fill={rgb(audifonos.color)} />
          </g>
        )}

        {/* 14. Gorra */}
        {gorra && (
          <g>
            <path d="M37 38 Q37 16 60 16 Q83 16 83 38 Z" fill={rgb(gorra.color)} />
            <ellipse cx="62" cy="38" rx="28" ry="4.5" fill={sombra(gorra.color)} />
            <circle cx="60" cy="17" r="2.2" fill={sombra(gorra.color)} />
          </g>
        )}
      </g>

      {/* 15. Marco */}
      {marco && (
        <path
          d={cabeza ? "M32 8 H94 V70 L88 76 H26 V14 Z" : "M12 2 H118 V148 L108 158 H2 V12 Z"}
          fill="none"
          stroke={rgb(marco.color)}
          strokeWidth={cabeza ? 2 : 2.5}
        />
      )}
    </svg>
  )
}

function Zapato({ x, color }: { x: number; color?: string }) {
  return (
    <g>
      <path d={`M${x} 146 Q${x} 140 ${x + 8} 140 L${x + 16} 140 Q${x + 22} 141 ${x + 22} 147 L${x + 22} 149 L${x} 149 Z`} fill={color ? rgb(color) : PALETA.zapatoBase} />
      <rect x={x} y={148} width={22} height={2.6} rx="1.2" fill={color ? PALETA.suela : PALETA.ropaSombra} />
    </g>
  )
}

function Mano({ cx, color, piel }: { cx: number; color?: string; piel: string }) {
  return color ? (
    <g>
      <rect x={cx - 6.5} y={106} width={13} height={5} rx="2" fill={sombra(color)} />
      <circle cx={cx} cy={115} r={6.5} fill={rgb(color)} />
    </g>
  ) : (
    <circle cx={cx} cy={114} r={5.8} fill={piel} />
  )
}

function Cabeza({
  r,
  foto,
  idClip,
  sinSombrero,
  conHoodie,
}: {
  r: Rasgos
  foto?: string | null
  idClip: string
  sinSombrero: boolean
  conHoodie: boolean
}) {
  if (foto) {
    return (
      <g>
        <circle cx="60" cy="46" r="23" fill={PALETA.ropaSombra} />
        <image href={foto} x="38" y="24" width="44" height="44" preserveAspectRatio="xMidYMid slice" clipPath={`url(#${idClip})`} />
        <circle cx="60" cy="46" r="22" fill="none" stroke="white" strokeOpacity="0.25" />
      </g>
    )
  }

  if (r.cabeza === "robot") {
    return (
      <g>
        <line x1="60" y1="26" x2="60" y2="15" stroke={PALETA.metalSombra} strokeWidth="2" />
        <circle cx="60" cy="14" r="3.2" fill={rgb(r.acento)} />
        <rect x="37" y="26" width="46" height="40" rx="9" fill={PALETA.metal} stroke={PALETA.metalSombra} strokeWidth="1.5" />
        <rect x="42" y="34" width="36" height="16" rx="5" fill={PALETA.tela} />
        <g className="avatar-ojos">
          <rect x="46" y="39" width="10" height="6" rx="2" fill="rgb(56,214,245)" />
          <rect x="64" y="39" width="10" height="6" rx="2" fill="rgb(56,214,245)" />
        </g>
        <path d="M50 57 H70 M50 60 H70" stroke={PALETA.metalSombra} strokeWidth="1.5" />
      </g>
    )
  }

  if (r.cabeza === "alien") {
    return (
      <g>
        <path d="M46 26 L40 12 M74 26 L80 12" stroke={r.piel} strokeWidth="2.4" strokeLinecap="round" />
        <circle cx="40" cy="11" r="3" fill={r.piel} />
        <circle cx="80" cy="11" r="3" fill={r.piel} />
        <ellipse cx="60" cy="46" rx="23" ry="24" fill={r.piel} />
        <g className="avatar-ojos">
          <ellipse cx="51" cy="46" rx="6" ry="8" fill={PALETA.ojos} />
          <ellipse cx="69" cy="46" rx="6" ry="8" fill={PALETA.ojos} />
        </g>
        <circle cx="53" cy="43" r="1.8" fill="white" />
        <circle cx="71" cy="43" r="1.8" fill="white" />
        <path d="M55 60 Q60 63 65 60" fill="none" stroke={PALETA.ojos} strokeWidth="1.6" strokeLinecap="round" />
      </g>
    )
  }

  if (r.cabeza === "fantasma") {
    return (
      <g>
        <g className="avatar-ojos">
          <ellipse cx="51" cy="46" rx="4.5" ry="6.5" fill={PALETA.ojos} />
          <ellipse cx="69" cy="46" rx="4.5" ry="6.5" fill={PALETA.ojos} />
        </g>
        <ellipse cx="60" cy="59" rx="3.5" ry="4" fill={PALETA.ojos} />
      </g>
    )
  }

  const ninja = r.peinado === "ninja"
  return (
    <g>
      {!conHoodie && (
        <>
          <circle cx="38" cy="48" r="4.2" fill={ninja ? PALETA.tela : r.piel} />
          <circle cx="82" cy="48" r="4.2" fill={ninja ? PALETA.tela : r.piel} />
        </>
      )}
      <circle cx="60" cy="46" r="22" fill={ninja ? PALETA.tela : r.piel} />
      {ninja && (
        <>
          <rect x="40" y="39" width="40" height="13" rx="6.5" fill={r.piel} />
          <path d="M80 38 L94 33 L91 41 Z M80 42 L93 46 L88 50 Z" fill={PALETA.tela} />
        </>
      )}
      <g className="avatar-ojos">
        <circle cx="51" cy="46" r="2.6" fill={PALETA.ojos} />
        <circle cx="69" cy="46" r="2.6" fill={PALETA.ojos} />
      </g>
      {!ninja && <path d="M54 56 Q60 60.5 66 56" fill="none" stroke={PALETA.ojos} strokeOpacity="0.75" strokeWidth="1.6" strokeLinecap="round" />}
      {(r.peinado === "corto" || r.peinado === "sombrero") && (
        <path d="M38 44 Q37 22 60 22 Q83 22 82 44 Q78 31 60 31 Q42 31 38 44 Z" fill={r.cabello} />
      )}
      {r.peinado === "largo" && <path d="M38 42 Q40 23 60 23 Q80 23 82 42 Q70 30 58 36 Q48 31 38 42 Z" fill={r.cabello} />}
      {r.peinado === "sombrero" && !sinSombrero && (
        <g>
          <ellipse cx="60" cy="30" rx="31" ry="5" fill={PALETA.sombrero} />
          <path d="M44 30 Q44 12 60 12 Q76 12 76 30 Z" fill={PALETA.sombrero} />
          <rect x="44" y="24" width="32" height="4" fill={rgb(r.acento, 0.8)} />
        </g>
      )}
    </g>
  )
}
