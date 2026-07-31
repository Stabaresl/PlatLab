import { create } from "zustand"
import {
  getPerfilGamificacion,
  equiparCosmetico,
  quitarCosmetico,
  equiparTitulo,
  quitarTitulo,
  cambiarAvatarPreset,
  uploadAvatar,
  ApiError,
  type PerfilJugador,
} from "../pages/api"

interface GamificationState {
  perfil: PerfilJugador | null
  loading: boolean
  error: string
  load: () => Promise<void>
  equip: (cosmeticoDesbloqueadoId: string) => Promise<void>
  unequip: (cosmeticoDesbloqueadoId: string) => Promise<void>
  equipTitle: (tituloDesbloqueadoId: string) => Promise<void>
  unequipTitle: (tituloDesbloqueadoId: string) => Promise<void>
  setAvatarPreset: (clave: string) => Promise<void>
  uploadAvatarFile: (archivo: File) => Promise<void>
}

// Estado global del "avatar" (perfil de progresión + inventario
// equipado) — se usa tanto en el badge chico del Navbar como en
// ProfilePage, sin tener que re-fetchear en cada lugar ni pasar props
// por muchos niveles (el usuario propuso Zustand explícitamente para
// esto).
export const useGamificationStore = create<GamificationState>((set, get) => ({
  perfil: null,
  loading: false,
  error: "",

  load: async () => {
    set({ loading: true, error: "" })
    try {
      const perfil = await getPerfilGamificacion()
      set({ perfil, loading: false })
    } catch (err) {
      set({
        loading: false,
        error: err instanceof ApiError ? err.message : "No se pudo cargar tu progresión.",
      })
    }
  },

  equip: async (cosmeticoDesbloqueadoId: string) => {
    const perfilActual = get().perfil
    if (!perfilActual) return
    try {
      await equiparCosmetico(cosmeticoDesbloqueadoId)
      await get().load()
    } catch (err) {
      set({ error: err instanceof ApiError ? err.message : "No se pudo equipar el cosmético." })
    }
  },

  unequip: async (cosmeticoDesbloqueadoId: string) => {
    try {
      await quitarCosmetico(cosmeticoDesbloqueadoId)
      await get().load()
    } catch (err) {
      set({ error: err instanceof ApiError ? err.message : "No se pudo quitar el cosmético." })
    }
  },

  equipTitle: async (tituloDesbloqueadoId: string) => {
    try {
      await equiparTitulo(tituloDesbloqueadoId)
      await get().load()
    } catch (err) {
      set({ error: err instanceof ApiError ? err.message : "No se pudo equipar el título." })
    }
  },

  unequipTitle: async (tituloDesbloqueadoId: string) => {
    try {
      await quitarTitulo(tituloDesbloqueadoId)
      await get().load()
    } catch (err) {
      set({ error: err instanceof ApiError ? err.message : "No se pudo quitar el título." })
    }
  },

  setAvatarPreset: async (clave: string) => {
    try {
      await cambiarAvatarPreset(clave)
      await get().load()
    } catch (err) {
      set({ error: err instanceof ApiError ? err.message : "No se pudo cambiar el avatar." })
    }
  },

  uploadAvatarFile: async (archivo: File) => {
    try {
      await uploadAvatar(archivo)
      await get().load()
    } catch (err) {
      set({ error: err instanceof ApiError ? err.message : "No se pudo subir la imagen." })
    }
  },
}))
