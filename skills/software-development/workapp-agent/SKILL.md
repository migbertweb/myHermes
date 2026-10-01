---
name: workapp-agent
description: "Full-stack freelance project manager app: Express + sql.js + React + Tailwind + Vite. Project tracking, kanban, budgets, analytics, clients, invoices, timer."
version: 1.2.0
author: Hermes Agent
---

# WorkApp Agent — Freelance Project Manager

Full-stack app para gestión de proyectos freelance ubicada en `/home/migbert/workapp-agent`.

## Stack

- **Backend**: Express + sql.js (SQLite WASM — NO native compile needed, avoids better-sqlite3 build failures on Arch/CachyOS)
- **Frontend**: React 19 + Vite 6 + Tailwind v4 + react-router-dom + recharts + dnd-kit + lucide-react
- **Puertos**: Backend 3001, Frontend Vite 5173 (proxy `/api` → 3001)

## Arranque

```bash
# Backend (terminal 1)
cd /home/migbert/workapp-agent && node server.js

# Frontend (terminal 2)
cd /home/migbert/workapp-agent/client && npx vite --port 5173
```

## Estructura

```
workapp-agent/
├── server.js              # API REST + auth middleware
├── db.js                  # sql.js wrapper con prepared statements + users table
├── auth.js                # JWT auth: seedAdmin, requireAuth, login/register/logout/me
├── notify.js              # Telegram notifications
├── activity.js            # Activity log centralizado
├── package.json           # root: express + sql.js + cors + bcryptjs + jsonwebtoken + cookie-parser + multer
├── client/
│   ├── vite.config.js     # proxy /api → 3001
│   ├── index.html
│   └── src/
│       ├── main.jsx       # BrowserRouter entry
│       ├── App.jsx        # Router + sidebar + theme toggle + ToastProvider + mobile hamburger + auth gate
│       ├── api.js         # fetch wrapper con JWT token (auth header + 401 handling)
│       ├── pdf.js         # jsPDF generators: downloadInvoicePDF, downloadBudgetPDF
│       ├── AuthContext.jsx # React context: login/logout/user + session check
│       ├── roles.js       # ROLE_NAMES map (dev→Desarrollador, etc.)
│       ├── index.css      # Tailwind base + CSS vars (dark/light) + print styles + responsive MQ
│       ├── components/
│       │   ├── Modal.jsx
│       │   ├── ProjectForm.jsx      # datalist dinámico de clientes desde API
│       │   ├── ActivityFeed.jsx     # timeline con timeAgo relativo
│       │   └── FileUpload.jsx       # drag & drop + multer, download/delete
│       └── pages/
│           ├── Login.jsx         # Pantalla de login
│           ├── Dashboard.jsx       # KPIs configurables (widgets) + cards de proyectos + create modal
│           ├── Projects.jsx        # CRUD proyectos + clone + CSV + cards clickeables (useNavigate)
│           ├── ProjectDetail.jsx   # 5 tabs: overview (activity+files), kanban, tasklist (CSV), budget (PDF), time + timer
│           ├── Budget.jsx          # Admin: tarifas editables, asunciones, márgenes, PDF
│           ├── Analytics.jsx       # 7 gráficos recharts + market rates + auto-refresh 30s
│           ├── Clients.jsx         # CRUD clientes con métricas
│           ├── Invoices.jsx        # CRUD facturas + PDF download + CSV
│           └── Settings.jsx        # Info del sistema + cambio de contraseña
```

## Autenticación (DIY JWT)

Stack: `bcryptjs` + `jsonwebtoken` + `cookie-parser` (3 deps puras JS, 0 compilación nativa).

**Archivos**:
- `auth.js` — `seedAdmin()`, `requireAuth` middleware, `authRoutes(app)` con `/api/auth/login|register|logout|me` + `PUT /api/auth/password`
- `client/src/AuthContext.jsx` — React context con `login()`, `logout()`, `user`, chequea sesión al montar
- `client/src/pages/Login.jsx` — Pantalla de login (sin credenciales visibles en el footer)
- `client/src/pages/Settings.jsx` — Formulario "Cambiar Contraseña" integrado

**Flujo**:
1. Al arrancar, `seedAdmin()` crea usuario admin/admin123 si no existe
2. Login → bcrypt.compare → JWT (7d) → httpOnly cookie + token en response
3. Frontend guarda token en localStorage y lo envía en header `Authorization: Bearer`
4. Middleware `requireAuth` protege todas las rutas `/api/*` excepto `/api/auth/*` y `/api/market_rates`
5. API responde 401 → frontend limpia token y recarga (muestra login)
6. Logout limpia cookie + localStorage
7. Cambio de contraseña: `PUT /api/auth/password` (validado con currentPassword) + formulario en Ajustes

**Variables de entorno**:
- `JWT_SECRET` (default: `workapp-dev-secret-change-in-production`)
- `ADMIN_USER` / `ADMIN_PASS` (default: `admin` / `admin123`)

## Schema SQLite (sql.js)

Tablas: `projects`, `stages`, `tasks`, `line_items`, `time_entries`, `assumptions`, `project_rates`, `clients`, `invoices`, `users`, `activity_log`, `attachments`.

Etapas default al crear proyecto: Discovery, Presupuesto, Contrato, Ejecución, QA, Entregado.
Tarifas default por rol: dev=40, design=35, pm=30, qa=25.
Auth: admin seed al primer boot (admin/admin123), JWT 7d, proteger todas las rutas `/api/*` menos `/api/auth/*`.

## Pitfalls y fixes aplicados

### 1. sql.js: "Statement closed" error (CRÍTICO)
**Causa**: `_db.prepare(sql)` no puede cachearse — los statements de sql.js se invalidan tras `free()/reset()`. Usar `_stmtCache` reventó en la segunda llamada.
**Fix**: Crear statement fresco en cada `all()`/`get()`/`run()`, sin caché. Patrón correcto:
```js
all(...params) {
  const stmt = _db.prepare(this.sql);
  stmt.bind(params.map(v => v === undefined ? null : v));
  const results = [];
  while (stmt.step()) results.push(stmt.getAsObject());
  stmt.free();
  return results;
}
```

### 2. npm install bloquea scripts — binarios no se instalan
**Causa**: `.npmrc` global tiene `allow-scripts=node-pty`. Paquetes como esbuild/vite/concurrently no ejecutan postinstall.
**Fix**: Crear `.npmrc` local con `allow-scripts=*` o aprobar específicos con `npm install-scripts approve <pkg>`.

### 3. Vite v8 no existe — package.json tenía `"vite": "^8.1.1"`
**Fix**: Cambiar a `"vite": "^6.0.0"` y `"@vitejs/plugin-react": "^4.3.4"`.

### 4. Componentes sin try-catch → UI congelada en "Cargando…"
**Causa**: `load()` en Analytics/Dashboard/Projects sin manejo de errores.
**Fix**: try-catch + `error` state + banner rojo con botón "Reintentar".

### 5. Project cards no navegaban al hacer click
**Causa**: Solo el `<Link>` del título era clickeable, no toda la card.
**Fix**: `onClick={() => navigate(...)}` en el `div.project-card`, `stopPropagation()` en botones edit/delete.

### 6. Campo cliente sin autocomplete
**Fix**: `<datalist>` poblado con `api.getClients()` al montar ProjectForm.

### 7. Autenticación: JWT + bcryptjs sin compilar
**Librerías**: `bcryptjs` (JS puro, NO `bcrypt` que requiere node-gyp), `jsonwebtoken`, `cookie-parser`.
**API pública**: `/api/auth/login`, `/api/auth/register`, `/api/auth/logout`, `/api/auth/me`, `/api/market_rates`.
**Protección**: Middleware `requireAuth` en `app.use('/api', ...)` protege todo lo demás.
**Frontend**: `AuthProvider` en main.jsx. Si no hay usuario → muestra `<Login/>`. Si 401 en cualquier request → limpia token → login.
**Credenciales default**: `admin` / `admin123`. Configurable con env vars `ADMIN_USER`/`ADMIN_PASS`.

### 8. Dokploy: Nixpacks ignora el Dockerfile y falla (CRÍTICO deploy)
**Causa**: Dokploy detecta `package.json` y usa Nixpacks por defecto. Nixpacks corre `npm ci` en el root sin devDeps del client → `npm run build` falla porque `vite` no existe.
**Fix**: En Dokploy → configuración de la app → cambiar método de build de "Nixpacks" a **"Dockerfile"**. El Dockerfile multi-stage ya está en el repo y maneja correctamente el build del frontend dentro de `client/`.
**Síntoma**: `sh: 1: vite: not found` en el log de build de Dokploy.
**Alternativa**: Agregar `cd client && npm install` en un script `prebuild` del package.json raíz, pero la imagen resultante sería mucho más pesada (Nixpacks usa ubuntu base + nix, ~550MB vs ~120MB con alpine + Dockerfile).

## Docker / Deploy

## Telegram Notifications (Tier 1) ✅

Bot: `@MyPiroworkapp_bot`, verificado con `getMe`. Token + chat ID configurados en Dokploy.

**Archivos**: `notify.js` (helper con `send()`, `projectCreated()`, `taskCompleted()`, `invoiceOverdue()`, `deadlineNear()`), hooks async en server.js para `POST /api/projects` y `PUT /api/tasks/:id` (transición a `done`). Endpoint `POST /api/settings/telegram` con `{test: true}`.

**Flujo de diagnóstico**:
1. `curl -s "https://api.telegram.org/bot<TOKEN>/getMe"` — si 401, token inválido (no es falta de /start)
2. Usuario debe enviar `/start` al bot antes de cualquier notificación
3. Probar: `node -e "import('./notify.js').then(m => m.notify.send('test'))"`

## Clone de proyecto (Tier 1 Item 3) ✅

`POST /api/projects/:id/clone` — duplica estructura completa: etapas (mapea oldId→newId), tareas (resetea status a `todo`), rates, opcional `{include_line_items: true}` para line items.
UI: botón 📋 en cada card de Projects.jsx. `api.cloneProject(id, includeLineItems)`.

## Export CSV (Tier 1 Item 4) ✅

Endpoints: `GET /api/projects/export/csv`, `GET /api/projects/:id/tasks/export/csv`, `GET /api/time/export/csv`, `GET /api/invoices/export/csv`.
UI: botones 📥 CSV en Projects, Invoices, y pestaña Tasklist (ProjectDetail). `toCSV()` helper en server.js.

## Activity Log (Tier 1 Item 5) ✅

Tabla `activity_log` (id, project_id, username, action, entity, entity_id, name, details, created_at).
Módulo `activity.js` con `activity.log()` centralizado. Hooks en server.js: proyecto creado, tarea creada, tarea→done.
API: `GET /api/activity?limit=30`, `GET /api/projects/:id/activity`.
UI: `ActivityFeed.jsx` con timeAgo relativo. Dashboard (5 items compacto) y ProjectDetail overview (historial completo).

### Pitfall 9: Dockerfile no copia nuevos .js de raíz (CRÍTICO deploy)

**Causa**: Al agregar `notify.js` o `activity.js`, el Dockerfile solo copiaba `server.js db.js auth.js`. Deploy falla con `ERR_MODULE_NOT_FOUND`.
**Fix**: Agregar `COPY notify.js ./` y `COPY activity.js ./` en el stage de producción.
**Regla permanente**: todo `.js` nuevo en la raíz del proyecto DEBE tener su `COPY` en el Dockerfile simultáneamente. Si no, deploy falla.

### Pitfall 11: jsPDF autotable — `i.autoTable is not a function` en Vite/ESM

**Causa**: `import 'jspdf-autotable'` como side-effect no engancha al prototype de jsPDF con tree-shaking de Vite.
**Síntoma**: Al hacer click en 📄 Descargar PDF → alert "i.autoTable is not a function" o silencio total.
**Fix**: 
```js
// ❌ ROTO — side-effect no funciona con Vite
import { jsPDF } from 'jspdf';
import 'jspdf-autotable';
doc.autoTable({ ... });

// ✅ CORRECTO
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
autoTable(doc, { ... });
```
**Regla**: Siempre usar la forma funcional `autoTable(doc, opts)` en proyectos con Vite.

### Pitfall 16: jsPDF — columnas de tabla no caben en la página (CRÍTICO PDF)

**Causa**: Los anchos de columna sumados exceden el ancho disponible. A4 = 210mm, márgenes = 20mm c/u, ancho usable = 170mm.
**Síntoma**: Warning "Of the table content, X units width could not fit page" + error "Invalid argument passed to jsPDF.f3" en `encodeColorString` → `setTextColor`. El error real es que `doc.lastAutoTable` queda `undefined` al fallar la tabla, y luego `y = undefined + 8 = NaN`, y el `doc.text(label, sx, NaN)` o el `setTextColor` con estado corrupto lanzan el error.
**Fix**: 
1. Reducir columnWidths a exactamente 170mm: `10 + 80 + 26 + 20 + 34 = 170` 
2. Guard en TODOS los `doc.lastAutoTable.finalY`: `y = (doc.lastAutoTable?.finalY || y + 20) + offset`

### Pitfall 17: jsPDF — setTextColor/setFillColor/setDrawColor NO aceptan arrays RGB (jsPDF 4.2.1)

**Causa**: `encodeColorString` (`f3`) en jsPDF 4.2.1 solo acepta strings hex o 3 números sueltos. Pasar un array `[51,51,51]` o hacer spread `...[51,51,51]` lanza `Invalid argument passed to jsPDF.f3`.
**Fix**: Usar strings hexadecimales para TODOS los colores:
```js
// ❌ ROTO — arrays o spread
const T = { teal: [0, 168, 150] };
doc.setTextColor(T.teal);       // ROMPE
doc.setTextColor(...T.teal);    // ROMPE

// ✅ CORRECTO — hex strings
const T = { teal: '#00a896', ink: '#333333', gray: '#666666', light: '#e0e0e0', white: '#ffffff', red: '#dc3545', green: '#00a896' };
doc.setTextColor(T.ink);
doc.setFillColor(T.teal);
```
**Aplica a**: `setTextColor`, `setFillColor`, `setDrawColor`. Buscar con regex `\[.*\]` en la paleta de colores para verificar que no queden arrays.

### Pitfall 18: jsPDF — cabecera "No" se rompe en dos líneas

**Causa**: Columna de 10mm es muy angosta para "No" → "N" en una línea, "o" en otra. Desalinea toda la tabla.
**Fix**: Usar `'#'` (1 carácter) en vez de `'No'`. Ajustar columna a 8mm centrada. Compensar +2mm en la columna de descripción.
```js
// ✅
head: [['#', 'Descripción', 'Precio', 'Cant (h)', 'Total']],
columnStyles: { 0: { cellWidth: 8, halign: 'center' }, 1: { cellWidth: 82 }, ... }
// 8 + 82 + 26 + 20 + 34 = 170mm
```

### Pitfall 19: jsPDF — total debe calcularse de line items reales

**Causa**: La factura mostraba `Subtotal = Total = invoice.amount` sin desglose real.
**Fix**: 
1. Cargar line items antes de generar PDF: `const items = await api.getLineItems(inv.project_id)`
2. `lineSubtotal = lineItems.reduce((s, i) => s + (i.amount || 0), 0)`
3. Si `Math.abs(lineSubtotal - invoice.amount) > 0.01`, mostrar "Ajuste"
4. El botón en Invoices.jsx debe ser async: `onClick={async () => { const items = await api.getLineItems(...); await downloadInvoicePDF(inv, project, items); }}`

### Pitfall 12: DB se borra en cada deploy de Dokploy (CRÍTICO datos)

**Causa**: La DB se creaba en `/app/workapp.db` (directorio raíz del contenedor), no en `/app/data/workapp.db` (dentro del volumen montado). Cada redeploy destruye el contenedor → DB nueva.
**Síntoma**: Después de cada deploy, la app arranca como nueva (sin proyectos, admin re-seedeado). Log muestra: `Database initialized at /app/workapp.db` en vez de `/app/data/workapp.db`.
**Fix (código)**: Cambiar default en `db.js` de `path.join(__dirname, 'workapp.db')` a `path.join(__dirname, 'data', 'workapp.db')`. Agregar `fs.mkdirSync(dataDir, { recursive: true })` en `bootstrap()`.
**Fix (Dokploy)**: En Dokploy Dashboard → servicio WorkApp → pestaña Volumes/Storage → agregar manualmente:
  - **Path en contenedor**: `/app/data`
  - **Tipo**: Volume
  - **Nombre**: `workapp_data`
**Verificación**: Crear un proyecto, hacer deploy, verificar que sobrevive. El log debe decir `Database initialized at /app/data/workapp.db` y NO debe mostrar `Admin user created` en deploys subsiguientes.

### Pitfall 14: NODE_ENV=production impide instalar devDependencies localmente

**Causa**: Si el shell tiene `NODE_ENV=production`, `npm install` en `/client` salta devDependencies (vite, tailwindcss, @vitejs/plugin-react, @tailwindcss/vite). `npx vite` falla con `ERR_MODULE_NOT_FOUND: Cannot find package 'vite'`.
**Síntoma**: `ls node_modules/vite` → no existe. `npm install` dice "up to date".
**Fix**: `npm install --include=dev` en `/client`, o `unset NODE_ENV` antes de instalar.

### Pitfall 15: Logo en PDFs — carga async con canvas (jsPDF + Vite)

**Patrón correcto para meter imágenes en jsPDF desde el proyecto**:
```js
let _logoDataUrl = null;

async function loadLogo() {
  if (_logoDataUrl) return _logoDataUrl; // cache
  const img = await new Promise((resolve, reject) => {
    const i = new Image();
    i.onload = () => resolve(i);
    i.onerror = reject;
    i.src = '/logo.png'; // servido como estático por Express/Vite
  });
  const canvas = document.createElement('canvas');
  canvas.width = img.width;
  canvas.height = img.height;
  canvas.getContext('2d').drawImage(img, 0, 0);
  _logoDataUrl = canvas.toDataURL('image/png');
  return _logoDataUrl;
}
// Uso: const logoUrl = await loadLogo(); doc.addImage(logoUrl, 'PNG', x, y, w, h);
```
**Requiere**: `async/await` en todas las funciones que llamen a `drawHeader()` (que a su vez llama a `loadLogo()`). Exportar las funciones de PDF como `async`.
**Ubicación del logo**: `client/public/logo.png` → servido en `/logo.png`. Si se usa en Express production, también debe estar en el build.
### Pitfall 13: Estilo PDF — el usuario mostró diseño de referencia (lección)

**Situación**: El usuario mostró una imagen de factura profesional y dijo "me gusta este estilo".
**Acción**: Adaptar los PDFs al estilo de referencia inmediatamente, no ignorarlo.
**Resultado final (v5 — autoTable alineado)**:
- **Empresa**: Migbert Yanez · Desarrollo Freelance
- **Logo**: carga async desde `/logo.png` vía `new Image()` → canvas → `data:image/png` → `doc.addImage()`. Cacheado en `_logoDataUrl`. Fallback a "M" dibujado si carga falla.
- **Paleta**: colores en hex strings (`'#00a896'`, `'#333333'`, etc.) — arrays RGB no compatibles con jsPDF 4.2.1
- **Header**: logo pill izq + empresa + contacto der (2 columnas), separador gris
- **Títulos**: FACTURA 24pt teal derecha. PRESUPUESTO 13pt teal (etiqueta) + nombre proyecto 12pt bold negro (título real). La fecha en 8pt gris abajo.
- **Tablas**: `autoTable(doc, {...})` estilo plain con `margin: { left: 20, right: 20 }`. Sin `columnStyles` (auto-sizing nativo evita desalineación). `fontSize: 7`, `cellPadding: 3` para maximizar contenido en una página.
- **Factura foot rows**: Subtotal, Ajuste (si difiere), TOTAL — calculados de `lineItems.reduce()`. El botón PDF de Invoices hace `await api.getLineItems(inv.project_id)` para cargar items reales.
- **Presupuesto**: 3 tablas secuenciales (Etapas, Desglose costos, Resumen financiero) todas con el mismo `margin`. Resumen financiero: tabla con colores condicionales (verde positivo, rojo costo).
- **Footer**: línea de firma izq + formas geométricas decorativas der (achicadas para no tapar fecha) + "Gracias"
- **Notas**: 2 columnas compactas (<50% del footer). Sección de validez: línea única.
- **Método de pago**: Transferencia bancaria · Pago móvil · Revolut. Detalles: Banco Mercado Pago / Nubank · Revolut: @migbertyanez. Plazo 15 días.
- **Budget page PDF**: La página `/budget` usa `downloadBudgetPDF()` (jsPDF profesional), NO `window.print()`. Botón "Exportar PDF" con ícono Download y clase `btn-primary`. Carga stages vía `api.getStages()` antes de generar.
- **Espaciado compacto global**: `cellPadding: 3`, `fontSize: 7`, secciones y+=5-6mm para que todo entre en una página.

## PR & Branch Workflow

Convenciones:
- **Una rama por fix**: `fix/<desc>` o `feat/<desc>` → un PR por cambio, nunca agrupar
- **Commit**: `fix:` o `feat:` + descripción concisa
- **Build antes de commit**: `cd client && npm run build`
- **Merge**: `gh pr merge <N> --squash --delete-branch` → `git checkout main && git pull origin main`
- **Post-fix visual**: re-correr `npx -y impeccable detect client/src/`

**Ramas activas**:
- `main` — producción, deploy automático en Dokploy (puerto 3001)
- `dev` — desarrollo local, probar cambios antes de merge a main
- Flujo: `dev` → test local (`npx vite --port 5173`) → merge a `main` vía PR → deploy producción
- Ambas ramas deben mantenerse sincronizadas: después de merge a main, `git checkout dev && git merge main && git push origin dev`
- PR desde dev a main: `gh pr create --base main` (no al revés)
- **Nunca desarrollar directamente en main**. Usar dev para experimentos locales. Solo mergear a main cuando esté verificado.

## Features

| Feature | Implementación |
|---|---|
| Dark/light toggle | `data-theme` attribute + CSS vars + localStorage |
| PDF invoices | jsPDF + autotable — estilo teal corporativo `#00A896`. `downloadInvoicePDF()` con header 2 columnas, tabla clean, resumen financiero, footer decorativo. **Ver `references/pdf-generation.md` para pitfalls detallados.** |
| PDF budgets | jsPDF + autotable — `downloadBudgetPDF()` con etapas, costos, margen, validez 30 días, formas geométricas decorativas |
| Toast notifications | React context + slideIn animation + auto-dismiss 4s |
| Mobile hamburger | `@media (max-width: 768px)`: `.mobile-header` + overlay slide-in |
| Role names | `roles.js` con `ROLE_NAMES` map, `.role-full`/`.role-short` CSS toggle |
| Live timer | `useEffect` con `setInterval` en ProjectDetail, persiste entrada al detener |
| Kanban drag&drop | `@dnd-kit/core` con `DndContext` + `useDraggable`/`useDroppable` |
| Market rates | Endpoint `/api/market_rates` con 14 categorías freelance hardcodeadas |
| Password change | `PUT /api/auth/password` + formulario en Ajustes con confirmación |
| File uploads | Multer + drag & drop en ProjectDetail, tabla `attachments`, download/delete |
| Dashboard widgets | Toggle KPIs via ⚙️ settings, persistido en localStorage `workapp-widgets` |
| Clone proyecto | `POST /api/projects/:id/clone` — etapas, tareas, rates, opcional line items |
| Export CSV | Projects, tasks, time, invoices — `toCSV()` helper |
| Activity log | `activity_log` table, feed en Dashboard + ProjectDetail con timeAgo |
| Favicon | SVG personalizado con logo W en gradiente violeta |

## Responsive breakpoints

- `@media (max-width: 768px)`: sidebar → hamburger menu, budget grid → 1 col, kanban cols → 220px, padding reducido, role names → abreviados
- Desktop (>768px): sidebar fija 240px, grid 2fr 1fr en budget, roles completos

## Vite config

```js
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { port: 5173, proxy: { '/api': 'http://localhost:3001' } }
})
```

## Docker / Deploy

### Dockerfile (multi-stage, alpine)

- **Stage 1 (builder)**: `node:22-alpine` — instala root deps + client deps, compila frontend con `vite build`
- **Stage 2 (production)**: `node:22-alpine` — solo server + `client/dist/` + deps prod (0 devDeps). Corre como `node` user.
- Peso final: ~120 MB (alpine + sql.js WASM + Express + build React estático).
- SQLite DB path configurable vía `DB_PATH` env var (default: `./data/workapp.db`). En Docker se apunta a `/app/data/workapp.db` montado como volumen.

### docker-compose.yml para Dokploy

```yaml
services:
  workapp:
    build: .
    restart: unless-stopped
    ports: ["3001:3001"]
    volumes: [workapp_data:/app/data]
    environment:
      DB_PATH: /app/data/workapp.db
      JWT_SECRET: ${JWT_SECRET:-change-me}
      ADMIN_USER: ${ADMIN_USER:-admin}
      ADMIN_PASS: ${ADMIN_PASS:-change-me}
    healthcheck:
      test: wget --spider http://localhost:3001/api/auth/me
volumes:
  workapp_data:
```

### Dokploy — configuración

1. Crear app apuntando al repo https://github.com/migbertweb/workgestionapp
2. **Build method: Dockerfile** (NO Nixpacks — ver pitfall #8)
3. Variables de entorno en la UI de Dokploy (no en archivo):
   - `JWT_SECRET` — secreto seguro
   - `ADMIN_PASS` — contraseña del admin
4. La DB persiste en volumen `workapp_data` → sobrevive redeploys

### Variables de entorno soportadas

- Repo público: https://github.com/migbertweb/workgestionapp
- sql.js NO usa `better-sqlite3`. Compatible con cualquier plataforma sin compilar módulos nativos.
- Persistencia: `export()` a `.db` con debounce 50ms en cada write.
- `last_insert_rowid()` se consulta con `_db.exec()` después del `step()`.
- Las animaciones CSS (`slideIn`, `transition`) están en index.css.
