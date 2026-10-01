# Client-side PDF Generation with jsPDF

Patterns for generating PDFs in the browser (Vite/React) using jsPDF + jspdf-autotable.

## Dependencies

```json
"jspdf": "^4.2.1",
"jspdf-autotable": "^5.0.8"
```

## ESM Import (critical)

Side-effect import does NOT work with Vite tree-shaking:

```js
// BROKEN — Vite strips the side-effect
import 'jspdf-autotable';

// WORKS
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
```

## Usage Pattern

```js
const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });

autoTable(doc, {
  startY: 60,
  head: [['Col1', 'Col2']],
  body: [[val1, val2]],
  theme: 'plain',
  styles: { fontSize: 8, cellPadding: 4, textColor: [51, 51, 51] },
  headStyles: { textColor: [0, 168, 150], fontStyle: 'bold', fillColor: [255, 255, 255] },
  bodyStyles: { lineColor: [224, 224, 224], lineWidth: 0.2 },
});

// Guard against undefined result
const finalY = doc.lastAutoTable?.finalY || startY + 40;
```

## Common Errors

### `i.autoTable is not a function`
→ Wrong import. Use `import autoTable from 'jspdf-autotable'` and call `autoTable(doc, opts)`.

### `Invalid argument passed to jsPDF.f3`
→ A value passed to `doc.text()` is NaN or undefined. Usually caused by `doc.lastAutoTable.finalY` being undefined after a failed autoTable call. Always guard: `(doc.lastAutoTable?.finalY || fallback) + offset`.

### Logo loading for PDF header
Load from static path (e.g., `/logo.png`) via Canvas → data URL:

```js
let _logoDataUrl = null;
async function loadLogo() {
  if (_logoDataUrl) return _logoDataUrl;
  const img = await new Promise((resolve, reject) => {
    const i = new Image();
    i.onload = () => resolve(i);
    i.onerror = reject;
    i.src = '/logo.png';
  });
  const canvas = document.createElement('canvas');
  canvas.width = img.width;
  canvas.height = img.height;
  canvas.getContext('2d').drawImage(img, 0, 0);
  _logoDataUrl = canvas.toDataURL('image/png');
  return _logoDataUrl;
}

// Usage in async function:
const logoUrl = await loadLogo();
if (logoUrl) doc.addImage(logoUrl, 'PNG', x, y, w, h);
```

## Design Tips for Professional PDFs

- Teal corporate palette: `teal: [0, 168, 150], ink: [51, 51, 51], gray: [102, 102, 102], light: [224, 224, 224]`
- Header: slim accent bar at top, logo left, contact info right, thin separator line
- Tables: `theme: 'plain'`, white header with colored text, light gray row dividers
- Summary: right-aligned below table, total in bold with separator line
- Footer: signature line, decorative shapes (triangles) at bottom-right, thank-you message
- Font: Helvetica throughout (bold for headings, normal for body, italic for notes)
