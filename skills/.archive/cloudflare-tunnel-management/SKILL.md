---
name: cloudflare-tunnel-management
description: Diagnose Cloudflare Tunnel 530/1016 and www redirects.
---

# Cloudflare Tunnel Management

Gestión de sitios expuestos vía Cloudflare Tunnel (managed by token) con Dokploy detrás. Cubre diagnóstico de hostnames caídos, publicación de subdominios y canonicalización www → apex.

## Cuándo usar
- Un subdominio responde 530 / error 1016 ("Origin DNS error") pero el apex funciona.
- Hay que publicar un hostname nuevo en el túnel (app.migbertweb.xyz, etc.).
- Decidir cómo manejar www vs no-www (canonicalización SEO).
- Auditar qué dominio sirve qué y desde qué servidor.

## Arquitectura típica (migbertweb)
- **VPS hetzner (37.27.243.58)**: Dokploy (traefik en 80/443) + contenedor cloudflared. Este es el ORIGIN del portfolio.
- **serverhogar (192.168.1.8)**: NO corre Dokploy (solo filebrowser) — no buscar el origin ahí.
- El túnel es **managed by token**: `TUNNEL_TOKEN` en env del contenedor cloudflared; la config (public hostnames) vive SOLO en el dashboard Cloudflare Zero Trust — no hay config.yml local.
- El contenedor cloudflared es **distroless**: no tiene `cat`/shell — no intentar `docker exec ... cat`.

## Diagnóstico (en orden)
1. `dig +short dominio A` — IPs 172.67.x / 104.21.x = registro proxied (orange cloud). Son IPs del edge de Cloudflare, NO del origin.
2. `curl -sI https://dominio` — status: 200 OK vs 530 (error de edge).
3. Cuerpo: `curl -s https://dominio` — "error code: 1016" = Origin DNS error.
4. Confirmar túnel en el VPS: `docker ps | grep cloudflared`; `docker inspect <cid> --format '{{.Config.Cmd}}'` → `tunnel run` + env TUNNEL_TOKEN.
5. `curl https://dominio/cdn-cgi/trace` — confirma que pasa por Cloudflare.

## Error 1016 / 530 — causa raíz
Cloudflare no puede resolver el **origin** del hostname. Con túnel, cada hostname debe estar **publicado en el túnel** (Zero Trust → Tunnels → Public Hostnames); Cloudflare crea el CNAME `<tunnel-id>.cfargotunnel.com` automáticamente. Si el subdominio tiene un registro A suelto proxied (p. ej. copiado del apex), Cloudflare intenta resolver un origin que no existe → 1016.

## Fix recomendado para www (SEO)
www debe **301 a no-www** (canonical ya apunta a no-www; servir duplicado = contenido duplicado).
1. Dashboard Cloudflare → dominio → **Rules → Redirect Rules → Create rule**
2. When: Hostname equals `www.dominio.com`
3. Then: Dynamic → `concat("https://dominio.com", http.request.uri.path)` (preservar query string)
4. Status code **301** → Deploy

La rule se evalúa en el edge ANTES de resolver origin → www nunca toca el túnel → el 1016 desaparece sin tocar el túnel ni el DNS.

## Fix alternativo (si www debe servir contenido)
1. Zero Trust → Tunnels → [túnel] → Public Hostnames → Add: hostname www + el MISMO Service que el apex.
2. Borrar el registro A suelto de www en DNS.
3. ⚠️ Crea contenido duplicado → igual necesitas 301 en traefik. Preferir el Redirect Rule.

## Pitfalls
- **Verificar content-type, no solo status**: en una SPA (fallback de Vite), un archivo faltante (robots.txt, sitemap.xml, og-image.png) devuelve **200 text/html** — peor que 404 para crawlers. Usar `curl -s -o /dev/null -w '%{http_code} %{content_type}'`.
- No buscar config del túnel en el servidor (managed by token → config remota en dashboard).
- `dig` mostrando IPs de Cloudflare NO significa que el registro esté sano — solo que está proxied.

## Referencias
- `references/migbertweb-infra.md` — topología real del portfolio: VPS, DNS, errores observados y estado del SEO aplicado.
