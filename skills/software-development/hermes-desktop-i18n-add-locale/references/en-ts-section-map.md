# Mapa de secciones de `en.ts` (referencia maestra para traducción)

`apps/desktop/src/i18n/en.ts` tiene ~2,529 líneas. Es la fuente de todas las claves.
Cuando delegues la creación/finalización del archivo de traducción a un subagent,
pásale este mapa en lugar de leer `en.ts` completo en tu contexto.

## Claves top-level y sub-secciones

- **common** — ~45 strings (apply, save, cancel, delete, copy, tryHint fn, on/off…)
- **fileMenu** — reveal*, copyPath, rename, delete, deleteTitle fn
- **boot** — ready, desktopBootFailedWithMessage fn, steps{}, errors{}, failure{}
- **notifications** — region, hide/show/more fns, clearAll, errors{}, voice{}, native{}
- **remoteDisplayBanner** — message fn
- **titlebar** — hideSidebar, search, openSettings, openStarmap, openKeybinds…
- **keybinds** — title, rebind, categories{}, actions{} (50+ claves 'keybinds.*' / 'nav.*' / 'session.*' / 'view.*' / 'profile.*' / 'composer.*')
- **language** — label, description, saving, switchTo, searchPlaceholder, noResults
- **settings**
  - nav{}, notifications{kinds{}}, sections{}, searchPlaceholder{}, modeOptions{}
  - appearance{pet{}}, about{}, config{}, credentials{}, envActions{}
  - gateway{} (grande: cloud*, remote*, auth*, token*…), keys{}, mcp{} (grande: catalog*, status*…)
  - model{}, providers{}, sessions{}, toolsets{}
  - ⚠️ `fieldLabels` y `fieldDescriptions` se HEREDAN vía `defineLocale()` — NO incluir
- **skills** — tab*, search*, hub{trust{}, verdict*, policy*} (grande)
- **starmap** — title, subtitle fn, share*, import*
- **agents** — close, title, running/failed/done, workers*, *Count fns
- **commandCenter** — pets{}, generatePet{}, installTheme{}, sections{}, sectionDescriptions{}, nav{}, sectionEntries{}, maintenance{} (grande)
- **messaging** — states{}, fieldCopy{TELEGRAM_*, DISCORD_*, BLUEBUBBLES_*, MATTERMOST_*, QQ_*, QQBOT_*, SLACK_*, MATRIX_*, SIGNAL_*, WHATSAPP_*} (grande), platformIntro{}
- **profiles** — nameHint, createDesc, clone*, soul*, delete*, rename*
- **cron** — states{}, deliveryLabels{}, scheduleLabels{}, scheduleHints{}, days{}, *Title/*Desc fns
- **artifacts** — tab*, items*, col*, kind*
- **sidebar** — nav{}, projects{} (grande), row{}
- **composer** — placeholders[], commandDescs{}, hotkeyDescs{}, snippets{codeReview,implementationPlan,explainThis}
- **statusStack** — background, subagents, todos fns, coding{} (grande: git/review/commit)
- **updates** — stages{}, applyStatus{}
- **install** — stageStates{}, failedDesc, progress fn
- **onboarding** — apiKeyOptions{}, flowSubtitles{}, *SignIn fns
- **modelPicker** — title, search, pro/free, priceTitle
- **modelVisibility** — title, search
- **shell** — modelMenu{}, modelOptions{}, gatewayMenu{}, statusbar{contextUsagePanel{}}
- **rightSidebar** — files, terminal, tree*, preview*
- **preview** — console{}, web{} (grande)
- **assistant** — thread{}, approval{}, clarify{}, tool{actions{}, prefixes{}, titleTemplates{}, titles{browser_*, clarify, cronjob, edit_file, execute_code, image_generate, list_files, patch, read_file, search_files, session_search_recall, terminal, todo, vision_analyze, web_extract, web_search, write_file} con done/pending/pendingAction}
- **prompts** — sudo*, secret*
- **desktop** — yolo*, profile*, branch*, image*, handoff{}
- **errors** — genericFailure, boundary*
- **ui** — search{}, pagination{}, sidebar{}

## Reglas de traducción (pasar al subagent)

- Español neutro latino, tuteo. "Guardar" no "Guardad"; "Configuración" no "Ajustes".
- NO traducir: Hermes, Hermes Desktop, proveedores (OpenAI, Anthropic, Nous, OpenRouter, Gemini, xAI, Fireworks, GitHub, Discord, Slack, Telegram, Matrix, Signal, WhatsApp, QQ, QQBot, Mattermost, BlueBubbles), MCP, OAuth, PKCE, IPC, Gateway, Starmap, SOUL.md, MEMORY.md, USER.md, IDEA.md, config.yaml, YOLO, PR, API, URL, CLI, JSON, MIME, Vite, React, gh.
- Funciones flecha: mantener forma. `deleteTitle: name => \`¿Eliminar ${name}?\``
- `defineLocale()` hereda claves faltantes del inglés — puede ser parcial, pero para un locale completo traducir todo lo visible.
