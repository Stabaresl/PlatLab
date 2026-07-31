import { useRef, useState } from "react"
import { motion } from "framer-motion"
import { AVATAR_PRESETS } from "../lib/avatarPresets"
import { useGamificationStore } from "../store/gamificationStore"
import { resolveMediaUrl, type PerfilJugador } from "../pages/api"
import { Button } from "./ui/button"

const MAX_TAMANO_MB = 2

// Selector de avatar — grilla de predeterminados (emoji + color) más la
// opción de subir una foto propia. Reusa framer-motion (ya instalado)
// para el resaltado del preset elegido, sin ninguna librería nueva.
export default function AvatarPicker({ perfil }: { perfil: PerfilJugador }) {
  const { setAvatarPreset, uploadAvatarFile } = useGamificationStore()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [busy, setBusy] = useState(false)
  const [localError, setLocalError] = useState("")
  const [preview, setPreview] = useState<string | null>(null)

  const handlePreset = async (clave: string) => {
    if (busy) return
    setBusy(true)
    await setAvatarPreset(clave)
    setBusy(false)
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const archivo = e.target.files?.[0]
    e.target.value = ""
    if (!archivo) return

    if (!archivo.type.startsWith("image/")) {
      setLocalError("El archivo debe ser una imagen.")
      return
    }
    if (archivo.size > MAX_TAMANO_MB * 1024 * 1024) {
      setLocalError(`La imagen no puede superar ${MAX_TAMANO_MB} MB.`)
      return
    }

    setLocalError("")
    setPreview(URL.createObjectURL(archivo))
    setBusy(true)
    await uploadAvatarFile(archivo)
    setBusy(false)
    setPreview(null)
  }

  return (
    <div>
      <div className="grid gap-2 sm:gap-3 mb-4" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(84px, 1fr))" }}>
        {AVATAR_PRESETS.map((p) => {
          const activo = perfil.avatar_tipo === "preset" && perfil.avatar_valor === p.clave
          return (
            <button
              key={p.clave}
              type="button"
              disabled={busy}
              onClick={() => handlePreset(p.clave)}
              title={p.nombre}
              className="relative chamfer-sm flex flex-col items-center gap-1 p-2 cursor-pointer transition-colors disabled:opacity-50 disabled:cursor-wait"
              style={{
                backgroundColor: activo ? `rgba(${p.color}, 0.14)` : "var(--surface)",
                border: `1px solid ${activo ? `rgb(${p.color})` : "var(--border-default)"}`,
              }}
            >
              {activo && (
                <motion.span
                  layoutId="avatar-preset-activo"
                  className="absolute inset-0 chamfer-sm"
                  style={{ border: `2px solid rgb(${p.color})` }}
                  transition={{ duration: 0.2 }}
                />
              )}
              <span style={{ fontSize: 26, lineHeight: 1 }}>{p.emoji}</span>
              <span className="text-[9px] text-center leading-tight" style={{ color: "var(--text-muted)" }}>{p.nombre}</span>
            </button>
          )
        })}
      </div>

      <div className="flex items-center gap-3">
        {preview && (
          <img src={preview} alt="Vista previa" className="w-10 h-10 chamfer-sm object-cover" style={{ border: "1px solid var(--border-default)" }} />
        )}
        {perfil.avatar_tipo === "subido" && !preview && (
          <img
            src={resolveMediaUrl(perfil.avatar_valor)}
            alt="Tu avatar actual"
            className="w-10 h-10 chamfer-sm object-cover"
            style={{ border: "1px solid var(--signal-cyan)" }}
          />
        )}
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={busy}
          onClick={() => fileInputRef.current?.click()}
          className="chamfer-sm font-mono text-xs uppercase tracking-wide"
        >
          {busy ? "Subiendo…" : "Subir tu foto"}
        </Button>
        <input ref={fileInputRef} type="file" accept="image/png,image/jpeg,image/gif" className="hidden" onChange={handleFileChange} />
      </div>
      {localError && <p className="text-xs mt-2" style={{ color: "var(--signal-red)" }}>{localError}</p>}
    </div>
  )
}
