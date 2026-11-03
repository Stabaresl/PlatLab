# Gateway de PlatLAB para la instalación local / aula (docker-compose.local.yml):
# compila la SPA y la sirve con Caddy, que además hace de reverse proxy hacia
# el backend. Así todo entra por UN solo puerto (PLATLAB_PORT, 8080 por
# defecto): sin Node/Bun en la máquina de quien instala y sin CORS.

FROM oven/bun:1.3.14 AS build
WORKDIR /app
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile
COPY . .
# Sin VITE_API_URL: el build de producción usa rutas relativas (/api/v1) y
# el WebSocket se arma desde window.location (ver src/pages/api.ts) — la
# misma imagen sirve para localhost y para la IP de la red local.
ARG VITE_OAUTH_ENABLED=false
ENV VITE_OAUTH_ENABLED=${VITE_OAUTH_ENABLED}
RUN bun run build

FROM caddy:2.8.4-alpine
COPY docker/Caddyfile /etc/caddy/Caddyfile
COPY --from=build /app/dist /srv/app
