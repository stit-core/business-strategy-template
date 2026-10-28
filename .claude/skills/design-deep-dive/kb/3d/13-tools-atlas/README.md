# 13-tools-atlas — атлас инструментов

Справочник «можно ли этим пользоваться»: версия, лицензия и её ограничения, живость проекта, работает ли без окна и
без ключей, ценность для агента-дизайнера. Откуда взята запись — колонка `source`: `manual`, `live:<площадка>` (npm, PyPI,
GitHub/ungh.cc, Forgejo projects.blender.org, extensions.blender.org), `cache:repos`, `cache:registry`; день сбора — колонка `collected`.

## Файлы

| Файл | Что внутри |
|---|---|
| `01-blender-addons-extensions.md` | встроенные модули Blender 5.2.2, платформа extensions.blender.org, сторонние аддоны (RetopoFlow, BlenderKit, MPFB…), аддоны-мосты к ИИ-генераторам, сторона аддона MCP |
| `02-web-runtime-libraries.md` | движки веб-3D (three, R3F, Babylon, PlayCanvas, model-viewer, Needle, Spline…), анимация/прокрутка (GSAP, Lenis, Theatre.js), сплаты для веба, лёгкие/нишевые библиотеки, peer-совместимость с three r186 |
| `03-pipeline-cli-services.md` | CLI glTF/текстурного конвейера (gltf-transform, gltfpack, toktx, валидатор), MCP-серверы для Blender (14 живых + сравнение угроз), библиотеки 3D-ассетов, сервисы-генераторы 3D, `bpy`/`fake-bpy-module`, инструменты изоляции |
| `atlas.tsv` | машиночитаемая таблица — 180 записей, 16 колонок (name…category…version…license…status…notes) |

## Выжимка папки

1. Руками в атласе заполнены только лицензии, их ограничения и «ценность для агента» (остальное — живые запросы с кэшем).
2. GitHub REST API — последний рубеж после ungh.cc и собственного кэша (лимит 60 запросов/час без токена, общий на
   всю машину).
3. **Bool Tool, F2, Bsurfaces и LoopTools Relax/Curve/GStretch не входят в ядро Blender 5.2.2** — отдельные GPL-расширения с
   extensions.blender.org; LoopTools Flatten/Circle/Space встроены родными `mesh.flatten/circularize/space_edge_loops_evenly` (X/02).
4. **mcp-for-blender 2.0.3 — 3 неисправленные CVE** (10661, 10662, 10688), не 2, как считала волна 1; официальный
   Blender Lab MCP 1.0.3 — путь без окна и без известных CVE, но без полноценной песочницы.
5. Платных Blender-аддонов на extensions.blender.org нет (площадка требует GPL-совместимую лицензию) — Hard Ops,
   BoxCutter, MESHmachine, RetopoFlow распространяются отдельно.
6. Needle Engine, Theatre.js studio, Hunyuan3D-2, Sketchfab Store — четыре явно ограниченные лицензии, проверенные
   этой волной первоисточником (не по памяти).
7. Для «можно ли взять ассет» — сначала `03-pipeline-cli-services.md §6` (правило «лицензия → действие» —
   `10-ai-3d-generation-assets/03 §1.1`, не дублируется).
8. Статус (`живой`/`заморожен`/`заброшен`) — автоматически по дате последней активности (`>270`/`>540` дней), либо
   вручную, если дата недоступна (сервисы без публичного реестра версий).
9. Полная методика сбора, проверка 5 спорных лицензий и живость GitHub-лимита — `99-raw/experiments/L/00-atlas-collect/README.md`.
