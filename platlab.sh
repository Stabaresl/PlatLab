#!/usr/bin/env bash
# Instala y administra PlatLAB en Linux o macOS (equivalente a platlab.ps1).
#
#   bash platlab.sh                       instala (o actualiza) con preguntas
#   bash platlab.sh instalar --modo red --admin-email profe@universidad.edu.co
#   bash platlab.sh iniciar | detener | estado | logs [servicio] | actualizar | desinstalar [--borrar-datos]
#
# Opciones: --modo local|red  --puerto N  --admin-email X  --admin-nombre X  --si (sin preguntas)
#
# Se puede volver a ejecutar sin miedo: no borra datos y sirve para actualizar.

set -euo pipefail
cd "$(dirname "$0")"

ACCION="instalar"
SERVICIO=""
MODO=""
PUERTO=""
ADMIN_EMAIL=""
ADMIN_NOMBRE="Administrador"
SIN_PREGUNTAS=0
BORRAR_DATOS=0

COMPOSE=(docker compose -f docker-compose.yml -f docker-compose.local.yml)
COMPOSE_MINIMO="2.24.4"   # `!reset` / `!override` en docker-compose.local.yml

# --- Salida ----------------------------------------------------------------

if [ -t 1 ]; then
  C_CYAN=$'\033[36m'; C_VERDE=$'\033[32m'; C_AMARILLO=$'\033[33m'; C_ROJO=$'\033[31m'; C_FIN=$'\033[0m'
else
  C_CYAN=""; C_VERDE=""; C_AMARILLO=""; C_ROJO=""; C_FIN=""
fi
titulo() { printf '\n%s== %s%s\n' "$C_CYAN" "$1" "$C_FIN"; }
ok()     { printf '  %s[ok]%s %s\n' "$C_VERDE" "$C_FIN" "$1"; }
info()   { printf '  %s\n' "$1"; }
aviso()  { printf '  %s[!] %s%s\n' "$C_AMARILLO" "$1" "$C_FIN"; }
fallar() { printf '\n  %s[x] %s%s\n' "$C_ROJO" "$1" "$C_FIN"; exit 1; }

preguntar_si_no() {  # $1 pregunta, $2 defecto (s|n)
  local defecto="${2:-s}" r sufijo="[S/n]"
  [ "$defecto" = "n" ] && sufijo="[s/N]"
  if [ "$SIN_PREGUNTAS" = 1 ]; then [ "$defecto" = "s" ]; return; fi
  read -r -p "  $1 $sufijo " r || r=""
  r="$(printf '%s' "$r" | tr '[:upper:]' '[:lower:]')"
  [ -z "$r" ] && r="$defecto"
  [ "$r" = "s" ] || [ "$r" = "si" ] || [ "$r" = "sí" ] || [ "$r" = "y" ]
}

# --- Argumentos ------------------------------------------------------------

if [ $# -gt 0 ] && [[ "$1" != --* ]]; then ACCION="$1"; shift; fi
if [ $# -gt 0 ] && [[ "$1" != --* ]]; then SERVICIO="$1"; shift; fi
while [ $# -gt 0 ]; do
  case "$1" in
    --modo) MODO="${2:-}"; shift 2 ;;
    --puerto) PUERTO="${2:-}"; shift 2 ;;
    --admin-email) ADMIN_EMAIL="${2:-}"; shift 2 ;;
    --admin-nombre) ADMIN_NOMBRE="${2:-}"; shift 2 ;;
    --si|--sin-preguntas) SIN_PREGUNTAS=1; shift ;;
    --borrar-datos) BORRAR_DATOS=1; shift ;;
    -h|--help|ayuda) sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) fallar "Opción desconocida: $1 (usa --help)" ;;
  esac
done
case "$ACCION" in
  instalar|iniciar|detener|estado|logs|actualizar|desinstalar) ;;
  ayuda) sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
  *) fallar "Acción desconocida: $ACCION (usa --help)" ;;
esac
if [ -n "$MODO" ] && [ "$MODO" != "local" ] && [ "$MODO" != "red" ]; then fallar "--modo debe ser local o red"; fi
if [ -n "$PUERTO" ] && ! [[ "$PUERTO" =~ ^[0-9]+$ ]]; then fallar "--puerto debe ser un número"; fi

# --- .env ------------------------------------------------------------------

secreto() {  # hex: sin caracteres que docker compose interprete en .env
  local bytes="${1:-32}"
  if command -v openssl >/dev/null 2>&1; then openssl rand -hex "$bytes"
  else head -c "$bytes" /dev/urandom | od -An -tx1 | tr -d ' \n'; fi
}

env_valor() {
  [ -f .env ] || return 0
  awk -F= -v k="$1" '$0 ~ "^[[:space:]]*"k"[[:space:]]*=" { sub(/^[^=]*=/, ""); gsub(/^[ \t]+|[ \t\r]+$/, ""); print; exit }' .env
}

env_poner() {  # reemplaza KEY=... (también si estaba comentada) o la agrega al final
  local clave="$1" valor="$2" tmp
  tmp="$(mktemp)"
  if [ -f .env ]; then
    awk -v k="$clave" -v v="$valor" '
      $0 ~ "^[[:space:]]*#?[[:space:]]*"k"[[:space:]]*=" { if (!hecho) { print k"="v; hecho=1 }; next }
      { print }
      END { if (!hecho) print k"="v }' .env > "$tmp"
  else
    printf '%s=%s\n' "$clave" "$valor" > "$tmp"
  fi
  cat "$tmp" > .env && rm -f "$tmp"
}

clave_debil() {
  local v="${1:-}"
  [ -z "$v" ] || [ "${#v}" -lt 40 ] || [[ "$v" =~ changeme|insecure|cambiar ]]
}

# --- Docker ----------------------------------------------------------------

con_reintentos() {  # con_reintentos "qué" comando args...
  # Descargar imágenes es lo único que depende de internet, y en redes de
  # aula los cortes momentáneos son comunes.
  local que="$1" i; shift
  for i in 1 2 3 4; do
    if "$@"; then return 0; fi
    [ "$i" -lt 4 ] || return 1
    aviso "$que falló (intento $i de 4), probablemente por la red. Reintento en 10 s..."
    sleep 10
  done
}

docker_activo() { docker info --format '{{.ServerVersion}}' >/dev/null 2>&1; }
id_contenedor() { { "${COMPOSE[@]}" ps -q "$1" 2>/dev/null || true; } | head -n1; }

version_ge() {  # version_ge 2.30.1 2.24.4
  [ "$(printf '%s\n%s\n' "$2" "$1" | sort -t. -k1,1n -k2,2n -k3,3n | head -n1)" = "$2" ]
}

ip_local() {
  local ip=""
  if command -v ip >/dev/null 2>&1; then
    ip="$(ip route get 1.1.1.1 2>/dev/null | awk '{for (i=1;i<NF;i++) if ($i=="src") {print $(i+1); exit}}')"
  fi
  if [ -z "$ip" ] && command -v ipconfig >/dev/null 2>&1; then   # macOS
    ip="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)"
  fi
  printf '%s' "$ip"
}

# --- Pasos -----------------------------------------------------------------

revisar_requisitos() {
  titulo "Revisando requisitos"
  command -v docker >/dev/null 2>&1 || fallar "No encontré Docker. Instálalo (https://docs.docker.com/engine/install/ en Linux, Docker Desktop en macOS) y vuelve a ejecutar."

  local v
  v="$(docker compose version --short 2>/dev/null || true)"
  [ -n "$v" ] || fallar 'Falta "docker compose" (v2). En Linux instala el paquete docker-compose-plugin.'
  v="${v#v}"; v="${v%%-*}"; v="${v%%+*}"
  version_ge "$v" "$COMPOSE_MINIMO" || fallar "Tu docker compose es $v y PlatLAB necesita $COMPOSE_MINIMO o superior."
  ok "docker compose $v"

  if ! docker_activo; then
    if docker info 2>&1 | grep -qi "permission denied"; then
      fallar "Tu usuario no tiene permiso para usar Docker. Ejecuta: sudo usermod -aG docker \$USER  (y cierra sesión), o corre este script con sudo."
    fi
    fallar "Docker no está corriendo. Arráncalo (Linux: sudo systemctl start docker · macOS: abre Docker Desktop) y vuelve a intentar."
  fi
  ok "Docker está corriendo"

  local mem
  mem="$(docker info --format '{{.MemTotal}}' 2>/dev/null || echo 0)"
  if [ "${mem:-0}" -gt 0 ] && [ "$mem" -lt $((6 * 1024 * 1024 * 1024)) ]; then
    aviso "Docker tiene $((mem / 1024 / 1024)) MB de RAM. Con menos de 6 GB los laboratorios pueden fallar con muchos estudiantes."
  fi
  command -v git >/dev/null 2>&1 || aviso 'No encontré git: todo funciona, pero "actualizar" no podrá descargar versiones nuevas.'
}

resolver_modo() {
  if [ -n "$MODO" ]; then return; fi
  local guardado; guardado="$(env_valor PLATLAB_MODO)"
  if [ "$SIN_PREGUNTAS" = 1 ]; then MODO="${guardado:-local}"; return; fi

  titulo "¿Cómo se va a usar PlatLAB?"
  info "[1] Solo en este computador: ideal para probar. Trae cuentas demo con contraseñas conocidas."
  info "[2] En red / aula: otros equipos entran por la IP de este. Las cuentas demo se desactivan"
  info "    y creas tu propia cuenta de administrador."
  local defecto=1 r
  [ "$guardado" = "red" ] && defecto=2
  while true; do
    read -r -p "  Elige 1 o 2 [$defecto] " r || r=""
    r="${r:-$defecto}"
    case "$r" in 1) MODO=local; return ;; 2) MODO=red; return ;; esac
  done
}

resolver_puerto() {
  if [ -n "$PUERTO" ]; then return; fi
  local guardado; guardado="$(env_valor PLATLAB_PORT)"
  if [[ "$guardado" =~ ^[0-9]+$ ]]; then PUERTO="$guardado"; else PUERTO=8080; fi
}

revisar_puerto_libre() {
  [ -n "$(id_contenedor gateway)" ] && return 0   # ya es nuestro
  local ocupado=""
  if command -v ss >/dev/null 2>&1; then ocupado="$(ss -ltnH "sport = :$PUERTO" 2>/dev/null || true)"
  elif command -v lsof >/dev/null 2>&1; then ocupado="$(lsof -nP -iTCP:"$PUERTO" -sTCP:LISTEN 2>/dev/null || true)"; fi
  [ -z "$ocupado" ] || fallar "El puerto $PUERTO ya lo usa otro programa. Usa otro: bash platlab.sh instalar --puerto 8090"
}

preparar_env() {
  titulo "Preparando la configuración (.env)"
  if [ ! -f .env ]; then
    cp .env.example .env
    env_poner SECRET_KEY "$(secreto 32)"
    env_poner FLAG_HASH_KEY "$(secreto 32)"
    env_poner POSTGRES_PASSWORD "$(secreto 24)"
    env_poner DEBUG False
    env_poner DJANGO_ADMIN_URL "panel-$(secreto 6)/"
    chmod 600 .env
    ok ".env creado con claves aleatorias nuevas"
  else
    local copia; copia=".env.respaldo-$(date +%Y%m%d-%H%M%S)"
    cp .env "$copia" && chmod 600 "$copia"
    ok "Usando el .env existente (respaldo en $copia)"
    local secret; secret="$(env_valor SECRET_KEY)"
    if clave_debil "$secret"; then
      # Las flags y respuestas de examen guardadas se firmaron con la
      # SECRET_KEY vieja: se conserva como FLAG_HASH_KEY para que sigan
      # validando después de rotarla.
      if [ -z "$(env_valor FLAG_HASH_KEY)" ] && [ -n "$secret" ]; then env_poner FLAG_HASH_KEY "$secret"; fi
      env_poner SECRET_KEY "$(secreto 32)"
      ok "SECRET_KEY era débil: la cambié por una aleatoria (las sesiones abiertas se cierran)"
    fi
    if [ "$(env_valor POSTGRES_PASSWORD)" = "changeme" ]; then
      aviso 'POSTGRES_PASSWORD sigue en "changeme". No la cambio porque la base ya existe con esa clave (no está expuesta fuera de Docker).'
    fi
  fi
  env_poner PLATLAB_MODO "$MODO"
  env_poner PLATLAB_PORT "$PUERTO"
  if [ "$MODO" = "red" ]; then env_poner PLATLAB_BIND 0.0.0.0; else env_poner PLATLAB_BIND 127.0.0.1; fi
}

construir_imagenes_laboratorio() {
  titulo "Construyendo las imágenes de los laboratorios"
  local dir tag
  for dir in docker/targets/*/; do
    [ -f "$dir/IMAGE" ] || continue
    tag="$(tr -d ' \r\n' < "$dir/IMAGE")"
    info "$tag  <-  $dir"
    con_reintentos "La imagen $tag" docker build --quiet -t "$tag" "$dir" >/dev/null || fallar "No se pudo construir $tag."
    ok "$tag"
  done
}

levantar() {
  if [ "${1:-}" = "--construir" ]; then
    titulo "Construyendo y levantando PlatLAB (la primera vez tarda varios minutos)"
    con_reintentos "La construcción" "${COMPOSE[@]}" up -d --build --remove-orphans || fallar "No se pudo construir PlatLAB (revisa tu conexión a internet)."
  else
    titulo "Levantando PlatLAB"
    "${COMPOSE[@]}" up -d --remove-orphans
  fi
}

esperar() {
  info "Esperando a que el backend termine de arrancar (migraciones incluidas)..."
  local limite=$((SECONDS + 360)) id salud
  while true; do
    id="$(id_contenedor web)"
    if [ -n "$id" ]; then
      salud="$(docker inspect -f '{{.State.Health.Status}}' "$id" 2>/dev/null || true)"
      [ "$salud" = "healthy" ] && break
    fi
    [ $SECONDS -lt $limite ] || fallar "El backend no arrancó a tiempo. Revisa: bash platlab.sh logs web"
    sleep 3
  done
  limite=$((SECONDS + 120))
  until curl -fsS -o /dev/null "http://127.0.0.1:$PUERTO/api/v1/health/" 2>/dev/null; do
    [ $SECONDS -lt $limite ] || fallar "El backend está arriba pero la interfaz web no responde. Revisa: bash platlab.sh logs gateway"
    sleep 2
  done
  ok "PlatLAB responde"
}

semillas() {
  titulo "Cargando laboratorios, mapa de aprendizaje y catálogo de logros"
  local c
  # actualizar_contenido_labs va después de los seeds: guías paso a paso, consola realista y examen.
  for c in seed_demo_data seed_roadmap_labs seed_labs_expansion seed_gamification_catalog actualizar_contenido_labs; do
    info "$c"
    "${COMPOSE[@]}" exec -T web python manage.py "$c" >/dev/null
  done
  ok "Contenido cargado"

  if [ "$MODO" != "red" ]; then
    # Si antes se instaló en modo red/aula, las cuentas demo quedaron deshabilitadas.
    "${COMPOSE[@]}" exec -T web python manage.py seed_demo_data --activar-cuentas-demo >/dev/null
    "${COMPOSE[@]}" exec -T web python manage.py seed_sala_demo >/dev/null
    ok "Cuentas demo activas y sala demo lista (código PRUEBA)"
  fi

  if [ "$MODO" = "red" ]; then
    "${COMPOSE[@]}" exec -T web python manage.py seed_demo_data --desactivar-cuentas-demo >/dev/null
    ok "Cuentas demo desactivadas (sus contraseñas son públicas en el repositorio)"
    crear_admin
  fi
}

crear_admin() {
  local email="$ADMIN_EMAIL" nombre="$ADMIN_NOMBRE" n
  if [ -z "$email" ]; then
    if [ "$SIN_PREGUNTAS" = 1 ]; then
      aviso "Sin --admin-email no creo administrador. Créalo luego con: bash platlab.sh instalar --admin-email tu@correo"
      return
    fi
    titulo "Cuenta de administrador"
    while true; do
      read -r -p "  Correo del administrador: " email || email=""
      [[ "$email" =~ ^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$ ]] && break
      aviso "Ese correo no parece válido."
    done
    read -r -p "  Nombre completo [$nombre]: " n || n=""
    [ -n "$n" ] && nombre="$n"
  fi
  # La contraseña la genera el comando y la muestra UNA vez.
  "${COMPOSE[@]}" exec -T web python manage.py create_production_users --admin-email "$email" --admin-nombre "$nombre"
}

firewall() {
  if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q "Status: active"; then
    aviso "ufw está activo. Si otros equipos no logran entrar: sudo ufw allow $PUERTO/tcp"
  fi
  if command -v firewall-cmd >/dev/null 2>&1 && firewall-cmd --state >/dev/null 2>&1; then
    aviso "firewalld está activo. Si otros equipos no logran entrar: sudo firewall-cmd --add-port=$PUERTO/tcp --permanent && sudo firewall-cmd --reload"
  fi
}

resumen() {
  local ip panel
  printf '\n  %s==============================================================%s\n' "$C_VERDE" "$C_FIN"
  printf '  %s PlatLAB está listo%s\n' "$C_VERDE" "$C_FIN"
  printf '  %s==============================================================%s\n' "$C_VERDE" "$C_FIN"
  info "En este computador:   http://localhost:$PUERTO"
  if [ "$(env_valor PLATLAB_MODO)" = "red" ]; then
    ip="$(ip_local)"
    info "Desde otros equipos:  http://${ip:-<IP-de-este-equipo>}:$PUERTO"
  else
    info ""
    info "Cuentas demo (solo accesibles desde este computador):"
    info "  administrador  admin@platlab.demo        Admin1234"
    info "  instructor     instructor@platlab.demo   Instructor1234"
    info "  estudiante     estudiante@platlab.demo   Estudiante1234"
    info "Sala de prueba: entra como estudiante a Salas y usa el código PRUEBA."
  fi
  panel="$(env_valor DJANGO_ADMIN_URL)"
  [ -n "$panel" ] && info "Admin de Django:      http://localhost:$PUERTO/$panel"
  info ""
  info "Para el día a día:  bash platlab.sh iniciar | detener | estado | logs | actualizar"
}

instalar() {
  revisar_requisitos
  resolver_modo
  resolver_puerto
  revisar_puerto_libre
  preparar_env
  construir_imagenes_laboratorio
  levantar --construir
  esperar
  semillas
  [ "$MODO" = "red" ] && firewall
  resumen
  if [ "$SIN_PREGUNTAS" != 1 ] && preguntar_si_no "¿Abrir PlatLAB en el navegador ahora?" s; then
    if command -v xdg-open >/dev/null 2>&1; then xdg-open "http://localhost:$PUERTO" >/dev/null 2>&1 || true
    elif command -v open >/dev/null 2>&1; then open "http://localhost:$PUERTO" || true; fi
  fi
}

desinstalar() {
  docker_activo || fallar "Docker no está corriendo."
  if [ "$BORRAR_DATOS" = 1 ]; then
    aviso "Esto borra TODOS los datos de PlatLAB: usuarios, progreso, archivos subidos."
    if [ "$SIN_PREGUNTAS" != 1 ]; then
      local r; read -r -p "  Escribe BORRAR para confirmar: " r || r=""
      [ "$r" = "BORRAR" ] || { info "Cancelado."; return; }
    fi
    "${COMPOSE[@]}" down --remove-orphans --volumes
  else
    "${COMPOSE[@]}" down --remove-orphans
  fi
  local labs; labs="$(docker ps -aq --filter 'label=platlab.lab-environment=true')"
  # shellcheck disable=SC2086
  [ -n "$labs" ] && docker rm -f $labs >/dev/null
  ok "PlatLAB detenido y contenedores eliminados."
  [ "$BORRAR_DATOS" = 1 ] || info "Los datos se conservan. Para borrarlos también: bash platlab.sh desinstalar --borrar-datos"
}

case "$ACCION" in
  instalar) instalar ;;
  actualizar)
    if command -v git >/dev/null 2>&1 && [ -d .git ]; then
      titulo "Descargando la última versión"
      git pull --ff-only || fallar "git pull falló (¿cambios locales sin guardar?). Resuélvelo y vuelve a intentar."
    fi
    SIN_PREGUNTAS=1
    instalar
    ;;
  iniciar) revisar_requisitos; resolver_puerto; levantar; esperar; resumen ;;
  detener) "${COMPOSE[@]}" stop; ok "PlatLAB detenido. Para volver: bash platlab.sh iniciar" ;;
  estado) "${COMPOSE[@]}" ps ;;
  logs) if [ -n "$SERVICIO" ]; then "${COMPOSE[@]}" logs -f --tail 200 "$SERVICIO"; else "${COMPOSE[@]}" logs -f --tail 50; fi ;;
  desinstalar) desinstalar ;;
esac
