#!/usr/bin/env python3
"""
Generate professional CV PDFs from Obsidian vault markdown source.

Usage:
    source /tmp/pdfvenv/bin/activate
    python scripts/gen-cv-pdfs.py

Reads: vault/Work-Freelancer/Upwork/cv-migbert-dev-{pt,es,en}.md
Writes: src/assets/Curriculum-{pt,es,en}.pdf
"""

import re, os, sys
from fpdf import FPDF

FONT_DIR = '/usr/share/fonts/TTF'
VAULT_BASE = '/home/migbert/vaults/principal/Work-Freelancer/Upwork'
ASSETS = '/home/migbert/proyectos/frontend/portfolio-react/src/assets'

def strip_frontmatter(text):
    return re.sub(r'^---\n.*?\n---\n', '', text, flags=re.DOTALL).strip()

def parse_md(md_text):
    blocks = []
    for line in md_text.split('\n'):
        s = line.strip()
        if not s:
            blocks.append(('spacer', ''))
        elif s.startswith('## ') or s.startswith('### '):
            level = 2 if s.startswith('## ') else 3
            blocks.append((f'h{level}', s.lstrip('#').strip()))
        elif s.startswith('|---') or s.startswith('|--'):
            continue
        elif s.startswith('|'):
            cells = [c.strip() for c in s.strip('|').split('|')]
            blocks.append(('table_row', cells))
        elif s.startswith('- '):
            t = re.sub(r'\*\*(.*?)\*\*', r'\1', s[2:])
            blocks.append(('bullet', t))
        elif s.startswith('*') and s.endswith('*'):
            t = re.sub(r'\*\*(.*?)\*\*', r'\1', s.strip('*').strip())
            if t: blocks.append(('italic', t))
        else:
            t = re.sub(r'\*\*(.*?)\*\*', r'\1', s)
            t = re.sub(r'_(\w+)_', r'\1', t)
            if t and not t.startswith('<!--'):
                blocks.append(('para', t))
    return blocks

class CV_FPDF(FPDF):
    def __init__(self, title):
        super().__init__('P', 'mm', 'A4')
        self.set_auto_page_break(auto=True, margin=20)
        self.add_font('DJV', '', os.path.join(FONT_DIR, 'DejaVuSans.ttf'))
        self.add_font('DJV', 'B', os.path.join(FONT_DIR, 'DejaVuSans-Bold.ttf'))
        self.add_font('DJV', 'I', os.path.join(FONT_DIR, 'DejaVuSans-Oblique.ttf'))

    def header(self):
        if self.page_no() > 1:
            self.set_font('DJV', 'I', 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 8, 'Migbert Yanez', align='R')
            self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('DJV', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Pagina {self.page_no()}/{{nb}}', align='C')

    def section_title(self, text):
        self.set_font('DJV', 'B', 13)
        self.set_text_color(0, 120, 160)
        self.ln(3)
        self.cell(0, 8, text)
        self.ln(1)
        self.set_draw_color(0, 180, 230)
        self.set_line_width(0.5)
        self.line(self.get_x(), self.get_y(), self.get_x() + 190, self.get_y())
        self.ln(5)

    def sub_title(self, text):
        self.set_font('DJV', 'B', 11)
        self.set_text_color(40, 40, 40)
        self.ln(2)
        self.cell(0, 6, text)
        self.ln(6)

    def body_text(self, text, size=10):
        self.set_font('DJV', '', size)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 5, text)
        self.ln(1)

    def bullet(self, text, size=10):
        self.set_font('DJV', '', size)
        self.set_text_color(50, 50, 50)
        self.cell(6, 5, chr(8226))
        self.multi_cell(0, 5, text)
        self.ln(0.5)

    def italic_line(self, text, size=10):
        self.set_font('DJV', 'I', size)
        self.set_text_color(80, 80, 80)
        self.cell(0, 5, text)
        self.ln(5)

    def table_row(self, cells, size=9):
        self.set_font('DJV', '', size)
        self.set_text_color(50, 50, 50)
        if len(cells) >= 3:
            self.cell(0, 5, f'{cells[0].strip()}  {cells[1].strip()}  {cells[2].strip()}')
        self.ln(5)

    def contact_line(self, text):
        self.set_font('DJV', '', 9)
        self.set_text_color(80, 80, 80)
        self.cell(0, 5, text)
        self.ln(4)

    def divider(self):
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.2)
        self.line(self.get_x(), self.get_y(), self.get_x() + 190, self.get_y())
        self.ln(6)

def build_pdf(md_text, lang_label):
    content = strip_frontmatter(md_text)
    pdf = CV_FPDF(f'{lang_label} CV')
    pdf.alias_nb_pages()
    blocks = parse_md(content)

    pdf.add_page()
    pdf.set_font('DJV', 'B', 26)
    pdf.set_text_color(15, 15, 15)
    pdf.cell(0, 12, 'MIGBERT YANEZ')
    pdf.ln(11)

    role_match = re.search(r'# (?:CV|Resume|Curriculo).*?[-–—] (.+)', md_text, re.IGNORECASE)
    if role_match:
        pdf.set_font('DJV', '', 14)
        pdf.set_text_color(0, 140, 190)
        pdf.cell(0, 8, role_match.group(1))
        pdf.ln(10)

    pdf.set_font('DJV', '', 9)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 5, 'Joinville, SC - Brasil  |  +55 47 99747-0887  |  migbertyanez@email.com')
    pdf.ln(4)
    pdf.cell(0, 5, 'github.com/migbertweb  |  migbertweb.xyz')
    pdf.ln(6)
    pdf.divider()

    for btype, data in blocks:
        if btype == 'spacer': continue
        elif btype == 'h2': pdf.section_title(data)
        elif btype == 'h3': pdf.sub_title(data)
        elif btype == 'para': pdf.body_text(data)
        elif btype == 'bullet': pdf.bullet(data)
        elif btype == 'italic': pdf.italic_line(data)
        elif btype == 'table_row': pdf.table_row(data)

    return pdf

if __name__ == '__main__':
    files = [
        ('cv-migbert-dev-pt.md', 'Curriculum-pt.pdf'),
        ('cv-migbert-dev-es.md', 'Curriculum-es.pdf'),
        ('cv-migbert-dev-en.md', 'Curriculum-en.pdf'),
    ]
    for src, dst in files:
        path = os.path.join(VAULT_BASE, src)
        print(f'Generating {dst}...', end=' ')
        with open(path) as f:
            pdf = build_pdf(f.read(), dst.replace('.pdf','').replace('Curriculum-',''))
        pdf.output(os.path.join(ASSETS, dst))
        print(f'{os.path.getsize(os.path.join(ASSETS, dst))/1024:.0f} KB OK')
