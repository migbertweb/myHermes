# PDF generation with jsPDF + jspdf-autotable

## ESM Import (CRITICAL — Vite tree-shaking)

The side-effect import `import 'jspdf-autotable'` does NOT work with Vite/ESM bundlers.
The prototype extension gets tree-shaken and `doc.autoTable` is undefined at runtime.

```js
// ❌ BROKEN in Vite
import 'jspdf-autotable';
doc.autoTable({ ... });

// ✅ CORRECT for ESM/Vite
import autoTable from 'jspdf-autotable';
autoTable(doc, { ... });
```

`doc.lastAutoTable.finalY` still works after calling `autoTable(doc, opts)` — the function sets it internally.

## Loading external images

jsPDF cannot load images from URL directly. Pattern for embedding logo:

```js
let logoCache = null;

async function getLogo() {
  if (logoCache) return logoCache;
  const img = await new Promise((resolve, reject) => {
    const i = new Image();
    i.onload = () => resolve(i);
    i.onerror = reject;
    i.src = '/logo.png'; // must be in public/
  });
  const canvas = document.createElement('canvas');
  canvas.width = img.width;
  canvas.height = img.height;
  canvas.getContext('2d').drawImage(img, 0, 0);
  logoCache = canvas.toDataURL('image/png');
  return logoCache;
}

// In PDF function (must be async):
const dataUrl = await getLogo();
doc.addImage(dataUrl, 'PNG', x, y, w, h);
```

- Cache the data URL for subsequent PDFs (instant)
- Provide text fallback if image load fails
- Images must be in `client/public/` (served by Express static middleware)

## Design tips (teal corporate style)

| Element | Style |
|---------|-------|
| Header | Logo 16x16mm left, company name bold 15pt, tagline 7pt gray |
| Contact | Right-aligned, 8pt, location + phone + email |
| Title | Document type 13pt teal label, project name 12pt bold ink |
| Tables | `theme: 'plain'`, white header with teal text, light gray dividers |
| Summary | Right-aligned below table, bold total with line separator |
| Footer | Signature line left, date right, "Gracias" message, decorative triangles |
| Notes | Compact 2-column, max 3 lines, <50% of footer height |

## Docker persistence for SQLite

DB file must live inside a mounted volume, not at container root:

```js
// db.js default path — inside volume mount
const DB_PATH = process.env.DB_PATH || path.join(__dirname, 'data', 'workapp.db');

// bootstrap() must create directory at runtime
if (!fs.existsSync(path.dirname(DB_PATH))) {
  fs.mkdirSync(path.dirname(DB_PATH), { recursive: true });
}
```

Dockerfile needs `COPY` for ALL server-side modules (db.js, auth.js, notify.js, activity.js, etc).
Missing modules → `ERR_MODULE_NOT_FOUND` at deploy time.
