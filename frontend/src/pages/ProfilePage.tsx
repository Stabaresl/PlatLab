import { useEffect, useMemo, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { useGamificationStore } from "../store/gamificationStore"
import Navbar from "../components/Navbar"
import Footer from "../components/Footer"
import HeroBackground from "../components/HeroBackground"
import TerminalHeader from "../components/TerminalHeader"
import SectionHeading from "../components/SectionHeading"
import ProgressRing from "../components/ProgressRing"
import AvatarBadge from "../components/AvatarBadge"
import AvatarPicker from "../components/AvatarPicker"
import Revelar from "../components/movimiento/Revelar"
import BarraLlenado from "../components/movimiento/BarraLlenado"
import NumeroAnimado from "../components/movimiento/NumeroAnimado"
import { EASE_TACTICO } from "../components/movimiento/curvas"
import { IconTrophy, IconLock, IconGlasses, IconBackpack } from "../components/icons"
import { Skeleton } from "../components/ui/skeleton"
import { ICONO_COSMETICO, ORDEN_RAREZA, RAREZA_COLOR, RAREZA_LABEL, TIPO_LABEL } from "../lib/cosmeticos"
import {
  getCatalogoGamificacion,
  type CatalogoGamificacion,
  type CosmeticoPerfilItem,
  type LogroPerfilItem,
  type PerfilJugador,
  type RarezaCosmetico,
  type TipoCosmetico,
} from "./api"

// Misma tabla de umbrales que `modules/gamification/domain/entities.py::NIVEL_UMBRALES`
// — duplicada acá solo para calcular el % de avance dentro del nivel actual
// (dato de balance del juego, no sensible).
const NIVEL_UMBRALES = [0, 100, 250, 450, 700, 1000, 1400, 1900, 2500, 3200, 4000]

function porcentajeDeNivel(xp: number, xpSiguiente: number | null): number {
  if (xpSiguiente === null) return 100
  const anterior = [...NIVEL_UMBRALES].reverse().find((u) => u <= xp) ?? 0
  const rango = xpSiguiente - anterior
  if (rango <= 0) return 100
  return ((xp - anterior) / rango) * 100
}

/** "7/10" → { actual: 7, meta: 10 }; null si el backend no manda progreso numérico. */
function leerProgreso(texto: string | null): { actual: number; meta: number } | null {
  const m = texto?.match(/(\d+)\s*\/\s*(\d+)/)
  return m ? { actual: Number(m[1]), meta: Number(m[2]) } : null
}

type FiltroLogros = "todos" | "desbloqueados" | "pendientes"
type FiltroInventario = "todo" | "tuyos" | "bloqueados"

interface PiezaColeccion {
  cosmeticoId: string
  nombre: string
  tipo: TipoCosmetico
  rareza: RarezaCosmetico
  color: string
  propia: CosmeticoPerfilItem | null
  logroRequerido: string | null
}

export default function ProfilePage() {
  const { perfil, loading, error, load, equip, unequip, equipTitle, unequipTitle } = useGamificationStore()
  const role = localStorage.getItem("role")
  const tituloEquipado = perfil?.titulos.find((t) => t.equipado)
  const [catalogo, setCatalogo] = useState<CatalogoGamificacion | null>(null)

  useEffect(() => { load() }, [load])
  useEffect(() => {
    if (role !== "estudiante") return
    // Sin catálogo igual se muestra lo propio; solo se pierden las piezas por desbloquear.
    getCatalogoGamificacion().then(setCatalogo).catch(() => setCatalogo(null))
  }, [role])

  return (
    <div className="relative min-h-screen overflow-hidden" style={{ backgroundColor: "var(--canvas)", color: "var(--text-base)" }}>
      <HeroBackground image="grim" imageOpacity={0.06} overlayOpacity={0.9} texture="matrix" textureOpacity={0.03} />
      <div className="relative z-10 flex flex-col min-h-screen">
        <Navbar />
        <main className="flex-1">
          <div className="mx-auto px-4 sm:px-6 md:px-8 py-8 sm:py-10 md:py-12" style={{ maxWidth: "1040px" }}>
            <TerminalHeader title="Mi Perfil" subtitle="Tu progresión en PlatLAB" prompt="whoami --progresion" />

            <AnimatePresence>
              {error && (
                <motion.p initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="text-sm mb-6 px-3 py-2 chamfer-sm" style={{ color: "var(--signal-red)", backgroundColor: "color-mix(in srgb, var(--signal-red) 8%, transparent)", border: "1px solid var(--signal-red-dim)" }} role="alert">
                  ▲ {error}
                </motion.p>
              )}
            </AnimatePresence>

            {role !== "estudiante" ? (
              <div className="chamfer p-8 text-center" style={{ border: "1px dashed var(--border-strong)" }}>
                <p className="text-sm m-0" style={{ color: "var(--text-muted)" }}>
                  La progresión (XP, logros, cosméticos) se gana completando laboratorios como estudiante.
                </p>
              </div>
            ) : loading && !perfil ? (
              <div className="flex flex-col gap-4">
                {Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="chamfer h-24" style={{ backgroundColor: "var(--surface)" }} />
                ))}
              </div>
            ) : !perfil ? null : (
              <>
                <Cabecera perfil={perfil} tituloNombre={tituloEquipado?.nombre} />

                {/* ═══ PERSONALIZAR AVATAR ═══ */}
                <Revelar como="section" className="mb-8 sm:mb-10">
                  <SectionHeading icon={<IconGlasses />} title="Personalizar Avatar" subtitle="Elige uno predeterminado o sube tu propia foto" />
                  <div className="chamfer p-4 sm:p-5" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
                    <AvatarPicker perfil={perfil} />
                  </div>
                </Revelar>

                <Logros perfil={perfil} catalogo={catalogo} />

                {/* ═══ TÍTULOS ═══ */}
                <Revelar como="section" className="mb-8 sm:mb-10">
                  <SectionHeading icon={<IconTrophy />} title="Títulos" subtitle="Un solo título equipado a la vez: haz clic para equipar o quitar" />
                  {perfil.titulos.length === 0 ? (
                    <Vacio texto="Todavía no desbloqueas títulos: salen de los logros" />
                  ) : (
                    <div className="grid gap-3 sm:gap-4" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(min(200px, 100%), 1fr))" }}>
                      {perfil.titulos.map((titulo, i) => {
                        const color = RAREZA_COLOR[titulo.rareza]
                        return (
                          <Revelar key={titulo.id} desde="escala" retraso={Math.min(i * 0.05, 0.4)}>
                            <motion.button
                              type="button"
                              whileHover={{ y: -3 }}
                              whileTap={{ scale: 0.98 }}
                              onClick={() => (titulo.equipado ? unequipTitle(titulo.id) : equipTitle(titulo.id))}
                              className="chamfer w-full h-full flex flex-col items-start p-3 text-left cursor-pointer transition-colors"
                              style={{
                                backgroundColor: titulo.equipado ? "var(--surface-hover)" : "var(--surface)",
                                border: `1px solid ${titulo.equipado ? color : "var(--border-default)"}`,
                              }}
                            >
                              <span className="text-[9px] font-bold uppercase tracking-wide mb-1" style={{ color, fontFamily: "var(--font-mono)" }}>
                                {RAREZA_LABEL[titulo.rareza]}
                              </span>
                              <span className="text-sm font-bold mb-1" style={{ color: "var(--text-heading)" }}>{titulo.nombre}</span>
                              <span className="text-xs leading-relaxed mb-2" style={{ color: "var(--text-muted)" }}>{titulo.descripcion}</span>
                              <EstadoEquipo equipado={titulo.equipado} />
                            </motion.button>
                          </Revelar>
                        )
                      })}
                    </div>
                  )}
                </Revelar>

                <Inventario perfil={perfil} catalogo={catalogo} onEquipar={equip} onQuitar={unequip} />
              </>
            )}
          </div>
        </main>
        <Footer />
      </div>
    </div>
  )
}

/* ───────── Cabecera: avatar con su equipo + nivel ───────── */
function Cabecera({ perfil, tituloNombre }: { perfil: PerfilJugador; tituloNombre?: string }) {
  const avance = porcentajeDeNivel(perfil.xp, perfil.xp_para_siguiente_nivel)
  const equipadas = perfil.cosmeticos.filter((c) => c.equipado).length
  return (
    <Revelar
      como="section"
      className="chamfer grid gap-6 sm:grid-cols-[auto_minmax(0,1fr)_auto] items-center p-5 sm:p-7 mb-8 sm:mb-10"
      style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}
    >
      <div className="flex justify-center">
        <AvatarBadge perfil={perfil} size="lg" tituloNombre={tituloNombre} ranurasVacias />
      </div>
      <div className="flex flex-col items-center sm:items-start gap-3 min-w-0">
        <div className="flex items-baseline gap-3">
          <span className="text-[11px] uppercase tracking-widest" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>Nivel</span>
          <NumeroAnimado valor={perfil.nivel} className="text-4xl font-bold text-display leading-none" style={{ color: "var(--text-heading)" }} />
        </div>
        <div className="w-full flex flex-col gap-1.5" style={{ maxWidth: 360 }}>
          <BarraLlenado valor={avance} color="var(--signal-amber)" alto={6} etiqueta={`${Math.round(avance)} % del nivel ${perfil.nivel}`} />
          <span className="text-xs font-mono text-center sm:text-left" style={{ color: "var(--text-muted)" }}>
            <NumeroAnimado valor={perfil.xp} /> XP
            {perfil.xp_para_siguiente_nivel !== null ? ` · faltan ${perfil.xp_para_siguiente_nivel - perfil.xp} para el siguiente nivel` : " · nivel máximo"}
          </span>
        </div>
        <span className="text-[11px] uppercase tracking-widest text-center sm:text-left" style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
          {equipadas} pieza{equipadas === 1 ? "" : "s"} equipada{equipadas === 1 ? "" : "s"} · {perfil.cosmeticos.length} en tu inventario
        </span>
      </div>
      <div className="hidden sm:flex justify-center">
        <ProgressRing percent={avance} size={84} color="var(--signal-amber)" label="nivel" />
      </div>
    </Revelar>
  )
}

/* ───────── Logros ───────── */
function Logros({ perfil, catalogo }: { perfil: PerfilJugador; catalogo: CatalogoGamificacion | null }) {
  const [filtro, setFiltro] = useState<FiltroLogros>("todos")
  const desbloqueados = perfil.logros.filter((l) => l.desbloqueado).length

  // Recompensas por logro: las piezas y títulos que apuntan a él en el catálogo.
  const recompensas = useMemo(() => {
    const mapa = new Map<string, { piezas: CatalogoGamificacion["cosmeticos"]; titulos: CatalogoGamificacion["titulos"] }>()
    if (!catalogo) return mapa
    for (const logro of catalogo.logros) {
      mapa.set(logro.clave, {
        piezas: catalogo.cosmeticos.filter((c) => c.logro_requerido_id === logro.id),
        titulos: catalogo.titulos.filter((t) => t.logro_requerido_id === logro.id),
      })
    }
    return mapa
  }, [catalogo])

  const visibles = perfil.logros
    .filter((l) => (filtro === "todos" ? true : filtro === "desbloqueados" ? l.desbloqueado : !l.desbloqueado))
    .sort((a, b) => Number(b.desbloqueado) - Number(a.desbloqueado))

  return (
    <Revelar como="section" className="mb-8 sm:mb-10">
      <SectionHeading icon={<IconTrophy />} title="Logros" subtitle={`${desbloqueados} de ${perfil.logros.length} desbloqueados`} />
      <div className="flex flex-col sm:flex-row sm:items-center gap-3 mb-4">
        <div className="flex-1">
          <BarraLlenado valor={desbloqueados} max={perfil.logros.length} segmentos color="var(--signal-amber)" alto={5} etiqueta={`${desbloqueados} de ${perfil.logros.length} logros`} />
        </div>
        <Segmento
          grupo="logros"
          valor={filtro}
          onCambio={setFiltro}
          opciones={[
            { valor: "todos", etiqueta: "Todos" },
            { valor: "desbloqueados", etiqueta: "Ganados" },
            { valor: "pendientes", etiqueta: "Por ganar" },
          ]}
        />
      </div>

      {visibles.length === 0 ? (
        <Vacio texto={filtro === "desbloqueados" ? "Todavía no ganas logros: termina tu primer laboratorio" : "Ya los ganaste todos"} />
      ) : (
        <motion.div layout className="grid gap-3 sm:gap-4" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(min(240px, 100%), 1fr))" }}>
          <AnimatePresence>
            {visibles.map((logro, i) => (
              <TarjetaLogro key={logro.id} logro={logro} indice={i} recompensa={recompensas.get(logro.clave)} />
            ))}
          </AnimatePresence>
        </motion.div>
      )}
    </Revelar>
  )
}

function TarjetaLogro({
  logro,
  indice,
  recompensa,
}: {
  logro: LogroPerfilItem
  indice: number
  recompensa?: { piezas: CatalogoGamificacion["cosmeticos"]; titulos: CatalogoGamificacion["titulos"] }
}) {
  const color = RAREZA_COLOR[logro.rareza]
  const progreso = leerProgreso(logro.progreso)
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 14 }}
      whileInView={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.96 }}
      viewport={{ once: true }}
      transition={{ duration: 0.45, delay: Math.min(indice * 0.05, 0.4), ease: EASE_TACTICO }}
      whileHover={{ y: -3 }}
      className="relative chamfer flex flex-col p-4 overflow-hidden"
      style={{
        backgroundColor: logro.desbloqueado ? `color-mix(in srgb, ${color} 6%, var(--surface))` : "var(--surface)",
        border: `1px solid ${logro.desbloqueado ? color : "var(--border-default)"}`,
      }}
    >
      {logro.desbloqueado && (
        <motion.span
          aria-hidden="true"
          className="brillo"
          style={{ ["--brillo" as string]: color, skewX: -18 }}
          initial={{ x: "-120%", opacity: 0 }}
          whileInView={{ x: "320%", opacity: [0, 1, 0] }}
          viewport={{ once: true }}
          transition={{ duration: 1.5, delay: 0.3 + Math.min(indice * 0.05, 0.4), ease: EASE_TACTICO }}
        />
      )}
      <div className="flex items-start gap-3 mb-2">
        <span
          className="chamfer-sm flex items-center justify-center shrink-0"
          style={{
            width: 38,
            height: 38,
            backgroundColor: logro.desbloqueado ? `color-mix(in srgb, ${color} 16%, transparent)` : "var(--surface-hover)",
            color: logro.desbloqueado ? color : "var(--text-dim)",
          }}
        >
          {logro.desbloqueado ? <IconTrophy width={20} height={20} /> : <IconLock width={18} height={18} />}
        </span>
        <div className="flex flex-col min-w-0">
          <span className="text-[10px] font-bold uppercase tracking-wide" style={{ color: logro.desbloqueado ? color : "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
            {RAREZA_LABEL[logro.rareza]}
          </span>
          <span className="text-sm font-bold" style={{ color: logro.desbloqueado ? "var(--text-heading)" : "var(--text-base)" }}>{logro.nombre}</span>
        </div>
      </div>
      <span className="text-xs leading-relaxed" style={{ color: "var(--text-muted)" }}>{logro.descripcion}</span>

      {!logro.desbloqueado && progreso && (
        <div className="flex items-center gap-2 mt-3">
          <BarraLlenado valor={progreso.actual} max={progreso.meta} color={color} alto={4} etiqueta={`Progreso ${progreso.actual} de ${progreso.meta}`} />
          <span className="text-[10px] font-mono shrink-0" style={{ color: "var(--text-muted)" }}>{progreso.actual}/{progreso.meta}</span>
        </div>
      )}

      {recompensa && (recompensa.piezas.length > 0 || recompensa.titulos.length > 0) && (
        <div className="flex flex-wrap items-center gap-1.5 mt-3 pt-3" style={{ borderTop: "1px solid var(--border-hairline)" }}>
          <span className="text-[9px] uppercase tracking-widest mr-1" style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)" }}>Recompensa</span>
          {recompensa.piezas.map((p) => {
            const Icono = ICONO_COSMETICO[p.tipo]
            return (
              <span key={p.id} title={p.nombre} className="chamfer-sm flex items-center justify-center" style={{ width: 22, height: 22, border: `1px solid rgb(${p.color})`, opacity: logro.desbloqueado ? 1 : 0.6 }}>
                <Icono width={13} height={13} style={{ color: `rgb(${p.color})` }} />
              </span>
            )
          })}
          {recompensa.titulos.map((t) => (
            <span key={t.id} className="text-[10px] px-1.5 py-0.5 chamfer-sm" style={{ color: "var(--signal-amber)", border: "1px solid var(--border-amber)", fontFamily: "var(--font-mono)" }}>
              «{t.nombre}»
            </span>
          ))}
        </div>
      )}
    </motion.div>
  )
}

/* ───────── Inventario: la colección completa, con lo que falta ───────── */
function Inventario({
  perfil,
  catalogo,
  onEquipar,
  onQuitar,
}: {
  perfil: PerfilJugador
  catalogo: CatalogoGamificacion | null
  onEquipar: (id: string) => Promise<void>
  onQuitar: (id: string) => Promise<void>
}) {
  const [filtro, setFiltro] = useState<FiltroInventario>("todo")
  const [ocupado, setOcupado] = useState<string | null>(null)

  const coleccion = useMemo<PiezaColeccion[]>(() => {
    const propias = new Map(perfil.cosmeticos.map((c) => [c.cosmetico_id, c]))
    if (!catalogo) {
      return perfil.cosmeticos.map((c) => ({
        cosmeticoId: c.cosmetico_id, nombre: c.nombre, tipo: c.tipo, rareza: c.rareza, color: c.color, propia: c, logroRequerido: null,
      }))
    }
    const nombreLogro = new Map(catalogo.logros.map((l) => [l.id, l.nombre]))
    return catalogo.cosmeticos
      .map((c) => ({
        cosmeticoId: c.id,
        nombre: c.nombre,
        tipo: c.tipo,
        rareza: c.rareza,
        color: c.color,
        propia: propias.get(c.id) ?? null,
        logroRequerido: nombreLogro.get(c.logro_requerido_id) ?? null,
      }))
      .sort((a, b) => Number(!!b.propia) - Number(!!a.propia) || ORDEN_RAREZA.indexOf(a.rareza) - ORDEN_RAREZA.indexOf(b.rareza))
  }, [perfil.cosmeticos, catalogo])

  const visibles = coleccion.filter((p) => (filtro === "todo" ? true : filtro === "tuyos" ? !!p.propia : !p.propia))
  const tuyas = coleccion.filter((p) => p.propia).length

  const alternar = async (pieza: CosmeticoPerfilItem) => {
    if (ocupado) return
    setOcupado(pieza.id)
    await (pieza.equipado ? onQuitar(pieza.id) : onEquipar(pieza.id))
    setOcupado(null)
  }

  return (
    <Revelar como="section">
      <SectionHeading
        icon={<IconBackpack />}
        title="Inventario"
        subtitle={catalogo ? `${tuyas} de ${coleccion.length} piezas de la colección: equipa una por tipo y se ve en tu avatar` : "Haz clic en una pieza para equiparla o quitarla"}
      />
      {catalogo && (
        <div className="flex justify-end mb-4">
          <Segmento
            grupo="inventario"
            valor={filtro}
            onCambio={setFiltro}
            opciones={[
              { valor: "todo", etiqueta: "Todo" },
              { valor: "tuyos", etiqueta: "Tuyas" },
              { valor: "bloqueados", etiqueta: "Por desbloquear" },
            ]}
          />
        </div>
      )}

      {visibles.length === 0 ? (
        <Vacio texto={filtro === "bloqueados" ? "Ya tienes toda la colección" : "Todavía no desbloqueas piezas: termina laboratorios para conseguirlas"} />
      ) : (
        <motion.div layout className="grid gap-3 sm:gap-4" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(min(170px, 100%), 1fr))" }}>
          <AnimatePresence>
            {visibles.map((pieza, i) => (
              <TarjetaPieza key={pieza.cosmeticoId} pieza={pieza} indice={i} ocupado={ocupado === pieza.propia?.id} onAlternar={alternar} />
            ))}
          </AnimatePresence>
        </motion.div>
      )}
    </Revelar>
  )
}

function TarjetaPieza({
  pieza,
  indice,
  ocupado,
  onAlternar,
}: {
  pieza: PiezaColeccion
  indice: number
  ocupado: boolean
  onAlternar: (p: CosmeticoPerfilItem) => void
}) {
  const Icono = ICONO_COSMETICO[pieza.tipo]
  const rareza = RAREZA_COLOR[pieza.rareza]
  const propia = pieza.propia
  const equipada = !!propia?.equipado
  const contenido = (
    <>
      <div
        className="relative w-full self-stretch flex items-center justify-center chamfer-sm mb-3 overflow-hidden"
        style={{
          height: 76,
          background: propia
            ? `radial-gradient(circle at 50% 60%, rgba(${pieza.color}, 0.28), transparent 70%), var(--surface-sunken)`
            : "var(--surface-sunken)",
        }}
      >
        <span className="absolute left-2 top-1.5 text-[9px] font-bold uppercase tracking-wide" style={{ color: propia ? rareza : "var(--text-dim)", fontFamily: "var(--font-mono)" }}>
          {RAREZA_LABEL[pieza.rareza]}
        </span>
        <span className={propia ? "flotar" : undefined} style={{ animationDelay: `${(indice % 5) * 0.35}s` }}>
          <Icono width={34} height={34} style={{ color: propia ? `rgb(${pieza.color})` : "var(--text-dim)", opacity: propia ? 1 : 0.55 }} />
        </span>
        {!propia && (
          <span className="absolute right-2 top-1.5" style={{ color: "var(--text-dim)" }}>
            <IconLock width={13} height={13} />
          </span>
        )}
        <AnimatePresence>
          {equipada && (
            <motion.span
              initial={{ opacity: 0, scale: 0.4 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.4 }}
              className="absolute right-1.5 top-1.5 chamfer-sm flex items-center justify-center"
              style={{ width: 18, height: 18, backgroundColor: "var(--signal-green)" }}
            >
              <svg width="11" height="11" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                <path d="M2.5 7.5 L5.8 10.5 L11.5 3.8" stroke="var(--canvas)" strokeWidth="2.4" strokeLinecap="square" />
              </svg>
            </motion.span>
          )}
        </AnimatePresence>
      </div>
      <span className="text-xs font-bold" style={{ color: propia ? "var(--text-heading)" : "var(--text-muted)" }}>{pieza.nombre}</span>
      <span className="text-[10px] uppercase tracking-wide mt-0.5" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
        {TIPO_LABEL[pieza.tipo]}
      </span>
      {propia ? (
        <span className="mt-2">
          <EstadoEquipo equipado={equipada} ocupado={ocupado} />
        </span>
      ) : (
        <span className="text-[10px] leading-snug mt-2" style={{ color: "var(--text-dim)" }}>
          {pieza.logroRequerido ? `Se gana con el logro «${pieza.logroRequerido}»` : "Por desbloquear"}
        </span>
      )}
    </>
  )

  const animacion = {
    layout: true,
    initial: { opacity: 0, y: 14 },
    whileInView: { opacity: 1, y: 0 },
    exit: { opacity: 0, scale: 0.94 },
    viewport: { once: true },
    transition: { duration: 0.4, delay: Math.min(indice * 0.04, 0.35), ease: EASE_TACTICO },
  } as const

  if (!propia) {
    return (
      <motion.div {...animacion} className="chamfer flex flex-col items-start p-3" style={{ backgroundColor: "var(--surface)", border: "1px dashed var(--border-strong)" }}>
        {contenido}
      </motion.div>
    )
  }
  return (
    <motion.button
      {...animacion}
      type="button"
      whileHover={{ y: -3 }}
      whileTap={{ scale: 0.97 }}
      disabled={ocupado}
      onClick={() => onAlternar(propia)}
      aria-pressed={equipada}
      className="chamfer flex flex-col items-start p-3 text-left cursor-pointer transition-colors disabled:cursor-wait"
      style={{
        backgroundColor: equipada ? `rgba(${pieza.color}, 0.08)` : "var(--surface)",
        border: `1px solid ${equipada ? "var(--signal-green)" : "var(--border-default)"}`,
      }}
    >
      {contenido}
    </motion.button>
  )
}

/* ───────── Piezas pequeñas compartidas ───────── */
function EstadoEquipo({ equipado, ocupado = false }: { equipado: boolean; ocupado?: boolean }) {
  return (
    <span
      className="text-[10px] font-bold uppercase px-1.5 py-0.5"
      style={{
        color: equipado ? "var(--signal-green)" : "var(--text-dim)",
        backgroundColor: equipado ? "color-mix(in srgb, var(--signal-green) 12%, transparent)" : "transparent",
        fontFamily: "var(--font-mono)",
      }}
    >
      {ocupado ? "…" : equipado ? "Equipado" : "Equipar"}
    </span>
  )
}

function Vacio({ texto }: { texto: string }) {
  return (
    <div className="chamfer p-6 text-center" style={{ border: "1px dashed var(--border-strong)" }}>
      <p className="text-xs uppercase tracking-widest m-0" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
        [ {texto} ]
      </p>
    </div>
  )
}

function Segmento<T extends string>({
  grupo,
  valor,
  opciones,
  onCambio,
}: {
  grupo: string
  valor: T
  opciones: { valor: T; etiqueta: string }[]
  onCambio: (v: T) => void
}) {
  return (
    <div role="radiogroup" className="inline-flex chamfer-sm p-0.5 shrink-0" style={{ backgroundColor: "var(--surface-sunken)", border: "1px solid var(--border-default)" }}>
      {opciones.map((o) => {
        const activo = o.valor === valor
        return (
          <button
            key={o.valor}
            type="button"
            role="radio"
            aria-checked={activo}
            onClick={() => onCambio(o.valor)}
            className="relative px-2.5 py-1 text-[10px] uppercase tracking-wide whitespace-nowrap cursor-pointer"
            style={{ color: activo ? "var(--canvas)" : "var(--text-muted)", fontFamily: "var(--font-mono)" }}
          >
            {activo && (
              <motion.span
                layoutId={`segmento-${grupo}`}
                className="absolute inset-0 chamfer-sm"
                style={{ backgroundColor: "var(--signal-amber)" }}
                transition={{ duration: 0.25, ease: EASE_TACTICO }}
              />
            )}
            <span className="relative">{o.etiqueta}</span>
          </button>
        )
      })}
    </div>
  )
}
