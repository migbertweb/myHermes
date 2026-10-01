---
name: seo-webs
description: Use when the user asks to audit or optimize website SEO.
---

# SEO para webs

Optimización de sitios web para buscadores (Google principalmente). Cubre auditoría, keywords, on-page, SEO técnico, datos estructurados y medición.

## Cuándo usar
- El usuario pide "hacer SEO", "auditoría SEO", "optimizar la web para Google" o "subir en rankings".
- Antes de lanzar o rediseñar una web (porfolio, landing, e-commerce, blog).
- Cuando una web no indexa bien, tiene poco tráfico orgánico o Core Web Vitals malos.

## Flujo de trabajo
1. **Auditoría técnica base** — verificar indexación, rastreo y velocidad.
2. **Keyword research** — identificar términos con intención y volumen viable.
3. **Optimización on-page** — títulos, metas, headings, contenido, URLs, imágenes.
4. **SEO técnico** — sitemap, robots.txt, canonical, structured data, Core Web Vitals.
5. **Off-page** — backlinks, citaciones, señales locales (si aplica).
6. **Medición** — Google Search Console + Analytics, seguimiento semanal.

## Auditoría técnica (paso 1)
```bash
# Chequeo rápido de indexación y cabeceras
curl -sI https://dominio.com                          # status 200, x-robots-tag
curl -s https://dominio.com/robots.txt                # permisos de rastreo
curl -s https://dominio.com/sitemap.xml | head -50    # URLs incluidas
# Verificar www vs no-www y http vs https: deben redirigir (301) a UNA sola versión
```
- `x-robots-tag: noindex` en la home = problema grave.
- Bloqueo accidental en robots.txt (Disallow: /) = sitio fuera del índice.
- Sitemap debe listar solo URLs canónicas (200), sin parámetros, sin duplicados.
- **Google Search Console**: pedir indexación de URLs nuevas vía URL Inspection; revisar Cobertura y Page Experience.

## Keywords (paso 2)
- **Intención > volumen**: informacional (blog), transaccional (producto/servicio), navegacional (marca).
- Long-tail: 3+ palabras, menos competencia, conversión más alta.
- Una keyword principal por página + 2-3 secundarias relacionadas (sin canibalizar: nunca dos páginas atacando la misma keyword principal).
- Herramientas gratis: Google Keyword Planner (requiere cuenta Ads), Search Console (queries reales que ya posicionan), sugerencias de autocompletado de Google, "People also ask".

## On-page (paso 3)
- **Title** (50-60 chars): keyword principal al inicio, marca al final. Único por página.
- **Meta description** (140-160 chars): gancho + CTA, incluye keyword. No afecta ranking directo, sí CTR.
- **H1 único** por página con la keyword principal; jerarquía H2/H3 lógica.
- **Contenido**: cubrir la intención completa, sin relleno. 1 keyword por párrafo máximo, variaciones naturales.
- **URLs**: cortas, descriptivas, con keyword, minúsculas, guiones no underscores. Ej: `/servicios/diseno-web` no `/pagina?id=42`.
- **Imágenes**: nombre de archivo descriptivo, `alt` con la keyword cuando sea natural (no keyword stuffing en cada imagen), formato WebP/AVIF.
- **Links internos**: anclar con texto descriptivo ("guía de Core Web Vitals"), 3-10 por página, jerarquía: páginas importantes reciben más enlaces.

## SEO técnico (paso 4)
- **Canonical**: `<link rel="canonical" href="...">` en cada página apuntando a su versión definitiva. Crítico en React/SPA con rutas duplicadas o params de tracking.
- **Datos estructurados JSON-LD** (no microdata):
```json
{
  "@context": "https://schema.org",
  "@type": "Service",
  "name": "Desarrollo Web FullStack",
  "provider": { "@type": "Person", "name": "Migbert" },
  "areaServed": "Brasil",
  "url": "https://migbertweb.xyz"
}
```
  - Tipos útiles: `Service`, `Person`, `Organization`, `Article`, `BreadcrumbList`, `FAQPage` (solo si hay FAQ reales en la página), `Product` (e-commerce).
  - Validar en [validator.schema.org](https://validator.schema.org) o Rich Results Test de Google.
- **Core Web Vitals** (métricas reales de Google):
  - LCP < 2.5s (carga del contenido principal).
  - INP < 200ms (interactividad — reemplazó a FID).
  - CLS < 0.1 (estabilidad visual).
  - Medir: PageSpeed Insights (lab + campo), Search Console > Core Web Vitals (campo real).
- **SPA/React (Vite)**: prerender/SSR o metadata dinámica para que Google vea titles/metas; preconnect a fuentes y APIs; code-splitting por ruta.
- **Mobile-first**: viewport correcto, texto legible sin zoom, botones ≥ 48px.
- **HTTPS** obligatorio; evitar mixed content (http dentro de https).

## Off-page (paso 5)
- Backlinks de calidad > cantidad: directorios del sector, guest posts, perfiles de negocio (Google Business Profile para local).
- Señales locales: NAP (Nombre-Address-Phone) consistente en todas las plataformas, reseñas en Google Maps.
- No comprar backlinks ni redes PBN: riesgo de penalización manual.

## Errores comunes (pitfalls)
- **Noindex por error** en staging/entorno de pruebas copiado a producción.
- **Canonical apuntando a otra URL** (ej. a versión con params) → Google indexa la equivocada.
- **Keyword stuffing** en metas y alt → penalización o CTR bajo.
- **Contenido duplicado** entre páginas o copiado de otros sitios → canibalización o filtro.
- **Ignorar Search Console**: errores 404, cobertura, problemas de seguridad se ven ahí primero.
- **Cambiar URLs sin redirección 301** → pierde autoridad y tráfico.
- **Title cambiado por JS tras render** (SPA sin SSR/prerender) → Google indexa el title del HTML estático.
- Indexar "nofollow" enlaces internos importantes (nofollow es para enlaces externos no confiables, no para tu propia navegación).

## Herramientas
- **Google Search Console**: indexación, queries, Core Web Vitals, sitemaps. Gratis y obligatoria.
- **PageSpeed Insights**: lab + field data de CWV por URL.
- **Lighthouse** (Chrome DevTools / CLI): auditoría completa on-page+técnica.
- **Screaming Frog** (free hasta 500 URLs): crawl, titles duplicados, metas faltantes, broken links.
- **Rich Results Test**: validar JSON-LD.
- **Ahrefs/Semrush** (pago): backlinks y keywords avanzadas; alternativas: Ubersuggest, Keyword Surfer (extensión gratis).

## Verificación final (checklist)
1. `curl -sI` home → 200, HTTPS, sin `x-robots-tag: noindex`.
2. robots.txt no bloquea rutas importantes; sitemap.xml accesible y referenciado en GSC.
3. Una sola versión canónica (www/no-www + http/https resuelto con 301).
4. Title/description/H1 únicos por página, keyword principal presente.
5. JSON-LD válido en Rich Results Test.
6. PageSpeed Insights móvil: LCP < 2.5s, INP < 200ms, CLS < 0.1.
7. URLs canónicas en el sitemap; sin duplicados ni params.
8. Indexación pedida en GSC y status "Página indexada".
