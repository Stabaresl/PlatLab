// Cliente HTTP para la API real de PlatLAB (Django/DRF, `/api/v1`).
// Reemplaza el mock (Bun/Express en :3001) de la rama mik4ela.

const BASE = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000/api/v1"
// El WebSocket de la terminal (lab_environments) vive fuera de /api/v1,
// en la raíz ASGI (config/asgi.py) — mismo host, protocolo ws(s) en vez de http(s).
const WS_BASE = BASE.replace(/^http/, "ws").replace(/\/api\/v1\/?$/, "")
// `default_storage.url()` (Django) devuelve una ruta relativa ("/media/...")
// pensada para un backend que sirve las vistas Y los archivos desde el mismo
// origen — acá el frontend (Vite) vive en otro origen, así que un <a href>
// con esa ruta tal cual navega dentro de la SPA en vez de descargar el
// archivo, y el catch-all del router termina mandando a "/". Hay que
// resolverla contra el origen real del backend.
const MEDIA_ORIGIN = BASE.replace(/\/api\/v1\/?$/, "")

export function resolveMediaUrl(url: string): string {
  if (/^https?:\/\//.test(url)) return url
  return `${MEDIA_ORIGIN}${url.startsWith("/") ? "" : "/"}${url}`
}

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
export type EstadoLaboratorio = "borrador" | "en_revision" | "publicado"
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
  motivo_rechazo: string | null
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
    secciones: { id: string; orden: number; titulo: string; tiene_practica: boolean; duracion_estimada_minutos: number }[]
  }>(`/laboratories/${id}/toc/`)
}

interface LaboratorioResult {
  id: string
  nombre: string
  estado: EstadoLaboratorio
  tipo: TipoLaboratorio
  visible_en_catalogo: boolean
}

export function createLaboratorio(body: {
  nombre: string
  descripcion: string
  nivel_dificultad: NivelDificultad
  temas?: string[]
  resumen_cierre?: string
}) {
  return api<LaboratorioResult>("/laboratories/", {
    method: "POST",
    body: JSON.stringify(body),
  })
}

export function updateLaboratorio(id: string, body: Partial<{
  nombre: string
  descripcion: string
  nivel_dificultad: NivelDificultad
  temas: string[]
  resumen_cierre: string
}>) {
  return api<LaboratorioResult>(`/laboratories/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(body),
  })
}

export function publishLaboratorio(id: string) {
  return api<LaboratorioResult>(`/laboratories/${id}/publish/`, { method: "POST" })
}

export function duplicateLaboratorio(id: string) {
  return api<LaboratorioResult>(`/laboratories/${id}/duplicate/`, { method: "POST" })
}

export function submitLabForReview(id: string) {
  return api<LaboratorioResult>(`/laboratories/${id}/submit-review/`, { method: "POST" })
}

export function approveLab(id: string) {
  return api<LaboratorioResult>(`/laboratories/${id}/approve/`, { method: "POST" })
}

export function rejectLab(id: string, motivo: string) {
  return api<LaboratorioResult>(`/laboratories/${id}/reject/`, {
    method: "POST",
    body: JSON.stringify({ motivo }),
  })
}

export interface LaboratorioEnRevisionItem {
  id: string
  nombre: string
  instructor_id: string | null
  updated_at: string | null
}

export function listReviewQueue() {
  return api<LaboratorioEnRevisionItem[]>("/laboratories/review-queue/")
}

// Opt-in de un laboratorio personalizado (ya publicado) al catálogo público
// — activado por su instructor dueño o por un admin. Sin esto, un
// personalizado solo se asigna por invitación directa (`inviteStudents`).
export function setCatalogVisibility(id: string, visible: boolean) {
  return api<LaboratorioResult>(`/laboratories/${id}/catalog-visibility/`, {
    method: "PATCH",
    body: JSON.stringify({ visible }),
  })
}

export interface LaboratorioPersonalizadoPublicadoItem {
  id: string
  nombre: string
  instructor_id: string | null
  visible_en_catalogo: boolean
}

// Admin-only: todos los personalizado+publicado de cualquier instructor,
// para gestionar su visibilidad de catálogo (no solo la propia).
export function listPublishedCustomLabs() {
  return api<LaboratorioPersonalizadoPublicadoItem[]>("/laboratories/published-custom/")
}

export interface PasoGuiaInput {
  orden: number
  titulo: string
  instrucciones: string
  comando_sugerido?: string | null
}

interface SeccionBody {
  titulo: string
  contenido_teorico: string
  orden: number
  tiene_practica?: boolean
  objetivos?: string[]
  duracion_estimada_minutos?: number
  pasos_guia?: PasoGuiaInput[]
  entorno_practica?: EntornoPractica | null
  imagen_practica?: string | null
}

interface SeccionResult {
  id: string
  laboratorio_id: string
  orden: number
  titulo: string
  tiene_practica: boolean
}

export function createSeccion(laboratorioId: string, body: SeccionBody) {
  return api<SeccionResult>(`/laboratories/${laboratorioId}/sections/`, {
    method: "POST",
    body: JSON.stringify(body),
  })
}

export function updateSeccion(laboratorioId: string, seccionId: string, body: Partial<SeccionBody>) {
  return api<SeccionResult>(`/laboratories/${laboratorioId}/sections/${seccionId}/`, {
    method: "PATCH",
    body: JSON.stringify(body),
  })
}

export function uploadDockerfile(laboratorioId: string, seccionId: string, archivo: File) {
  const formData = new FormData()
  formData.append("archivo", archivo)
  return api<{ id: string; seccion_id: string; archivo_url: string; nombre_archivo: string; tamano_kb: number }>(
    `/laboratories/${laboratorioId}/sections/${seccionId}/dockerfile/`,
    { method: "POST", body: formData },
  )
}

export interface ContenidoSeccionPreview {
  seccion_id: string
  titulo: string
  contenido_teorico: string
  tiene_practica: boolean
  objetivos: string[]
  duracion_estimada_minutos: number
  pasos_guia: PasoGuia[]
  entorno_practica: EntornoPractica | null
  tiene_dockerfile: boolean
  dockerfile_url: string | null
}

export function getSeccionPreview(laboratorioId: string, seccionId: string) {
  return api<ContenidoSeccionPreview>(`/laboratories/${laboratorioId}/sections/${seccionId}/preview/`)
}

export function checkFlagPreview(laboratorioId: string, seccionId: string, valor: string) {
  return api<{ correcto: boolean }>(
    `/laboratories/${laboratorioId}/sections/${seccionId}/preview/check-flag/`,
    { method: "POST", body: JSON.stringify({ valor }) },
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

// Autoinscripción directa desde el catálogo (sin invitación de instructor) —
// solo válida para laboratorios predeterminado+publicado; el backend bloquea
// con 422 si el estudiante ya tiene otro laboratorio vigente sin terminar.
export function enrollLaboratorio(laboratorioId: string) {
  return api<{ id: string; laboratorio_id: string; estado: EstadoAsignacion }>(
    "/assignments/enroll/",
    { method: "POST", body: JSON.stringify({ laboratorio_id: laboratorioId }) },
  )
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
  tipo: TipoLaboratorio
  visible_en_catalogo: boolean
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

export interface SolicitudInstructor {
  id: string
  estado: "pendiente" | "aprobada" | "rechazada"
  orcid: string
  motivo_rechazo: string | null
  created_at: string | null
}

export function solicitarConvertirseEnInstructor(body: {
  orcid: string
  tipo: string
  institucion?: string
  especialidades?: string
  motivacion?: string
}) {
  return api<SolicitudInstructor>("/users/instructor-requests/", {
    method: "POST",
    body: JSON.stringify(body),
  })
}

export function getMiSolicitudInstructor() {
  return api<SolicitudInstructor | undefined>("/users/instructor-requests/mine/")
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

export interface SeccionProgreso {
  id: string
  orden: number
  titulo: string
  tiene_practica: boolean
  estado: "bloqueada" | "en_progreso" | "completada"
}

export interface ProgresoOverview {
  asignacion_id: string
  laboratorio_id: string
  laboratorio_nombre: string
  secciones_completas: boolean
  examen_disponible: boolean
  intentos_examen: number
  vencido: boolean
  fecha_vencimiento: string | null
  resumen_cierre: string | null
  secciones: SeccionProgreso[]
}

export function getProgresoOverview(assignmentId: string) {
  return api<ProgresoOverview>(`/progress/${assignmentId}/`)
}

export interface ComandoSimulado {
  comando: string
  salida: string
}

export interface EntornoPractica {
  prompt: string
  banner: string
  comandos: ComandoSimulado[]
}

export interface PasoGuia {
  orden: number
  titulo: string
  instrucciones: string
  comando_sugerido: string | null
}

export interface ContenidoSeccion {
  seccion_id: string
  titulo: string
  contenido_teorico: string
  tiene_practica: boolean
  estado: string
  objetivos: string[]
  duracion_estimada_minutos: number
  pasos_guia: PasoGuia[]
  entorno_practica: EntornoPractica | null
  entorno_real_disponible: boolean
}

export function getSectionContent(assignmentId: string, sectionId: string) {
  return api<ContenidoSeccion>(`/progress/${assignmentId}/sections/${sectionId}/`)
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

// Única forma de avanzar una sección sin práctica (tiene_practica=false,
// ej. una introducción teórica): no tiene flag que validar, así que no
// pasa por submitFlag — sin esto el laboratorio quedaba trabado ahí.
export function completeTheorySection(assignmentId: string, sectionId: string) {
  return api<{ correcto: boolean; seccion_desbloqueada: string | null }>(
    `/progress/${assignmentId}/sections/${sectionId}/complete/`,
    { method: "POST" },
  )
}

// ---------------------------------------------------------------------------
// lab_environments — entorno de práctica REAL (contenedor Docker
// descartable por estudiante, terminal vía WebSocket). Distinto de la
// consola simulada (`entorno_practica`, siempre disponible sin infra) —
// solo existe si la sección tiene `entorno_real_disponible=true`.
// ---------------------------------------------------------------------------

export interface EntornoRealEstado {
  activo: boolean
  id?: string
  estado?: "iniciando" | "activo" | "detenido" | "error"
  idle_timeout_minutos?: number
  max_lifetime_minutos?: number
}

export function startLabEnvironment(assignmentId: string, sectionId: string) {
  return api<Required<Omit<EntornoRealEstado, "activo">>>(
    `/lab-environments/${assignmentId}/sections/${sectionId}/start/`,
    { method: "POST" },
  )
}

export function stopLabEnvironment(entornoId: string) {
  return api<{ detenido: boolean }>(`/lab-environments/${entornoId}/stop/`, { method: "POST" })
}

export function getLabEnvironmentStatus(assignmentId: string, sectionId: string) {
  return api<EntornoRealEstado>(`/lab-environments/${assignmentId}/sections/${sectionId}/status/`)
}

export function labEnvironmentTerminalUrl(entornoId: string): string {
  const token = getAccessToken()
  return `${WS_BASE}/ws/lab-environments/${entornoId}/terminal/?token=${encodeURIComponent(token || "")}`
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

export interface PreguntaExamen {
  id: string
  enunciado: string
  tipo: "opcion_multiple" | "abierta"
  opciones: string[] | null
}

export function getExamen(assignmentId: string) {
  return api<{ examen_id: string; preguntas: PreguntaExamen[] }>(`/progress/${assignmentId}/exam/`)
}

export function submitExam(assignmentId: string, respuestas: Record<string, string>) {
  return api<{ puntaje: number; correctas: number; total: number; numero_intento: number }>(
    `/progress/${assignmentId}/exam/`,
    { method: "POST", body: JSON.stringify({ respuestas }) },
  )
}

export function getHistory(assignmentId: string) {
  return api<{ numero_intento: number; fecha_completado: string; puntaje: number | null }[]>(
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
