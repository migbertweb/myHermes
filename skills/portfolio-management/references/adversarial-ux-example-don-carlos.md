# Adversarial UX Test Example: Don Carlos vs migbertweb.xyz

## Persona

**Don Carlos Mendoza** — 59 años, dueño de Ferretería Mendoza, Caracas. Usa WhatsApp y YouTube nomás, su secretaria le maneja el correo. Quiere contratar un desarrollador para un sistema de inventario. Quemado: 3 freelancers le quedaron mal. Habla caraqueño ladillado, desconfiado. Si no ve resultados en 30 segundos cierra la página.

## Findings (Pragmatism Filter)

| # | Complaint | Filter | Rationale |
|---|-----------|--------|-----------|
| 1 | "Desenvolvedor" en portugués en hero | 🔴 REAL UX BUG | Ya corregido — hero role viene de i18n |
| 2 | Demasiada jerga técnica en bio | 🟡 VALID BUT LOW | Portafolio técnico, target espera jerga |
| 3 | "5+ anos" vs experiencia desde 2012 | 🔴 REAL UX BUG | Inconsistencia numérica resta confianza |
| 4 | Proyecto DevOps linkea al perfil de GH, no a proyecto concreto | 🟡 VALID BUT LOW | Preferible linkear a repo específico |
| 5 | 6 formas de contacto = parálisis | 🟢 FEATURE REQUEST | Simplificar a 1 CTA primario + iconos |
| 6 | Cargos no técnicos en experiencia | 🟡 VALID BUT LOW | Transparente pero malinterpretable |
| 7 | Stats "15+ tecnologías" suena negativo | ⚪ PERSONA NOISE | Cliente no técnico no entiende el señal |
| 8 | Videos de Linux no aportan al cliente | ⚪ PERSONA NOISE | Contenido para devs, esperable |
| 9 | Nombres de repos inentendibles | 🟢 FEATURE REQUEST | Agregar descripción en lenguaje de negocio |
| 10 | Contactar hace scroll al footer sin formulario | 🟡 VALID BUT LOW | Smooth scroll funciona, pero falta form rápido |

## Tickets generados

- **🔴 Ticket 1**: Inconsistencia años de experiencia — alinear hero stat con timeline real
- **🟢 Ticket 2**: Demasiadas opciones de contacto — reducir a 1 CTA primario
- **🟢 Ticket 3**: Descriptions de repos en lenguaje de negocio para no-devs

## Verdict

"Te contrataría si me explicas en cristiano qué vas a hacer por mi ferretería."
