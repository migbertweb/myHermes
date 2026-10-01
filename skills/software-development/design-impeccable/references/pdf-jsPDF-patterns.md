# jsPDF + autoTable patterns for Vite/ESM

## Import pattern (CRITICAL)
```js
// ❌ BROKEN — Vite tree-shakes side-effect imports
import 'jspdf-autotable';

// ✅ CORRECT — named import + function call
import autoTable from 'jspdf-autotable';
autoTable(doc, { ...opts });
```

Never use `doc.autoTable({...})` with ESM/Vite builds. Always use `autoTable(doc, {...})`.

## Color format (jsPDF 4.x)
```js
// ❌ BROKEN — arrays not accepted by encodeColorString
const T = { teal: [0, 168, 150] };
doc.setTextColor(T.teal);  // Invalid argument passed to jsPDF.f3

// ✅ CORRECT — hex strings
const T = { teal: '#00a896', ink: '#333333', gray: '#666666' };
doc.setTextColor(T.teal);
```

jsPDF 4.2+ `encodeColorString` (internal `f3`) rejects RGB arrays. Only hex strings (`'#333333'`) or 3 separate numbers (`51, 51, 51`) work.

## Table layout
- **Avoid `columnStyles` with fixed widths**: autoTable auto-sizes better. Fixed widths cause misalignment between headers and body.
- **Use `margin: { left: M, right: M }`** on every table for consistent alignment across multiple tables on the same page.
- **A4 usable width**: 210mm − (left + right margin). Column widths must sum ≤ this.
- **Foot rows for totals**: use `foot: [...]` instead of manual `doc.text()` positioning. Foot rows stay aligned with table columns.

## Logo loading (async)
```js
let _cache = null;
async function loadLogo() {
  if (_cache) return _cache;
  const img = await new Promise((res, rej) => {
    const i = new Image(); i.onload = () => res(i); i.onerror = rej;
    i.src = '/logo.png';
  });
  const c = document.createElement('canvas');
  c.width = img.width; c.height = img.height;
  c.getContext('2d').drawImage(img, 0, 0);
  return _cache = c.toDataURL('image/png');
}
// In drawHeader: doc.addImage(await loadLogo(), 'PNG', x, y, w, h);
```

## Defensive `lastAutoTable`
```js
// ❌ fragile — crashes if autoTable silently fails
y = doc.lastAutoTable.finalY + 8;

// ✅ guarded
y = (doc.lastAutoTable?.finalY || y + 20) + 8;
```

## Column width overflow → misleading error
When column widths exceed page width, autoTable issues a warning ("X units width could not fit page") and may corrupt internal state. The resulting `doc.lastAutoTable` can be undefined, cascading into a cryptic `setTextColor` / `f3` error far from the actual cause.

**Fix**: remove `columnStyles` and let autoTable auto-size. Use `margin: { left, right }` for alignment. If you must set widths, verify `sum(widths) <= pageWidth - leftMargin - rightMargin`.

## Font loading — `<link>` in HTML, never `@import` in CSS
```html
<!-- ✅ index.html -->
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
```
```css
/* ❌ BROKEN with Tailwind/PostCSS — @import must be first statement, Tailwind injects before it */
@import url('https://fonts.googleapis.com/css2?family=Outfit...');
```
PostCSS processes Tailwind first, injecting generated rules before the `@import`. This violates the CSS spec (`@import must precede all other statements`) and causes a warning loop.

## Compact layout for single-page PDFs
| Setting | Default | Compact |
|---------|---------|---------|
| `cellPadding` | 4-5 | 3 |
| `fontSize` tables | 8 | 7 |
| Section title gap | 7-10 | 5-6 |
| Client section y-step | 7 | 5 |
| Title-to-content gap | 6 | 5 |

Saves ~35mm total, keeping content on one A4 page even with 6+ stages and multiple line items.
