---
name: cv-management
description: "Gestion del CV de Migbert: actualizar, generar resumenes y mantener versiones."
usage: "Cuando el usuario pida actualizar su CV, crear una version breve/larga, extraer skills, o vincularlo con alguna postulacion."
---

# Gestion de CV

## Rutas
- Origen: `/home/migbert/Documentos/curriculo-profesiona.txt`
- Obsidian: `/home/migbert/vaults/principal/currículo-profissional.md`
- Mnemosyne: skills y experiencia laboral almacenados en memoria durable

## Acciones
1. Leer el archivo de origen cuando sea necesario re-sincronizar.
2. Actualizar `currículo-profissional.md` ante cambios confirmados por el usuario.
3. Extraer secciones especificas para postulaciones o cover letters.
4. Alinear contenido con Mnemosyne cuando se agreguen skills o experiencias nuevas.

## PDF Generation (portfolio)

Source CVs están en el vault: `Work-Freelancer/Upwork/cv-migbert-dev-{pt,es,en}.md`
Los PDFs del portfolio están en `portfolio-react/src/assets/Curriculum-{pt,es,en}.pdf`

Para regenerar: usar el skill `portfolio-management` y su script `scripts/gen-cv-pdfs.py`.
Requisito: `pip install fpdf2 markdown` en un venv.

```bash
source /tmp/pdfvenv/bin/activate
python ~/.hermes/skills/portfolio-management/scripts/gen-cv-pdfs.py
cd /home/migbert/proyectos/frontend/portfolio-react && npm run build
git add src/assets/Curriculum-*.pdf && git commit -m "fix: atualiza curriculos PDF"
git push
```

## Criterios
- No borrar historia laboral sin confirmacion explicita.
- Generar siempre la version portugues/ingles o espanol solo cuando se pida.
- Mantener consistencia entre Obsidian, Mnemosyne y este skill.
