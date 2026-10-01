# Infra migbertweb.xyz — estado observado (ago 2026)

Topología real verificada en sesión de auditoría SEO + fix de www (issue #12, PR #13).

## Servidores / origin
- **hetzner (37.27.243.58, hostname `dokploy1`)**: corre Dokploy completo — `dokploy.1.*` (3000), `dokploy-traefik` (80/443), `dokploy-postgres`, `dokploy-redis`, y el túnel `seguritynetworkservices-dokploycloudflared-*` (imagen `cloudflare/cloudflared:latest`, CMD `tunnel run`, env `TUNNEL_TOKEN=eyJh...`). **Es el origin del portfolio.**
- **worker1 (204.216.146.246)**, **worker2 (164.152.193.65)**, **gcpvps (34.187.251.169)**: tienen `dokploy-traefik` pero cloudflared NO fue detectado ahí (sin `docker ps` con cloudflared) — probar con `docker ps | grep cloudflared` antes de asumir.
- **serverhogar (192.168.1.8)**: NO corre Dokploy; solo `filebrowser-filebrowser-1` (8081). No buscar el origin del portfolio ahí.

## DNS (Cloudflare, proxied — orange cloud)
- NS: `may.ns.cloudflare.com` / `robert.ns.cloudflare.com`.
- `migbertweb.xyz` A → 172.67.202.156 / 104.21.34.93 (proxied, OK).
- `www.migbertweb.xyz` A → mismas IPs proxied pero **530 / error code 1016** ("Origin DNS error") — hostname NO publicado en el túnel; registro A suelto sin origin.
- `http://migbertweb.xyz` → 301 → `https://migbertweb.xyz/` (correcto).
- Detección Cloudflare: `curl -s https://migbertweb.xyz/cdn-cgi/trace` → `fl=...`, `colo=MIA`, `visit_scheme=https`.

## Túnel
- Managed by token (`TUNNEL_TOKEN`), config de public hostnames SOLO en dashboard Cloudflare Zero Trust.
- Contenedor distroless: `docker exec ... cat /etc/cloudflared/config.yml` falla ("executable file not found") — no hay config local. Usar `docker inspect` para CMD/ENV.

## Fix aplicado para www (dashboard Cloudflare, pendiente de aplicar por el usuario)
Redirect Rule: hostname equals `www.migbertweb.xyz` → dynamic `concat("https://migbertweb.xyz", http.request.uri.path)` → 301.

## SEO ya aplicado al repo portfolio-react (PR #13, mergeado)
- `public/robots.txt` — allow all + Sitemap ref.
- `public/sitemap.xml` — migbertweb.xyz + workapp.migbertweb.xyz.
- `public/favicon/og-image.png` — 1200x630, PIL, gradiente cyan `#00f3ff` → purple `#bc13fe` sobre `#0a0a0a`.
- `index.html` — JSON-LD `@graph` (Person + Service + WebSite), og:image:width/height, og:locale alternates (pt_BR/es_ES/en_US), twitter:image, meta robots, preconnect + carga real de Outfit (antes declarada en CSS pero nunca cargada).
- `src/App.tsx` — `document.documentElement.lang` sincronizado con locale (pt-BR/es/en).
- Verificación post-deploy: robots.txt → `200 text/plain`; sitemap.xml → `200 text/xml`; og-image.png → `200 image/png` (37 KB); JSON-LD parsea OK.

## Verificación de contenido (SPA fallback gotcha)
En el portfolio (Vite SPA), rutas inexistentes devuelven `200 text/html` (el index.html). Por eso robots.txt/sitemap.xml/og-image.png ausentes NO daban 404 sino 200 HTML — siempre chequear `content_type`, no solo status: `curl -s -o /dev/null -w '%{http_code} %{content_type}'`.

## Pendientes
- www → 301: aplicar Redirect Rule en Cloudflare (el usuario tiene acceso al dashboard).
- Core Web Vitals: PSI API sin quota (límite diario del proyecto compartido, project_number 583797351490) — reintentar otro día o con API key propia.
- Chunk JS ~529 KB (~165 KB gzip) — candidate a code-splitting por ruta si LCP falla.
