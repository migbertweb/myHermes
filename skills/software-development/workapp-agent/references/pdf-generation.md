# jsPDF Lessons — WorkApp PDF Generation

Condensed from 18+ PRs of fixes. Every jsPDF pitfall hit in production.

## Import (Vite/ESM)
```js
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable'; // NUNCA side-effect import
// Usar: autoTable(doc, opts) — NO doc.autoTable(opts)
```

## Colors — use HEX STRINGS, arrays are broken in jsPDF 4.2.1
```js
// jsPDF 4.2.1 encodeColorString (f3) NO acepta arrays RGB
// ✅ Hex strings — único formato 100% fiable
const T = { teal: '#00a896', ink: '#333333', gray: '#666666', light: '#e0e0e0', white: '#ffffff', red: '#dc3545', green: '#00a896' };
doc.setTextColor(T.ink);
doc.setFillColor(T.teal);
doc.setDrawColor(T.light);

// ❌ Arrays — Error: "Invalid argument passed to jsPDF.f3"
const T_bad = { teal: [0, 168, 150] };
doc.setTextColor(T_bad.teal); // ROMPE

// ❌ Spread de array — mismo error
doc.setTextColor(...[51, 51, 51]); // ROMPE
```

## Page layout
- A4: 210×297mm
- Margin: 20mm each side → usable width: 170mm
- **NO usar `columnStyles` con anchos fijos** — deja que autoTable auto-size las columnas. `columnStyles` causa desalineación entre headers y datos.
- Usar `margin: { left: 20, right: 20 }` en TODAS las tablas para alineación consistente entre tablas consecutivas.
- Header `'#'` (1 char) no `'No'` (se rompe en "N"+"o" en columnas angostas).

## Tablas: patrón correcto (auto-size + foot rows)
```js
// ✅ CORRECTO — sin columnStyles, totals en foot, margin explícito
autoTable(doc, {
  startY: y,
  head: [['#', 'Descripción', 'Precio', 'Cant (h)', 'Total']],
  body,
  foot: [
    [{ content: 'Subtotal', colSpan: 4, styles: { halign: 'right', fontStyle: 'bold' } },
     { content: money(subtotal), styles: { halign: 'right', fontStyle: 'bold' } }],
    [{ content: 'TOTAL', colSpan: 4, styles: { halign: 'right', fontStyle: 'bold', fontSize: 10 } },
     { content: money(total), styles: { halign: 'right', fontStyle: 'bold', fontSize: 10 } }],
  ],
  theme: 'plain',
  margin: { left: 20, right: 20 },
  styles: { fontSize: 8, cellPadding: 4, textColor: '#333333' },
  headStyles: { textColor: '#00a896', fontStyle: 'bold', fillColor: '#ffffff' },
  bodyStyles: { lineColor: '#e0e0e0', lineWidth: 0.2 },
  footStyles: { fillColor: '#ffffff', lineWidth: 0 },
});

// ❌ MAL — columnStyles + texto separado para totales
autoTable(doc, {
  columnStyles: { 0: { cellWidth: 10 }, 1: { cellWidth: 80 }, ... }, // DESALINEA
});
// ...y después:
doc.text('Total', sx, y); // texto suelto, nunca alineado con la tabla
```

## Table Y-position guard
```js
// ALWAYS guard lastAutoTable — puede ser undefined si la tabla falla
y = (doc.lastAutoTable?.finalY || y + 20) + offset;
```

## Presupuesto: resumen financiero como autoTable
NO uses `doc.text()` manual. Convertilo en tabla:
```js
const summaryBody = [
  [{ content: 'Presupuesto base', styles: { fontStyle: 'bold' } },
   { content: money(budget), styles: { halign: 'right' } }],
  [{ content: 'TOTAL PRESUPUESTO', styles: { fontStyle: 'bold', fontSize: 10 } },
   { content: money(total), styles: { halign: 'right', fontStyle: 'bold', fontSize: 10, textColor: '#00a896' } }],
];
autoTable(doc, {
  startY: y, body: summaryBody, theme: 'plain',
  margin: { left: 20, right: 20 }, // mismo margin que las tablas anteriores → alineación perfecta
  styles: { fontSize: 8, cellPadding: 4 }, bodyStyles: { lineColor: '#e0e0e0', lineWidth: 0.2 },
});
```

## Logo loading (async + canvas)
```js
let _logoDataUrl = null;
async function loadLogo() {
  if (_logoDataUrl) return _logoDataUrl;
  const img = await new Promise((resolve, reject) => {
    const i = new Image();
    i.onload = () => resolve(i);
    i.onerror = reject;
    i.src = '/logo.png'; // servido como estático
  });
  const c = document.createElement('canvas');
  c.width = img.width; c.height = img.height;
  c.getContext('2d').drawImage(img, 0, 0);
  _logoDataUrl = c.toDataURL('image/png');
  return _logoDataUrl;
}
// Uso: const url = await loadLogo(); doc.addImage(url, 'PNG', x, y, w, h);
// Requiere: async/await en drawHeader() y en TODAS las funciones que la llamen
```

## Invoice with line items
```js
// Fetch items before generating — el botón debe ser async
const items = await api.getLineItems(inv.project_id);
await downloadInvoicePDF(inv, project, items);

// Calculate subtotal from real items
const lineSubtotal = lineItems.reduce((s, i) => s + (i.amount || 0), 0);
if (Math.abs(lineSubtotal - invoice.amount) > 0.01) {
  // Show "Ajuste" line in foot
}
```

## Styling (Migbert Yanez brand)
- Teal accent: `#00a896`, Ink: `#333333`, Gray: `#666666`, Light: `#e0e0e0`
- Company: "Migbert Yanez · Desarrollo Freelance"
- Contact: Brasil, +55 47 99747-0887, migbertyanez@email.com
- Payment: Transferencia bancaria · Pago móvil · Revolut
  - Banco: Mercado Pago / Nubank · Revolut: @migbertyanez
  - Plazo: 15 días
- FACTURA: 24pt bold teal (palabra corta, puede ser grande)
- PRESUPUESTO: 13pt teal como ETIQUETA — el nombre del proyecto (12pt bold negro) es el título real
- Fecha en presupuesto: 8pt gris debajo del título
- Footer: línea de firma + formas geométricas decorativas (triángulos teal/negro, pequeños, sin tapar texto)
- Notas: 2 columnas compactas (<50% del footer)
