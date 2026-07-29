// Cliente HTTP para la API real de PlatLAB (Django/DRF, `/api/v1`).
// Reemplaza el mock (Bun/Express en :3001) de la rama mik4ela.

const BASE = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000/api/v1"

// Los botones de Google/GitHub solo tienen sentido si el backend tiene
// credenciales OAuth reales configuradas (GOOGLE_OAUTH_CLIENT_ID / GITHUB_
// OAUTH_CLIENT_ID en .env) — sin ellas, el proveedor devuelve un 404/400
// al recibir `client_id` vacío. Se ocultan por defecto para no dejar al
// usuario en un callejón sin salida; activar con VITE_OAUTH_ENABLED=true.
export const OAUTH_ENABLED = (import.meta as any).env?.VITE_OAUTH_ENABLED === "true"

// ---------------------------------------------------------------------------
// Tokens (SimpleJWT: access de vida corta + refresh rotado, seguridad.md §2)
// ---------------------------------------------------------------------------

export function getAccessToken(): string | null {
  return localStorage.getItem("token")
}

export function getRefreshToken(): string | null {
  return localStorage.getItem("refresh_token")
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem("token", access)
  localStorage.setItem("refresh_token", refresh)
}

export function clearTokens() {
  localStorage.removeItem("token")
  localStorage.removeItem("refresh_token")
  localStorage.removeItem("role")
  localStorage.removeItem("profile")
}

export function logout() {
  clearTokens()
  window.location.href = "/login"
}

// El access token solo trae `sub` (uuid) y `rol` como claims (JWTService) —
// no hay endpoint "/me", así que el rol/id salen de decodificar el JWT.
export interface JwtClaims {
  sub: string
  rol: Rol
  exp: number
  jti?: string
}

export function decodeJwt(token: string): JwtClaims | null {
  try {
    const payload = token.split(".")[1]
    const json = atob(payload.replace(/-/g, "+").replace(/_/g, "/"))
    return JSON.parse(json)
  } catch {
    return null
  }
}

export function getCurrentUser(): { id: string; rol: Rol } | null {
  const token = getAccessToken()
  if (!token) return null
  const claims = decodeJwt(token)
  if (!claims) return null
  return { id: claims.sub, rol: claims.rol }
}

// Perfil (nombre/email) no existe como endpoint self-service en el backend
// (GET /users/{id}/ es solo-admin) — se guarda localmente lo que el propio
// usuario ingresó en login/signup, a título informativo para el saludo.
export interface LocalProfile {
  email: string
  nombre_completo?: string
}

export function setLocalProfile(profile: LocalProfile) {
  localStorage.setItem("profile", JSON.stringify(profile))
}

export function getLocalProfile(): LocalProfile | null {
  const raw = localStorage.getItem("profile")
  return raw ? JSON.parse(raw) : null
}

// ---------------------------------------------------------------------------
// Errores (api.md §2: { error: { code, message, details } })
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  code: string
  details: { field: string; message: string }[]
  status: number

  constructor(status: number, code: string, message: string, details: { field: string; message: string }[] = []) {
    super(message)
    this.status = status
    this.code = code
    this.details = details
  }
}

let refreshInFlight: Promise<boolean> | null = null

async function tryRefresh(): Promise<boolean> {
  const refresh = getRefreshToken()
  if (!refresh) return false
  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      try {
        const res = await fetch(`${BASE}/auth/refresh/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh }),
        })
        if (!res.ok) return false
        const data = await res.json()
        setTokens(data.access, data.refresh)
        return true
      } catch {
        return false
      } finally {
        refreshInFlight = null
      }
    })()
  }
  return refreshInFlight
}

interface RequestOptions extends RequestInit {
  skipAuth?: boolean
  skipRetry?: boolean
}

export async function api<T>(path: string, options?: RequestOptions): Promise<T> {
  const { skipAuth, skipRetry, ...rest } = options || {}
  const token = skipAuth ? null : getAccessToken()
  const isFormData = rest.body instanceof FormData

  const res = await fetch(`${BASE}${path}`, {
    ...rest,
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...rest.headers,
    },
  })

  if (res.status === 204) return undefined as T

  if (res.status === 401 && !skipAuth && !skipRetry) {
    const refreshed = await tryRefresh()
    if (refreshed) {
      return api<T>(path, { ...options, skipRetry: true })
    }
    clearTokens()
    window.location.href = "/login"
    throw new ApiError(401, "UNAUTHENTICATED", "Sesión expirada.")
  }

  const data = await res.json().catch(() => ({}))

  if (!res.ok) {
    const err = data.error || {}
    throw new ApiError(res.status, err.code || "INTERNAL_ERROR", err.message || "Ocurrió un error inesperado.", err.details || [])
  }

  return data as T
}

// ---------------------------------------------------------------------------
// Dominio compartido
// ---------------------------------------------------------------------------

export type Rol = "estudiante" | "instructor" | "administrador"
export type NivelDificultad = "basico" | "intermedio" | "avanzado"
export type EstadoLaboratorio = "borrador" | "publicado"
export type TipoLaboratorio = "predeterminado" | "personalizado"
export type EstadoAsignacion = "pendiente" | "aceptada" | "rechazada" | "activa" | "vencida"
export type EstadoReporte = "abierto" | "en_revision" | "resuelto" | "no_reproducible"

// ---------------------------------------------------------------------------
// Auth — /api/v1/auth
// ---------------------------------------------------------------------------

export interface TokenPair {
  access: string
  refresh: string
  expires_in: number
  rol: Rol
}

export function register(body: {
  email: string
  password: string
  password_confirm: string
  nombre_completo: string
}) {
  return api<{ id: string; email: string; rol: Rol; email_verificado: boolean }>("/auth/register/", {
    method: "POST",
    skipAuth: true,
    body: JSON.stringify(body),
  })
}

export function login(body: { email: string; password: string }) {
  return api<TokenPair>("/auth/login/", {
    method: "POST",
    skipAuth: true,
    body: JSON.stringify(body),
  })
}

export function requestPasswordReset(email: string) {
  return api<{ message: string }>("/auth/password-reset/", {
    method: "POST",
    skipAuth: true,
    body: JSON.stringify({ email }),
  })
}

export function confirmPasswordReset(body: { token: string; password: string; password_confirm: string }) {
  return api<{ message: string }>("/auth/password-reset/confirm/", {
    method: "POST",
    skipAuth: true,
    body: JSON.stringify(body),
  })
}

export type OAuthProvider = "google" | "github"

export function oauthAuthorize(provider: OAuthProvider) {
  return api<{ authorize_url: string; state: string }>(`/auth/oauth/${provider}/authorize/`, {
    skipAuth: true,
  })
}

export function oauthCallback(provider: OAuthProvider, body: { code: string; state: string }) {
  return api<TokenPair>(`/auth/oauth/${provider}/callback/`, {
    method: "POST",
    skipAuth: true,
    body: JSON.stringify(body),
  })
}

export function oauthConfirmLink(body: { link_token: string; password: string }) {
  return api<TokenPair>("/auth/oauth/confirm-link/", {
    method: "POST",
    skipAuth: true,
    body: JSON.stringify(body),
  })
}

// ---------------------------------------------------------------------------
// Laboratories — /api/v1/laboratories
// ---------------------------------------------------------------------------

export interface LaboratorioListItem {
  id: string
  nombre: string
  descripcion: string
  nivel_dificultad: NivelDificultad
  estado: EstadoLaboratorio
  temas: string[]
  inscrito: boolean
}

export interface LaboratorioDetalle {
  id: string
  nombre: string
  descripcion: string
  nivel_dificultad: NivelDificultad
  estado: EstadoLaboratorio
  temas: string[]
  total_secciones: number
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export function getCatalogo(params?: { dificultad?: NivelDificultad; tema?: string; nombre?: string }) {
  const qs = new URLSearchParams(params as Record<string, string>).toString()
  return api<PaginatedResponse<LaboratorioListItem>>(`/laboratories/${qs ? `?${qs}` : ""}`)
}

export function getLaboratorio(id: string) {
  return api<LaboratorioDetalle>(`/laboratories/${id}/`)
}

export function getToc(id: string) {
  return api<{
    laboratorio_id: string
    secciones: { orden: number; titulo: string; tiene_practica: boolean }[]
  }>(`/laboratories/${id}/toc/`)
}

export function createLaboratorio(body: {
  nombre: string
  descripcion: string
  nivel_dificultad: NivelDificultad
  temas?: string[]
}) {
  return api<{ id: string; nombre: string; estado: EstadoLaboratorio; tipo: TipoLaboratorio }>("/laboratories/", {
    method: "POST",
    body: JSON.stringify(body),
  })
}

export function updateLaboratorio(id: string, body: Partial<{
  nombre: string
  descripcion: string
  nivel_dificultad: NivelDificultad
  temas: string[]
}>) {
  return api<{ id: string; nombre: string; estado: EstadoLaboratorio; tipo: TipoLaboratorio }>(`/laboratories/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(body),
  })
}

export function publishLaboratorio(id: string) {
  return api<{ id: string; nombre: string; estado: EstadoLaboratorio; tipo: TipoLaboratorio }>(`/laboratories/${id}/publish/`, {
    method: "POST",
  })
}

export function duplicateLaboratorio(id: string) {
  return api<{ id: string; nombre: string; estado: EstadoLaboratorio; tipo: TipoLaboratorio }>(`/laboratories/${id}/duplicate/`, {
    method: "POST",
  })
}

export function createSeccion(laboratorioId: string, body: {
  titulo: string
  contenido_teorico: string
  orden: number
  tiene_practica?: boolean
}) {
  return api<{ id: string; laboratorio_id: string; orden: number; titulo: string; tiene_practica: boolean }>(
    `/laboratories/${laboratorioId}/sections/`,
    { method: "POST", body: JSON.stringify(body) },
  )
}

export function defineFlag(laboratorioId: string, sectionId: string, body: {
  valor: string
  pista?: string | null
  paso_a_paso?: string | null
}) {
  return api<{ id: string; seccion_id: string }>(`/laboratories/${laboratorioId}/sections/${sectionId}/flag/`, {
    method: "PUT",
    body: JSON.stringify(body),
  })
}

export function createExamen(laboratorioId: string) {
  return api<{ id: string; laboratorio_id: string }>(`/laboratories/${laboratorioId}/exam/`, { method: "POST" })
}

export function addPregunta(laboratorioId: string, body: {
  enunciado: string
  tipo: "opcion_multiple" | "abierta"
  respuesta: string
  opciones?: string[] | null
}) {
  return api<{ id: string; examen_id: string; enunciado: string; tipo: string; opciones: string[] | null }>(
    `/laboratories/${laboratorioId}/exam/questions/`,
    { method: "POST", body: JSON.stringify(body) },
  )
}

// ---------------------------------------------------------------------------
// Assignments — /api/v1/assignments
// ---------------------------------------------------------------------------

export interface Asignacion {
  id: string
  estudiante_id: string
  laboratorio_id: string
  estado: EstadoAsignacion
  fecha_invitacion: string
  fecha_vencimiento: string | null
}

export function listAssignments() {
  return api<Asignacion[]>("/assignments/")
}

export function inviteStudents(body: { laboratorio_id: string; estudiantes: string[]; fecha_vencimiento?: string | null }) {
  return api<{
    invitaciones: { identificador: string; resultado: string; asignacion_id: string | null }[]
  }>("/assignments/invitations/", { method: "POST", body: JSON.stringify(body) })
}

export function acceptInvitation(id: string) {
  return api<Asignacion>(`/assignments/invitations/${id}/accept/`, { method: "POST" })
}

export function rejectInvitation(id: string) {
  return api<Asignacion>(`/assignments/invitations/${id}/reject/`, { method: "POST" })
}

export interface EstudianteFiltrado {
  estudiante_id: string
  nombre_completo: string
  laboratorio_id: string
  estado_asignacion: EstadoAsignacion
  porcentaje_completitud: number
}

export function listStudents(params?: { nombre?: string; laboratorio_id?: string }) {
  const qs = new URLSearchParams(params as Record<string, string>).toString()
  return api<EstudianteFiltrado[]>(`/assignments/students${qs ? `?${qs}` : ""}`)
}

export interface InstructorDashboardItem {
  laboratorio_id: string
  nombre: string
  estado: EstadoLaboratorio
  estudiantes_inscritos: number
  porcentaje_completitud_promedio: number
}

export function getInstructorDashboard() {
  return api<InstructorDashboardItem[]>("/assignments/dashboard/")
}

// ---------------------------------------------------------------------------
// Users — /api/v1/users (mayormente solo-admin)
// ---------------------------------------------------------------------------

export interface UsuarioItem {
  id: string
  email: string
  nombre_completo: string
  rol: Rol
  is_active: boolean
}

export function listUsers(params?: { rol?: Rol; is_active?: boolean }) {
  const qs = new URLSearchParams(params as unknown as Record<string, string>).toString()
  return api<UsuarioItem[]>(`/users/${qs ? `?${qs}` : ""}`)
}

export function getUser(id: string) {
  return api<UsuarioItem>(`/users/${id}/`)
}

export function updateUser(id: string, body: Partial<{ nombre_completo: string; rol: Rol }>) {
  return api<UsuarioItem>(`/users/${id}/`, { method: "PATCH", body: JSON.stringify(body) })
}

export function disableUser(id: string) {
  return api<UsuarioItem>(`/users/${id}/disable/`, { method: "POST" })
}

export function enableUser(id: string) {
  return api<UsuarioItem>(`/users/${id}/enable/`, { method: "POST" })
}

export interface AdminDashboard {
  usuarios_por_rol: Record<string, number>
  laboratorios_activos: number
  labs_mas_populares: { laboratorio_id: string; nombre: string; estudiantes_inscritos: number }[]
  tasa_completitud_promedio: number
}

export function getAdminDashboard() {
  return api<AdminDashboard>("/users/dashboard/")
}

// ---------------------------------------------------------------------------
// Progress — /api/v1/progress
// ---------------------------------------------------------------------------

export function getSectionContent(assignmentId: string, sectionId: string) {
  return api<{ seccion_id: string; titulo: string; contenido_teorico: string; tiene_practica: boolean; estado: string }>(
    `/progress/${assignmentId}/sections/${sectionId}/`,
  )
}

export function submitFlag(assignmentId: string, sectionId: string, valor: string) {
  return api<{
    correcto: boolean
    seccion_desbloqueada?: string | null
    intentos_fallidos?: number
    pista_disponible?: boolean
    pista?: string
    paso_a_paso_disponible?: boolean
    paso_a_paso?: string
  }>(`/progress/${assignmentId}/sections/${sectionId}/flag/`, {
    method: "POST",
    body: JSON.stringify({ valor }),
  })
}

export function getHint(assignmentId: string, sectionId: string) {
  return api<{
    intentos_fallidos: number
    pista_disponible: boolean
    paso_a_paso_disponible: boolean
    pista?: string
    paso_a_paso?: string
  }>(`/progress/${assignmentId}/sections/${sectionId}/hint/`)
}

export function submitExam(assignmentId: string, respuestas: Record<string, string>) {
  return api<{ puntaje: number; correctas: number; total: number; numero_intento: number }>(
    `/progress/${assignmentId}/exam/`,
    { method: "POST", body: JSON.stringify({ respuestas }) },
  )
}

export function getHistory(assignmentId: string) {
  return api<{ numero_intento: number; fecha_completado: string; puntaje: number }[]>(
    `/progress/${assignmentId}/history/`,
  )
}

// ---------------------------------------------------------------------------
// Reports — /api/v1/reports
// ---------------------------------------------------------------------------

export interface Reporte {
  id: string
  laboratorio_id: string
  estado: EstadoReporte
  descripcion?: string
  fecha_creacion: string
  fecha_resolucion?: string | null
}

export function createReport(body: { laboratorio_id: string; seccion_id?: string | null; descripcion: string; adjunto?: File }) {
  const form = new FormData()
  form.append("laboratorio_id", body.laboratorio_id)
  if (body.seccion_id) form.append("seccion_id", body.seccion_id)
  form.append("descripcion", body.descripcion)
  if (body.adjunto) form.append("adjunto", body.adjunto)
  return api<Reporte>("/reports/", { method: "POST", body: form })
}

export function myReports() {
  return api<Reporte[]>("/reports/me/")
}

export function listReports(params?: { estado?: EstadoReporte; laboratorio?: string }) {
  const qs = new URLSearchParams(params as Record<string, string>).toString()
  return api<Reporte[]>(`/reports/${qs ? `?${qs}` : ""}`)
}

export function updateReportStatus(id: string, estado: EstadoReporte) {
  return api<Reporte>(`/reports/${id}/`, { method: "PATCH", body: JSON.stringify({ estado }) })
}

// ---------------------------------------------------------------------------
// Notifications — /api/v1/notifications
// ---------------------------------------------------------------------------

export interface Notificacion {
  id: string
  tipo: string
  mensaje: string
  canal: string
  leida: boolean
  entidad_tipo: string
  entidad_id: string | null
  fecha_creacion: string
}

export function listNotifications(params?: { leida?: boolean }) {
  const qs = new URLSearchParams(params as unknown as Record<string, string>).toString()
  return api<Notificacion[]>(`/notifications/${qs ? `?${qs}` : ""}`)
}

export function markNotificationRead(id: string) {
  return api<Notificacion>(`/notifications/${id}/read/`, { method: "PATCH" })
}
