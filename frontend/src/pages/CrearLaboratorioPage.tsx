import { useState } from "react"
import { useNavigate } from "react-router-dom"
import ReactMarkdown from "react-markdown"
import {
  createLaboratorio,
  createSeccion,
  defineFlag,
  uploadDockerfile,
  createExamen,
  addPregunta,
  submitLabForReview,
  ApiError,
  type NivelDificultad,
} from "./api"
import Navbar from "../components/Navbar"
import Footer from "../components/Footer"
import HeroBackground from "../components/HeroBackground"
import TerminalHeader from "../components/TerminalHeader"
import { Button } from "../components/ui/button"
import { Input } from "../components/ui/input"
import { Label } from "../components/ui/label"
import { Textarea } from "../components/ui/textarea"
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "../components/ui/select"

const STEPS = ["Datos generales", "Secciones", "Examen", "Cierre", "Revisar y enviar"]

interface PasoGuiaForm {
  titulo: string
  instrucciones: string
  comando_sugerido: string
}
interface ComandoForm {
  comando: string
  salida: string
}
interface SeccionForm {
  titulo: string
  contenido_teorico: string
  objetivos: string
  duracion_estimada_minutos: number
  tiene_practica: boolean
  pasos_guia: PasoGuiaForm[]
  entorno_prompt: string
  entorno_banner: string
  comandos: ComandoForm[]
  flag_valor: string
  flag_pista: string
  flag_paso_a_paso: string
  imagen_practica: string
  dockerfile: File | null
}
interface PreguntaForm {
  enunciado: string
  tipo: "opcion_multiple" | "abierta"
  respuesta: string
  opciones: string
}

function nuevaSeccion(): SeccionForm {
  return {
    titulo: "",
    contenido_teorico: "",
    objetivos: "",
    duracion_estimada_minutos: 15,
    tiene_practica: false,
    pasos_guia: [],
    entorno_prompt: "root@lab:~#",
    entorno_banner: "",
    comandos: [],
    flag_valor: "",
    flag_pista: "",
    flag_paso_a_paso: "",
    imagen_practica: "",
    dockerfile: null,
  }
}

const labelCls = "text-xs uppercase tracking-wide"
const labelStyle = { color: "var(--text-muted)", fontFamily: "var(--font-mono)" } as const

function FieldLabel({ children }: { children: React.ReactNode }) {
  return <Label className={labelCls} style={labelStyle}>{children}</Label>
}

function MarkdownEditor({
  value,
  onChange,
  placeholder,
  rows = 6,
}: {
  value: string
  onChange: (v: string) => void
  placeholder?: string
  rows?: number
}) {
  const [tab, setTab] = useState<"escribir" | "preview">("escribir")

  const cargarArchivo = async (file: File | undefined) => {
    if (!file) return
    onChange(await file.text())
  }

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div className="flex gap-1">
          <button type="button" onClick={() => setTab("escribir")} className="chamfer-sm px-2 py-1 text-[10px] uppercase font-mono cursor-pointer border" style={{ backgroundColor: tab === "escribir" ? "var(--surface-hover)" : "transparent", borderColor: "var(--border-default)", color: tab === "escribir" ? "var(--signal-cyan)" : "var(--text-muted)" }}>
            Escribir
          </button>
          <button type="button" onClick={() => setTab("preview")} className="chamfer-sm px-2 py-1 text-[10px] uppercase font-mono cursor-pointer border" style={{ backgroundColor: tab === "preview" ? "var(--surface-hover)" : "transparent", borderColor: "var(--border-default)", color: tab === "preview" ? "var(--signal-cyan)" : "var(--text-muted)" }}>
            Vista previa
          </button>
        </div>
        <label className="chamfer-sm px-2 py-1 text-[10px] uppercase font-mono cursor-pointer border" style={{ borderColor: "var(--border-default)", color: "var(--text-muted)" }}>
          Cargar .md
          <input type="file" accept=".md,.markdown,.txt" className="hidden" onChange={(e) => cargarArchivo(e.target.files?.[0])} />
        </label>
      </div>
      {tab === "escribir" ? (
        <Textarea value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder} rows={rows} className="chamfer-sm font-mono text-sm" />
      ) : (
        <div className="chamfer-sm p-3 text-sm prose-invert" style={{ backgroundColor: "var(--surface-sunken)", border: "1px solid var(--border-default)", color: "var(--text-base)", minHeight: rows * 24 }}>
          {value.trim() ? <ReactMarkdown>{value}</ReactMarkdown> : <span style={{ color: "var(--text-dim)" }}>Sin contenido todavía.</span>}
        </div>
      )}
    </div>
  )
}

export default function CrearLaboratorioPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState(0)

  const [nombre, setNombre] = useState("")
  const [descripcion, setDescripcion] = useState("")
  const [nivelDificultad, setNivelDificultad] = useState<NivelDificultad>("basico")
  const [temas, setTemas] = useState("")

  const [secciones, setSecciones] = useState<SeccionForm[]>([nuevaSeccion()])

  const [incluirExamen, setIncluirExamen] = useState(false)
  const [preguntas, setPreguntas] = useState<PreguntaForm[]>([])

  const [resumenCierre, setResumenCierre] = useState("")

  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState("")

  const patchSeccion = (i: number, patch: Partial<SeccionForm>) =>
    setSecciones((prev) => prev.map((s, idx) => (idx === i ? { ...s, ...patch } : s)))

  const patchPregunta = (i: number, patch: Partial<PreguntaForm>) =>
    setPreguntas((prev) => prev.map((p, idx) => (idx === i ? { ...p, ...patch } : p)))

  const datosGeneralesValidos = nombre.trim().length > 0 && descripcion.trim().length > 0
  const seccionesValidas =
    secciones.length > 0 &&
    secciones.every((s) => s.titulo.trim() && s.contenido_teorico.trim() && (!s.tiene_practica || s.flag_valor.trim()))

  const handleSubmit = async () => {
    setSubmitting(true)
    setError("")
    try {
      const lab = await createLaboratorio({
        nombre,
        descripcion,
        nivel_dificultad: nivelDificultad,
        temas: temas.split(",").map((t) => t.trim()).filter(Boolean),
        resumen_cierre: resumenCierre,
      })

      for (let i = 0; i < secciones.length; i++) {
        const s = secciones[i]
        const seccionResult = await createSeccion(lab.id, {
          titulo: s.titulo,
          contenido_teorico: s.contenido_teorico,
          orden: i + 1,
          tiene_practica: s.tiene_practica,
          objetivos: s.objetivos.split("\n").map((o) => o.trim()).filter(Boolean),
          duracion_estimada_minutos: s.duracion_estimada_minutos || 15,
          pasos_guia: s.tiene_practica
            ? s.pasos_guia
                .filter((p) => p.titulo.trim() && p.instrucciones.trim())
                .map((p, idx) => ({
                  orden: idx + 1,
                  titulo: p.titulo,
                  instrucciones: p.instrucciones,
                  comando_sugerido: p.comando_sugerido.trim() || null,
                }))
            : [],
          entorno_practica:
            s.tiene_practica && s.comandos.length > 0
              ? {
                  prompt: s.entorno_prompt || "root@lab:~#",
                  banner: s.entorno_banner,
                  comandos: s.comandos.filter((c) => c.comando.trim()),
                }
              : null,
          imagen_practica: s.tiene_practica && s.imagen_practica.trim() ? s.imagen_practica.trim() : null,
        })

        if (s.tiene_practica && s.flag_valor.trim()) {
          await defineFlag(lab.id, seccionResult.id, {
            valor: s.flag_valor,
            pista: s.flag_pista.trim() || null,
            paso_a_paso: s.flag_paso_a_paso.trim() || null,
          })
        }
        if (s.tiene_practica && s.dockerfile) {
          await uploadDockerfile(lab.id, seccionResult.id, s.dockerfile)
        }
      }

      const preguntasValidas = preguntas.filter((p) => p.enunciado.trim() && p.respuesta.trim())
      if (incluirExamen && preguntasValidas.length > 0) {
        await createExamen(lab.id)
        for (const p of preguntasValidas) {
          await addPregunta(lab.id, {
            enunciado: p.enunciado,
            tipo: p.tipo,
            respuesta: p.respuesta,
            opciones:
              p.tipo === "opcion_multiple"
                ? p.opciones.split("\n").map((o) => o.trim()).filter(Boolean)
                : null,
          })
        }
      }

      await submitLabForReview(lab.id)
      navigate("/dashboard")
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo crear el laboratorio.")
      setSubmitting(false)
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden" style={{ backgroundColor: "var(--canvas)", color: "var(--text-base)" }}>
      <HeroBackground image="term" imageOpacity={0.06} overlayOpacity={0.9} texture="grid" textureOpacity={0.03} />
      <div className="relative z-10 flex flex-col min-h-screen">
        <Navbar />
        <main className="flex-1">
          <div className="mx-auto px-4 sm:px-6 md:px-8 py-6 sm:py-8" style={{ maxWidth: "900px" }}>
            <TerminalHeader title="Nuevo Laboratorio" subtitle="Se envía a revisión de un administrador antes de publicarse" prompt="instructor → crear-laboratorio" />

            {/* ═══ Stepper ═══ */}
            <div className="flex items-center gap-1.5 mb-6 flex-wrap">
              {STEPS.map((label, i) => (
                <button
                  key={label}
                  type="button"
                  onClick={() => setStep(i)}
                  className="chamfer-sm px-2.5 py-1.5 text-[10px] sm:text-xs font-mono uppercase tracking-wide cursor-pointer border transition-colors"
                  style={{
                    backgroundColor: step === i ? "var(--surface-hover)" : "transparent",
                    borderColor: step === i ? "var(--signal-amber)" : "var(--border-default)",
                    color: step === i ? "var(--signal-amber)" : "var(--text-muted)",
                  }}
                >
                  {i + 1}. {label}
                </button>
              ))}
            </div>

            {error && (
              <p className="text-sm mb-4 px-3 py-2 chamfer-sm" style={{ color: "var(--signal-red)", backgroundColor: "rgba(255,71,87,0.08)", border: "1px solid var(--signal-red-dim)" }} role="alert">
                ▲ {error}
              </p>
            )}

            <div className="chamfer p-4 sm:p-6 mb-5" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-default)" }}>
              {step === 0 && (
                <div className="flex flex-col gap-4">
                  <div className="flex flex-col gap-1.5">
                    <FieldLabel>Nombre *</FieldLabel>
                    <Input value={nombre} onChange={(e) => setNombre(e.target.value)} placeholder="Ej: SQL Injection: Bypass de Login" className="chamfer-sm h-10" />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <FieldLabel>Descripción *</FieldLabel>
                    <Textarea value={descripcion} onChange={(e) => setDescripcion(e.target.value)} rows={3} className="chamfer-sm" placeholder="Resumen breve que se muestra en el catálogo." />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <FieldLabel>Nivel de dificultad</FieldLabel>
                    <Select value={nivelDificultad} onValueChange={(v) => setNivelDificultad(v as NivelDificultad)}>
                      <SelectTrigger className="chamfer-sm w-full h-10">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="basico">Básico</SelectItem>
                        <SelectItem value="intermedio">Intermedio</SelectItem>
                        <SelectItem value="avanzado">Avanzado</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <FieldLabel>Temas (separados por coma)</FieldLabel>
                    <Input value={temas} onChange={(e) => setTemas(e.target.value)} placeholder="sql injection, autenticación" className="chamfer-sm h-10" />
                  </div>
                </div>
              )}

              {step === 1 && (
                <div className="flex flex-col gap-6">
                  {secciones.map((s, i) => (
                    <SeccionEditor
                      key={i}
                      seccion={s}
                      orden={i + 1}
                      onChange={(patch) => patchSeccion(i, patch)}
                      onRemove={secciones.length > 1 ? () => setSecciones((prev) => prev.filter((_, idx) => idx !== i)) : undefined}
                    />
                  ))}
                  <Button type="button" variant="outline" onClick={() => setSecciones((prev) => [...prev, nuevaSeccion()])} className="chamfer-sm font-mono text-xs uppercase self-start">
                    + Agregar sección
                  </Button>
                </div>
              )}

              {step === 2 && (
                <div className="flex flex-col gap-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" checked={incluirExamen} onChange={(e) => setIncluirExamen(e.target.checked)} />
                    <span className="text-sm" style={{ color: "var(--text-base)" }}>Este laboratorio incluye examen final (opcional)</span>
                  </label>

                  {incluirExamen && (
                    <div className="flex flex-col gap-4">
                      {preguntas.map((p, i) => (
                        <div key={i} className="chamfer-sm p-3 flex flex-col gap-2" style={{ backgroundColor: "var(--surface-hover)", border: "1px solid var(--border-hairline)" }}>
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-mono uppercase" style={{ color: "var(--text-muted)" }}>Pregunta {i + 1}</span>
                            <button type="button" onClick={() => setPreguntas((prev) => prev.filter((_, idx) => idx !== i))} className="text-xs cursor-pointer border-none bg-transparent" style={{ color: "var(--signal-red)" }}>
                              Quitar
                            </button>
                          </div>
                          <Input value={p.enunciado} onChange={(e) => patchPregunta(i, { enunciado: e.target.value })} placeholder="Enunciado" className="chamfer-sm h-9" />
                          <Select value={p.tipo} onValueChange={(v) => patchPregunta(i, { tipo: v as PreguntaForm["tipo"] })}>
                            <SelectTrigger className="chamfer-sm w-full h-9">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="opcion_multiple">Opción múltiple</SelectItem>
                              <SelectItem value="abierta">Abierta</SelectItem>
                            </SelectContent>
                          </Select>
                          {p.tipo === "opcion_multiple" && (
                            <Textarea value={p.opciones} onChange={(e) => patchPregunta(i, { opciones: e.target.value })} placeholder={"Una opción por línea"} rows={3} className="chamfer-sm text-sm" />
                          )}
                          <Input value={p.respuesta} onChange={(e) => patchPregunta(i, { respuesta: e.target.value })} placeholder={p.tipo === "opcion_multiple" ? "Opción correcta (tal cual aparece arriba)" : "Respuesta esperada"} className="chamfer-sm h-9" />
                        </div>
                      ))}
                      <Button type="button" variant="outline" onClick={() => setPreguntas((prev) => [...prev, { enunciado: "", tipo: "opcion_multiple", respuesta: "", opciones: "" }])} className="chamfer-sm font-mono text-xs uppercase self-start">
                        + Agregar pregunta
                      </Button>
                    </div>
                  )}
                </div>
              )}

              {step === 3 && (
                <div className="flex flex-col gap-2">
                  <FieldLabel>Resumen de cierre (Markdown, opcional)</FieldLabel>
                  <p className="text-xs mb-1" style={{ color: "var(--text-muted)" }}>Se muestra al estudiante cuando completa todas las secciones del laboratorio.</p>
                  <MarkdownEditor value={resumenCierre} onChange={setResumenCierre} rows={8} placeholder={"## Resumen\n\nLo que el estudiante se lleva de este laboratorio..."} />
                </div>
              )}

              {step === 4 && (
                <div className="flex flex-col gap-3 text-sm" style={{ color: "var(--text-base)" }}>
                  <p><strong style={{ color: "var(--text-heading)" }}>{nombre || "(sin nombre)"}</strong> — {nivelDificultad}</p>
                  <p>{secciones.length} sección{secciones.length === 1 ? "" : "es"}, {secciones.filter((s) => s.tiene_practica).length} con práctica.</p>
                  {incluirExamen && <p>Examen con {preguntas.filter((p) => p.enunciado.trim()).length} pregunta(s).</p>}
                  {!datosGeneralesValidos && <p style={{ color: "var(--signal-red)" }}>Falta nombre/descripción (paso 1).</p>}
                  {!seccionesValidas && <p style={{ color: "var(--signal-red)" }}>Cada sección necesita título, contenido, y si tiene práctica, una flag (paso 2).</p>}
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                    Al enviar, el laboratorio queda en estado "En revisión" — un administrador lo revisa antes de que aparezca publicado en el catálogo.
                  </p>
                </div>
              )}
            </div>

            <div className="flex items-center justify-between gap-3">
              <Button type="button" variant="outline" disabled={step === 0} onClick={() => setStep((s) => Math.max(0, s - 1))} className="chamfer-sm font-mono text-xs uppercase">
                ← Atrás
              </Button>
              {step < STEPS.length - 1 ? (
                <Button type="button" onClick={() => setStep((s) => Math.min(STEPS.length - 1, s + 1))} className="chamfer-sm font-mono text-xs uppercase">
                  Siguiente →
                </Button>
              ) : (
                <Button type="button" disabled={submitting || !datosGeneralesValidos || !seccionesValidas} onClick={handleSubmit} className="chamfer-sm font-mono text-xs uppercase">
                  {submitting ? "Enviando…" : "Enviar a revisión"}
                </Button>
              )}
            </div>
          </div>
        </main>
        <Footer />
      </div>
    </div>
  )
}

function SeccionEditor({
  seccion,
  orden,
  onChange,
  onRemove,
}: {
  seccion: SeccionForm
  orden: number
  onChange: (patch: Partial<SeccionForm>) => void
  onRemove?: () => void
}) {
  const patchPaso = (i: number, patch: Partial<PasoGuiaForm>) =>
    onChange({ pasos_guia: seccion.pasos_guia.map((p, idx) => (idx === i ? { ...p, ...patch } : p)) })
  const patchComando = (i: number, patch: Partial<ComandoForm>) =>
    onChange({ comandos: seccion.comandos.map((c, idx) => (idx === i ? { ...c, ...patch } : c)) })

  return (
    <div className="chamfer-sm p-4 flex flex-col gap-3" style={{ backgroundColor: "var(--surface-hover)", border: "1px solid var(--border-default)" }}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold font-mono uppercase" style={{ color: "var(--signal-amber)" }}>Sección {orden}</span>
        {onRemove && (
          <button type="button" onClick={onRemove} className="text-xs cursor-pointer border-none bg-transparent" style={{ color: "var(--signal-red)" }}>
            Quitar sección
          </button>
        )}
      </div>

      <div className="flex flex-col gap-1.5">
        <FieldLabel>Título *</FieldLabel>
        <Input value={seccion.titulo} onChange={(e) => onChange({ titulo: e.target.value })} className="chamfer-sm h-9" />
      </div>

      <div className="flex flex-col gap-1.5">
        <FieldLabel>Contenido teórico * (Markdown)</FieldLabel>
        <MarkdownEditor value={seccion.contenido_teorico} onChange={(v) => onChange({ contenido_teorico: v })} rows={6} />
      </div>

      <div className="flex flex-col gap-1.5">
        <FieldLabel>Objetivos (uno por línea)</FieldLabel>
        <Textarea value={seccion.objetivos} onChange={(e) => onChange({ objetivos: e.target.value })} rows={3} className="chamfer-sm text-sm" />
      </div>

      <div className="flex flex-col gap-1.5 max-w-[200px]">
        <FieldLabel>Duración estimada (min)</FieldLabel>
        <Input type="number" min={1} value={seccion.duracion_estimada_minutos} onChange={(e) => onChange({ duracion_estimada_minutos: Number(e.target.value) || 15 })} className="chamfer-sm h-9" />
      </div>

      <label className="flex items-center gap-2 cursor-pointer">
        <input type="checkbox" checked={seccion.tiene_practica} onChange={(e) => onChange({ tiene_practica: e.target.checked })} />
        <span className="text-sm" style={{ color: "var(--text-base)" }}>Esta sección tiene práctica (flag + consola)</span>
      </label>

      {seccion.tiene_practica && (
        <div className="flex flex-col gap-4 pl-3" style={{ borderLeft: "2px solid var(--border-default)" }}>
          {/* Pasos de la guía */}
          <div className="flex flex-col gap-2">
            <FieldLabel>Pasos de la guía</FieldLabel>
            {seccion.pasos_guia.map((p, i) => (
              <div key={i} className="chamfer-sm p-3 flex flex-col gap-2" style={{ backgroundColor: "var(--surface)", border: "1px solid var(--border-hairline)" }}>
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono uppercase" style={{ color: "var(--text-muted)" }}>Paso {i + 1}</span>
                  <button type="button" onClick={() => onChange({ pasos_guia: seccion.pasos_guia.filter((_, idx) => idx !== i) })} className="text-xs cursor-pointer border-none bg-transparent" style={{ color: "var(--signal-red)" }}>
                    Quitar
                  </button>
                </div>
                <Input value={p.titulo} onChange={(e) => patchPaso(i, { titulo: e.target.value })} placeholder="Título del paso" className="chamfer-sm h-9" />
                <MarkdownEditor value={p.instrucciones} onChange={(v) => patchPaso(i, { instrucciones: v })} rows={3} placeholder="Instrucciones (Markdown)" />
                <Input value={p.comando_sugerido} onChange={(e) => patchPaso(i, { comando_sugerido: e.target.value })} placeholder="Comando sugerido (opcional)" className="chamfer-sm h-9 font-mono" />
              </div>
            ))}
            <Button type="button" variant="outline" size="sm" onClick={() => onChange({ pasos_guia: [...seccion.pasos_guia, { titulo: "", instrucciones: "", comando_sugerido: "" }] })} className="chamfer-sm font-mono text-xs uppercase self-start">
              + Agregar paso
            </Button>
          </div>

          {/* Consola simulada */}
          <div className="flex flex-col gap-2">
            <FieldLabel>Consola simulada</FieldLabel>
            <div className="flex gap-2">
              <Input value={seccion.entorno_prompt} onChange={(e) => onChange({ entorno_prompt: e.target.value })} placeholder="prompt" className="chamfer-sm h-9 font-mono flex-1" />
            </div>
            <Textarea value={seccion.entorno_banner} onChange={(e) => onChange({ entorno_banner: e.target.value })} placeholder="Banner de bienvenida de la consola" rows={2} className="chamfer-sm text-sm" />
            {seccion.comandos.map((c, i) => (
              <div key={i} className="flex flex-col sm:flex-row gap-2 items-start">
                <Input value={c.comando} onChange={(e) => patchComando(i, { comando: e.target.value })} placeholder="comando" className="chamfer-sm h-9 font-mono flex-1" />
                <Textarea value={c.salida} onChange={(e) => patchComando(i, { salida: e.target.value })} placeholder="salida simulada" rows={2} className="chamfer-sm text-sm font-mono flex-1" />
                <button type="button" onClick={() => onChange({ comandos: seccion.comandos.filter((_, idx) => idx !== i) })} className="text-xs cursor-pointer border-none bg-transparent shrink-0" style={{ color: "var(--signal-red)" }}>
                  Quitar
                </button>
              </div>
            ))}
            <Button type="button" variant="outline" size="sm" onClick={() => onChange({ comandos: [...seccion.comandos, { comando: "", salida: "" }] })} className="chamfer-sm font-mono text-xs uppercase self-start">
              + Agregar comando
            </Button>
          </div>

          {/* Flag */}
          <div className="flex flex-col gap-2">
            <FieldLabel>Flag *</FieldLabel>
            <Input value={seccion.flag_valor} onChange={(e) => onChange({ flag_valor: e.target.value })} placeholder="FLAG{...}" className="chamfer-sm h-9 font-mono" />
            <Input value={seccion.flag_pista} onChange={(e) => onChange({ flag_pista: e.target.value })} placeholder="Pista (opcional)" className="chamfer-sm h-9" />
            <Textarea value={seccion.flag_paso_a_paso} onChange={(e) => onChange({ flag_paso_a_paso: e.target.value })} placeholder="Paso a paso de ayuda progresiva (opcional)" rows={2} className="chamfer-sm text-sm" />
          </div>

          {/* Entorno real */}
          <div className="flex flex-col gap-2">
            <FieldLabel>Entorno real (opcional)</FieldLabel>
            <Input value={seccion.imagen_practica} onChange={(e) => onChange({ imagen_practica: e.target.value })} placeholder="Nombre de la imagen Docker (la asigna un admin tras revisar el Dockerfile)" className="chamfer-sm h-9 font-mono" />
            <label className="chamfer-sm px-3 py-2 text-xs uppercase font-mono cursor-pointer border self-start" style={{ borderColor: "var(--border-default)", color: "var(--text-muted)" }}>
              {seccion.dockerfile ? `Dockerfile: ${seccion.dockerfile.name}` : "Subir Dockerfile / contexto (.zip)"}
              <input type="file" className="hidden" onChange={(e) => onChange({ dockerfile: e.target.files?.[0] || null })} />
            </label>
          </div>
        </div>
      )}
    </div>
  )
}
