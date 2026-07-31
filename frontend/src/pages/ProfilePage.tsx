import { useEffect } from "react"
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
import { IconTrophy, IconLock, IconGlasses } from "../components/icons"
import { Skeleton } from "../components/ui/skeleton"
import type { RarezaCosmetico, TipoCosmetico } from "./api"

// Misma tabla de umbrales que `modules/gamification/domain/entities.py::NIVEL_UMBRALES`
// — duplicada acá solo para calcular el % del anillo de progreso dentro
// del nivel actual (dato de balance del juego, no sensible).
const NIVEL_UMBRALES = [0, 100, 250, 450, 700, 1000, 1400, 1900, 2500, 3200, 4000]

const RAREZA_LABEL: Record<RarezaCosmetico, string> = {
  comun: "Común",
  poco_comun: "Poco común",
  raro: "Raro",
  epico: "Épico",
  legendario: "Legendario",
  mitico: "Mítico",
}

const RAREZA_COLOR: Record<RarezaCosmetico, string> = {
  comun: "var(--text-muted)",
  poco_comun: "var(--signal-cyan)",
  raro: "var(--signal-green)",
  epico: "var(--signal-amber)",
  legendario: "168,85,247",
  mitico: "236,72,153",
}

const TIPO_LABEL: Record<TipoCosmetico, string> = {
  hoodie: "Hoodie", gafas: "Gafas", mascara: "Máscara", aura: "Aura", insignia: "Insignia",
  mochila: "Mochila", guantes: "Guantes", zapatos: "Zapatos", gorra: "Gorra", audifonos: "Audífonos",
  marco: "Marco",
}

function porcentajeDeNivel(xp: number, xpSiguiente: number | null): number {
  if (xpSiguiente === null) return 100
  const anterior = [...NIVEL_UMBRALES].reverse().find((u) => u <= xp) ?? 0
  const rango = xpSiguiente - anterior
  if (rango <= 0) return 100
  return ((xp - anterior) / rango) * 100
}

export default function ProfilePage() {
  const { perfil, loading, error, load, equip, unequip, equipTitle, unequipTitle } = useGamificationStore()
  const role = localStorage.getItem("role")
  const tituloEquipado = perfil?.titulos.find((t) => t.equipado)

  useEffect(() => { load() }, [load])

  return (
    <div className="relative min-h-screen overflow-hidden" style={{ backgroundColor: "var(--canvas)", color: "var(--text-base)" }}>
      <HeroBackground image="grim" imageOpacity={0.06} overlayOpacity={0.9} texture="matrix" textureOpacity={0.03} />
      <div className="relative z-10 flex flex-col min-h-screen">
        <Navbar />
        <main className="flex-1">
          <div className="mx-auto px-4 sm:px-6 md:px-8 py-8 sm:py-10 md:py-12" style={{ maxWidth: "980px" }}>
            <TerminalHeader title="Mi Perfil" subtitle="Tu progresión en PlatLAB" prompt="whoami --progresion" />

            <AnimatePresence>
              {error && (
                <motion.p initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="text-sm mb-6 px-3 py-2 chamfer-sm" style={{ color: "var(--signal-red)", backgroundColor: "rgba(255,71,87,0.08)", border: "1px solid var(--signal-red-dim)" }} role="alert">
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
            ) : loading || !perfil ? (
              <div className="flex flex-col gap-4">
                {Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="chamfer h-24" style={{ backgroundColor: "var(--surface)" }} />
                ))}
              </div>
            ) : (
              <>
                {/* ═══ AVATAR + XP ═══ */}
                <section className="chamfer flex flex-col sm:flex-row items-center gap-6 sm:gap-8 p-5 sm:p-7 mb-8 sm:mb-10" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
                  <AvatarBadge perfil={perfil} size="lg" tituloNombre={tituloEquipado?.nombre} />
                  <div className="flex-1 w-full flex flex-col items-center sm:items-start gap-2">
                    <span className="text-lg font-bold uppercase tracking-wide" style={{ color: "var(--text-heading)" }}>Nivel {perfil.nivel}</span>
                    <span className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>
                      {perfil.xp} XP{perfil.xp_para_siguiente_nivel !== null ? ` · ${perfil.xp_para_siguiente_nivel - perfil.xp} para el siguiente nivel` : " · nivel máximo"}
                    </span>
                  </div>
                  <ProgressRing percent={porcentajeDeNivel(perfil.xp, perfil.xp_para_siguiente_nivel)} size={80} color="var(--signal-amber)" label="nivel" />
                </section>

                {/* ═══ PERSONALIZAR AVATAR ═══ */}
                <section className="mb-8 sm:mb-10">
                  <SectionHeading icon={<IconGlasses />} title="Personalizar Avatar" subtitle="Elegí uno predeterminado o subí tu propia foto" />
                  <div className="chamfer p-4 sm:p-5" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
                    <AvatarPicker perfil={perfil} />
                  </div>
                </section>

                {/* ═══ LOGROS ═══ */}
                <section className="mb-8 sm:mb-10">
                  <SectionHeading icon={<IconTrophy />} title="Logros" subtitle={`${perfil.logros.filter((l) => l.desbloqueado).length}/${perfil.logros.length} desbloqueados`} />
                  <div className="grid gap-3 sm:gap-4" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))" }}>
                    {perfil.logros.map((logro) => (
                      <div
                        key={logro.id}
                        className="chamfer flex flex-col p-4"
                        style={{
                          backgroundColor: "var(--surface)",
                          border: `1px solid ${logro.desbloqueado ? RAREZA_COLOR[logro.rareza].startsWith("var") ? RAREZA_COLOR[logro.rareza] : `rgb(${RAREZA_COLOR[logro.rareza]})` : "var(--border-default)"}`,
                          opacity: logro.desbloqueado ? 1 : 0.55,
                        }}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-[10px] font-bold uppercase tracking-wide" style={{ color: RAREZA_COLOR[logro.rareza].startsWith("var") ? RAREZA_COLOR[logro.rareza] : `rgb(${RAREZA_COLOR[logro.rareza]})`, fontFamily: "var(--font-mono)" }}>
                            {RAREZA_LABEL[logro.rareza]}
                          </span>
                          {!logro.desbloqueado && <IconLock width={14} height={14} style={{ color: "var(--text-dim)" }} />}
                        </div>
                        <span className="text-sm font-bold mb-1" style={{ color: "var(--text-heading)" }}>{logro.nombre}</span>
                        <span className="text-xs leading-relaxed" style={{ color: "var(--text-muted)" }}>{logro.descripcion}</span>
                        {logro.progreso && (
                          <span className="text-[10px] font-mono mt-2" style={{ color: "var(--text-dim)" }}>{logro.progreso}</span>
                        )}
                      </div>
                    ))}
                  </div>
                </section>

                {/* ═══ TÍTULOS ═══ */}
                <section className="mb-8 sm:mb-10">
                  <SectionHeading icon={<IconTrophy />} title="Títulos" subtitle="Un solo título equipado a la vez — click para equipar o quitar" />
                  {perfil.titulos.length === 0 ? (
                    <div className="chamfer p-6 text-center" style={{ border: "1px dashed var(--border-strong)" }}>
                      <p className="text-xs uppercase tracking-widest m-0" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                        [ Todavía no desbloqueaste títulos ]
                      </p>
                    </div>
                  ) : (
                    <div className="grid gap-3 sm:gap-4" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))" }}>
                      {perfil.titulos.map((titulo) => {
                        const color = RAREZA_COLOR[titulo.rareza].startsWith("var") ? RAREZA_COLOR[titulo.rareza] : `rgb(${RAREZA_COLOR[titulo.rareza]})`
                        return (
                          <button
                            key={titulo.id}
                            type="button"
                            onClick={() => (titulo.equipado ? unequipTitle(titulo.id) : equipTitle(titulo.id))}
                            className="chamfer flex flex-col items-start p-3 text-left cursor-pointer transition-colors"
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
                            <span
                              className="text-[10px] font-bold uppercase px-1.5 py-0.5"
                              style={{
                                color: titulo.equipado ? "var(--signal-green)" : "var(--text-dim)",
                                backgroundColor: titulo.equipado ? "rgba(51,214,159,0.12)" : "transparent",
                              }}
                            >
                              {titulo.equipado ? "Equipado" : "Equipar"}
                            </span>
                          </button>
                        )
                      })}
                    </div>
                  )}
                </section>

                {/* ═══ INVENTARIO ═══ */}
                <section>
                  <SectionHeading icon={<IconTrophy />} title="Inventario" subtitle="Click para equipar o quitar" />
                  {perfil.cosmeticos.length === 0 ? (
                    <div className="chamfer p-6 text-center" style={{ border: "1px dashed var(--border-strong)" }}>
                      <p className="text-xs uppercase tracking-widest m-0" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                        [ Todavía no desbloqueaste cosméticos — completá laboratorios para conseguirlos ]
                      </p>
                    </div>
                  ) : (
                    <div className="grid gap-3 sm:gap-4" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))" }}>
                      {perfil.cosmeticos.map((item) => (
                        <button
                          key={item.id}
                          type="button"
                          onClick={() => (item.equipado ? unequip(item.id) : equip(item.id))}
                          className="chamfer flex flex-col items-start p-3 text-left cursor-pointer transition-colors"
                          style={{
                            backgroundColor: item.equipado ? `rgba(${item.color}, 0.12)` : "var(--surface)",
                            border: `1px solid ${item.equipado ? `rgb(${item.color})` : "var(--border-default)"}`,
                          }}
                        >
                          <span className="w-4 h-4 chamfer-sm mb-2" style={{ backgroundColor: `rgb(${item.color})` }} />
                          <span className="text-xs font-bold" style={{ color: "var(--text-heading)" }}>{item.nombre}</span>
                          <span className="text-[10px] uppercase tracking-wide mt-0.5" style={{ color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                            {TIPO_LABEL[item.tipo]}
                          </span>
                          <span
                            className="text-[10px] font-bold uppercase mt-2 px-1.5 py-0.5"
                            style={{
                              color: item.equipado ? "var(--signal-green)" : "var(--text-dim)",
                              backgroundColor: item.equipado ? "rgba(51,214,159,0.12)" : "transparent",
                            }}
                          >
                            {item.equipado ? "Equipado" : "Equipar"}
                          </span>
                        </button>
                      ))}
                    </div>
                  )}
                </section>
              </>
            )}
          </div>
        </main>
        <Footer />
      </div>
    </div>
  )
}
