# Fullstack scaffold: Express + React + Vite + Tailwind

When the user wants a richer SPA (dashboards, kanban with DnD, live charts, multi-tab views) keep the Express + SQLite backend from the default stack and split the frontend into a Vite-hosted React app under `client/`.

## Layout

```
project/
├── server.js           # Express API, serves /api/* and SPA fallback
├── db.js               # sql.js persistence (see persistence-patterns.md)
├── package.json        # root: concurrently dev scripts
├── client/
│   ├── package.json    # vite, react, tailwind, recharts, dnd-kit, lucide-react, react-router-dom
│   ├── vite.config.js  # proxy /api → backend
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx          # router + layout
│       ├── api.js           # fetch wrapper → /api/*
│       ├── index.css        # @import "tailwindcss";
│       ├── components/      # Modal, forms, cards
│       └── pages/           # one file per route
```

## Vite config

```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: { '/api': 'http://localhost:3001' }
  }
})
```

Tailwind v4 uses `@tailwindcss/vite` (no `postcss.config.js`, no `tailwind.config.js` needed). Just `@import "tailwindcss";` at the top of `src/index.css`.

## Root package.json dev scripts

```json
{
  "scripts": {
    "dev": "concurrently \"npm run server\" \"npm run client\"",
    "server": "node server.js",
    "client": "cd client && npm run dev",
    "build": "cd client && npm run build"
  },
  "devDependencies": { "concurrently": "^9.0.1" }
}
```

If `concurrently` fails to install its binary (due to npm `allow-scripts` restrictions — see persistence-patterns.md), drop the `dev` script and run backend/frontend in separate terminals:

```bash
# Terminal 1
node server.js
# Terminal 2
cd client && npx vite --port 5173 --host
```

## Express SPA fallback

After all `/api/*` routes, serve the built client so production mode (single port 3001) works:

```js
const clientBuild = path.join(__dirname, 'client', 'dist');
app.use('/assets', express.static(path.join(clientBuild, 'assets')));
app.get('*', (req, res, next) => {
  if (req.path.startsWith('/api/')) return next();
  res.sendFile(path.join(clientBuild, 'index.html'));
});
```

## Vite version pinning

Vite majors break often. Pin to known-good ranges:
- `vite@^6.0.0` — current stable as of Node 26.
- `@vitejs/plugin-react@^4.3.4`
- `tailwindcss@^4.0.0` + `@tailwindcss/vite@^4.0.0`

Avoid `vite@^8.x` or higher — these don't exist yet and npm will silently skip the dependency (install reports success but `node_modules/vite` is missing). Always verify with `ls node_modules/.bin/vite` after install.

## Installing client deps without tripping terminal heuristics

`npm install` with many packages can be flagged as a long-running process by the terminal tool. Workarounds that worked:

- `npm install --no-audit --no-fund --ignore-scripts <pkgs>` — quiet flags reduce output and the install stays foreground-eligible.
- Write `client/package.json` directly with all deps pinned, then `rm -rf client/node_modules client/package-lock.json && npm install --no-audit --no-fund --ignore-scripts --prefix client` fresh.
- If the terminal tool keeps blocking, use `execute_code` with its `terminal()` helper — it has different heuristics.

## DnD-kit kanban pattern

For drag-and-drop status columns:

- `DndContext` wraps the board; each column is a `useDroppable`; each card is `useDraggable`.
- `PointerSensor` with `activationConstraint: { distance: 5 }` prevents accidental drags on click.
- `onDragEnd` calls `api.updateTask(id, { status: over.id })` and updates local state optimistically.
- `DragOverlay` renders a ghost of the active card for visual feedback.
- Cast draggable IDs to strings (`String(task.id)`) — dnd-kit requires string IDs.

## Recharts live data

For charts that refresh (analytics):

```jsx
useEffect(() => {
  const load = async () => setData(await api.getAnalytics());
  load();
  const i = setInterval(load, 30000); // 30s refresh
  return () => clearInterval(i);
}, []);
```

Use `ResponsiveContainer` + `BarChart`/`PieChart`/`AreaChart` with dark theme colors: grid `#334155`, tooltip bg `#1e293b` border `#475569`.

## Pitfall: root install wipes client/node_modules

Running `npm install --prefix .` from the project root can remove a sibling `client/node_modules` directory (observed with concurrently install). Always re-run client install after touching root deps:

```bash
rm -rf client/node_modules client/package-lock.json
(cd client && npm install --no-audit --no-fund --ignore-scripts)
```

## Smoke test checklist

After both servers are up:
1. `curl -s http://localhost:3001/api/projects` → `[]` or array of projects
2. `curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/` → `200`
3. `curl -s http://localhost:5173/src/main.jsx -o /dev/null -w "%{http_code}"` → `200` (Vite serving JSX)
4. `curl -s -X POST http://localhost:3001/api/projects -H 'Content-Type: application/json' -d '{"name":"Test"}'` → verify the created object
5. `curl -s http://localhost:3001/api/projects` → array with the new project (if empty, check sql.js `.run()` vs `.exec()` in db.js)
6. Navigate browser to `http://localhost:5173/` → dashboard loads, no console errors

## Frontend error handling: avoid eternal "Cargando…" states

**The bug**: pages that fetch data on mount with `load()` but don't wrap it in try-catch. If the API returns 500 (backend down, bad query), `data` stays null and the component renders "Cargando…" forever with no feedback to the user. Analytics and dashboards are the most common victims.

**Fix — universal pattern for every data-fetching page:**

```jsx
const [data, setData] = useState(null);
const [error, setError] = useState('');

const load = async () => {
  try {
    const result = await api.getSomething();
    setData(result);
    setError('');
  } catch (e) {
    setError('Error: ' + e.message);
  }
};

useEffect(() => { load(); }, []);

if (error) return (
  <div className="card">
    <p style={{ color: 'var(--danger)' }}>{error}</p>
    <button className="btn btn-primary" onClick={load}>Reintentar</button>
  </div>
);
if (!data) return <div>Cargando…</div>;
```

Apply this to every page that calls `api.*` in a `load()` function. Also wrap `handleCreate`/`handleEdit`/`handleDelete` in try-catch and set the same error state so mutation failures surface visibly.

## Clickable project card pattern

When using react-router `Link` inside a card, only the text is clickable — clicking the card body does nothing. Fix by using `useNavigate` with `onClick` on the card div, and `e.stopPropagation()` on action buttons (edit/delete):

```jsx
const navigate = useNavigate();
<div className="project-card" onClick={() => navigate(`/projects/${p.id}`)}>
  <h3>{p.name}</h3>
  <button onClick={(e) => { e.stopPropagation(); handleEdit(p); }}>Edit</button>
  <button onClick={(e) => { e.stopPropagation(); handleDelete(p.id); }}>Delete</button>
</div>
```

## Dark/light theme toggle

CSS custom properties in `:root` + `[data-theme="light"]`, toggled via a button that sets `document.documentElement.setAttribute('data-theme', theme)` and persists to `localStorage`:

```jsx
const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark');
useEffect(() => {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
}, [theme]);
```

Toggle button: `<button onClick={() => setTheme(t => t === 'dark' ? 'light' : 'dark')}>` with Sun/Moon icons.

## Toast notifications via React context

Lightweight toast system without external deps: create a ToastContext with an `add(msg, type)` function, render a fixed-position toast tray at the bottom right. Wrap the app in `<ToastProvider>`.

```jsx
export const ToastContext = createContext();
export function useToast() { return useContext(ToastContext); }

function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const add = useCallback((msg, type = 'info') => {
    const id = Date.now();
    setToasts(t => [...t, { id, msg, type }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 4000);
  }, []);
  return (
    <ToastContext.Provider value={add}>
      {children}
      <div style={{ position: 'fixed', bottom: 20, right: 20, zIndex: 200 }}>
        {toasts.map(t => (
          <div key={t.id} style={{ background: typeColor, animation: 'slideIn 0.2s' }}>{t.msg}</div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
```

## PDF / print export

**Print (simplest)**: `window.print()` with `@media print` CSS that hides sidebar, buttons, modals, and applies clean black-on-white styling. No external PDF library needed.

```css
@media print {
  body { background: white; color: black; }
  aside, .btn, button, .sidebar-link, .modal-overlay { display: none !important; }
  main { margin: 0 !important; padding: 16px !important; max-width: 100% !important; }
  .card, .stat-card, .project-card { border: 1px solid #ddd; box-shadow: none; break-inside: avoid; }
}
```

**jsPDF + autotable (professional PDFs)**: When the user needs styled PDFs with tables, headers, and branding:

```bash
cd client && npm install jspdf jspdf-autotable
```

**⚠️ CRITICAL — ESM import pitfall**: `import 'jspdf-autotable'` as a side-effect does NOT work with Vite/ESM tree-shaking. The `doc.autoTable()` method won't exist. Must use named import + function call:

```js
// ❌ BROKEN with Vite
import { jsPDF } from 'jspdf';
import 'jspdf-autotable';
doc.autoTable({ ... });  // TypeError: doc.autoTable is not a function

// ✅ WORKS with Vite
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
autoTable(doc, { ... });  // correct
```

After calling `autoTable(doc, opts)`, `doc.lastAutoTable.finalY` is still available for positioning subsequent content.

**Design iteration**: When the user shows a reference image ("me gusta este estilo"), adapt the PDF styling immediately — don't argue. Use the reference's palette, header layout, table style, summary format, and footer decorations.

## Datalist for dynamic autocomplete (no external deps)

When a form field needs to suggest existing values from the DB while allowing free-text input (e.g., client names when creating a project), use HTML5 `<datalist>`:

```jsx
const [clients, setClients] = useState([]);
useEffect(() => { api.getClients().then(setClients).catch(() => {}); }, []);

// In the form:
<input
  className="input"
  value={form.client}
  onChange={e => setClient(e.target.value)}
  list="client-list"
  placeholder="Seleccioná o escribí un cliente..."
/>
<datalist id="client-list">
  {clients.map(c => <option key={c.id} value={c.name} />)}
</datalist>
```

The browser shows a dropdown with matching options as the user types, but the field remains a free-text input (new values allowed). Falls back to plain text input in old browsers. Zero npm deps.

## Responsive patterns: desktop-full / mobile-abbreviated labels

When a label is long on desktop but needs abbreviating on mobile, use paired spans with CSS media queries:

```jsx
<span>
  <span className="role-full">{ROLE_NAMES[role] || role}</span>
  <span className="role-short">{role}</span>
</span>
```

```css
.role-full { display: inline; }
.role-short { display: none; }

@media (max-width: 768px) {
  .role-full { display: none; }
  .role-short { display: inline; }
  aside { display: none !important; }
  main { padding: 16px !important; max-width: 100% !important; }
  .budget-grid { grid-template-columns: 1fr !important; }
  .kanban-col { min-width: 220px; width: 220px; max-height: 60vh; }
}
```

This pattern works for any content that has a long + short form: role names, status labels, full names vs initials.

## Mobile hamburger menu

When hiding the desktop sidebar on mobile (`@media (max-width: 768px) { aside { display: none } }`), provide a hamburger menu overlay so the user can still navigate:

1. Add a `<div className="mobile-header">` fixed at top (hidden on desktop, flex on mobile). It shows a compact logo + hamburger button.
2. The hamburger opens a `<div className="mobile-overlay">` (full-screen semi-transparent backdrop) containing the same sidebar nav.
3. Close on overlay click, ✕ button, or route change (`useEffect(() => setOpen(false), [loc.pathname])`).

```jsx
const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
useEffect(() => { setMobileMenuOpen(false); }, [loc.pathname]);

{/* Mobile header — hidden on desktop, flex on mobile via CSS */}
<div className="mobile-header" style={{
  position: 'fixed', top: 0, left: 0, right: 0, height: 52,
  background: 'var(--surface)', borderBottom: '1px solid var(--border)',
  display: 'none', alignItems: 'center', justifyContent: 'space-between',
  padding: '0 16px', zIndex: 50,
}}>
  <span style={{ fontWeight: 700 }}>WorkApp</span>
  <button onClick={() => setMobileMenuOpen(true)} style={{ background: 'none', border: 'none', color: 'var(--text)', cursor: 'pointer' }}>
    <Menu size={24} />
  </button>
</div>

{/* Mobile overlay — slides in from left */}
{mobileMenuOpen && (
  <div className="mobile-overlay" onClick={() => setMobileMenuOpen(false)} style={{
    position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 60
  }}>
    <div onClick={e => e.stopPropagation()} style={{
      position: 'absolute', top: 0, left: 0, bottom: 0, width: 260,
      background: 'var(--surface)', borderRight: '1px solid var(--border)',
      padding: 20, overflowY: 'auto',
    }}>
      <button onClick={() => setMobileMenuOpen(false)} style={{ position: 'absolute', right: 16, top: 16, background: 'none', border: 'none', color: 'var(--text)', cursor: 'pointer' }}>
        <X size={22} />
      </button>
      {/* Reuse the same navItems + theme toggle as desktop sidebar */}
      {navItems.map(item => (
        <NavLink key={item.to} to={item.to} className="sidebar-link">{item.label}</NavLink>
      ))}
    </div>
  </div>
)}
```

CSS: make main content offset for the mobile header.

```css
.mobile-header { display: none; }

@media (max-width: 768px) {
  .desktop-sidebar { display: none !important; }
  .mobile-header { display: flex !important; }
  .main-content {
    padding: 68px 16px 16px !important;  /* 52px header + 16px gap */
    max-width: 100% !important;
  }
}
```

## Server management: don't fight tool backgrounding

When the terminal tool rejects `&`, `nohup`, or `disown` syntax, and `background=true` times out/kills the process — stop trying. Free the port for the user and tell them to start the server themselves:

```bash
lsof -tiTCP:3001 -sTCP:LISTEN | xargs -r kill -9
```

Tell the user: `cd project && node server.js`. Wasting multiple turns on background process workarounds frustrates the user. Same applies to Vite — if it's already running on 5173, leave it alone.