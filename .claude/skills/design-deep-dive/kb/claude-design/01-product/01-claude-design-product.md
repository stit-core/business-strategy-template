# Claude Design: продукт на 25.09.2026

Снимок: 25.09.2026 · источников: 33: help center — 11 статей (Claude Design, дизайн-системы, два админ-гайда, артефакты, шаринг, release notes,
модели и effort, модели по умолчанию, доступ к моделям, Fable на тарифах; обновлены 02–24.09.2026); privacy center — 4 статьи;
anthropic.com — анонс Claude Design (17.04), 9 анонсов моделей, страница вебинара; claude.com — страница продукта, страница
артефактов, 3 поста блога (17.06, 24.07, 16.09), страница плагина Design; code.claude.com — документация артефактов; плюс 3 файла
соседних баз; ролики заказчика — ссылками с таймкодом.
Главные ограничения: Claude Design не запускался (решение оркестратора) — всё о качестве, скорости, реальном расходе лимитов и
поведении интерфейса `[не проверено]`; help center читается без JavaScript (`fetch.py`, таблицы — отдельным разбором HTML), даты
статей — `dateModified`; **переключатель модели в Claude Design официально есть, но модель по умолчанию и список доступных моделей
не названы** (§2).

## Выжимка для агента

1. Знай: с 16.09.2026 Claude Design — не только приложение claude.ai/design, а **шаблон артефакта Design** в любом чате, во вкладке
   Artifacts и в Claude Code (команда `/design` — с 17.06); standalone claude.ai/design работает дальше со своим тумблером.
   `[документация]` → §1, §11
2. Знай: статус — **beta на платных тарифах** (Pro, Max, Team, Enterprise; на старте 17.04 — research preview); на Enterprise
   выключен по умолчанию. Free — нет: так пишут help center, страница продукта и блог 16.09; фраза release notes 16.09 «every plan,
   including Free» относится к артефактам вообще. `[документация]` `[спорно]` → §1
3. Знай: в Claude Design **есть переключатель модели** (Enterprise-статьи help center 21–23.09 ставят его в один ряд с чатом и Claude
   Code; Fable 5 / 5.1 доступны «in Claude Design»), но **модель по умолчанию и набор моделей для Claude Design не названы**; на
   старте — Opus 4.7. «Opus 5.5 в Claude Design» официально не подтверждён. `[документация]` `[спорно]` → §2
4. Делай: перед работой выбирай модель явно — Opus 5.5 с effort High или Extra high (входит в лимиты подписки); Fable 5.1 — только на
   Max (≤ 50 % недельного лимита) или за usage credits (на Pro — только за credits). Модель и effort пиши в протокол. `[документация]`
   `[не проверено]` → §2, §7
5. Делай: **сначала дизайн-система, потом экраны**. Вендор: без неё — «functional but generic output». `[документация]` → §4, §9
6. Делай: промт = **goal + layout + content + audience**; Claude сам задаёт уточняющие вопросы. `[документация]` → §9
7. Делай: способ правки выбирай по размеру: chat — структура и новые разделы, inline comments — один компонент, прямая правка на
   холсте — быстрые визуальные сдвиги. `[документация]` → §3
8. Не делай: не полагайся только на инлайн-комментарии — известный сбой «comments can disappear before Claude reads them»; важную
   правку дублируй в чат. `[документация]` → §3, §10
9. Делай: перед сменой направления пиши «Save what we have and try a completely different approach.» — истории версий нет.
   `[документация]` → §3, §10
10. Делай: проси 2–3 варианта, когда направление не ясно; проси ревью на доступность, контраст, иерархию. `[документация]` → §3, §9
11. Знай: экспорт — .zip, PDF, PPTX, standalone HTML, Google Slides (только standalone), 15 внешних сервисов (Canva, Lovable, v0,
    Vercel, Netlify, Replit, Miro и др.) и handoff: «Send to local coding agent» / «Send to Claude Code Web». `[документация]` → §6
12. Знай: из Claude Code дизайн-систему заводит `/design-sync` (React-компоненты и токены), а `/design` создаёт, правит, импортирует
    дизайн; в терминале Claude даёт ссылку на веб. Детали моста — `02-claude-code-bridge/`. `[документация]` → §4, §6
13. Знай: лимиты **общие** с чатом и Claude Code с 17.06.2026 (раньше — свой недельный лимит); большие кодовые базы, полные деки и
    много итераций расходуют больше; при исчерпании — стоп до сброса или usage credits. Прямые правки на холсте, по словам автора
    продукта, «use no tokens» — финальные мелочи делай руками. `[документация]` `[мнение вендора]` → §7
14. Не делай: не подключай очень большой репозиторий в браузерном Claude Design — вендор советует делать это из Claude Code.
    `[документация]` → §5, §10
15. Знай: дизайн приватен по умолчанию; права view / comment / edit; открыть артефакт (кроме legacy) можно только с аккаунтом
    Claude. `[документация]` → §6
16. Знай: превью — sandboxed iframe на отдельном домене Anthropic, доступ по короткоживущим подписанным токенам с перепроверкой
    прав при каждом открытии. `[документация]` → §8
17. Знай: у standalone Claude Design нет audit logs и data residency; организации с CMEK/ZDR/HIPAA не получают новые артефакты
    (шаблоны, дизайн-системы). `[документация]` → §8
18. Делай: дизайн-систему проверяй тестовым проектом («Create a landing page for [your product].») и только потом публикуй.
    `[документация]` → §4
19. Знай: на iOS/Android можно только попросить дизайн и посмотреть; шаблоны, холст, шаринг — веб и десктоп. `[документация]` → §1
20. Знай: «2.0» и «3.0» — названия блогеров; официальных версий нет. Вехи: 17.04 запуск (research preview, Opus 4.7); **17.06**
    новый редактор, переписанный импорт дизайн-систем, `/design-sync` и `/design`, общий лимит (это и есть «2.0» из роликов); 16.09
    шаблон артефактов в любом чате, отдельные Claude Slides. `[документация]` → §11
21. Не делай: не проси логотипы и фотореалистичные картинки — «Claude Design doesn't have an image model and isn't built for image
    generation»; приноси свои ассеты. `[мнение вендора]` → §3, §9
22. Знай: вендор отдаёт Claude Design раннюю разведку — вайрфреймы и много вариантов («Ask for ten options, then remix»), а продакшн —
    Claude Code: «if you're shipping production software, stick with Claude Code». Порядок этапов скилла — `../../../references/phases.md`.
    `[мнение вендора]` → §3, §9

## 1. Что это, статус, тарифы, где живёт

**Определение (help center, 23.09.2026):** «Claude Design lets you create designs, interactive prototypes, one-pagers, and other visual
work by chatting with Claude. It's one of the templates you can start an artifact from, so you can use it in any chat, in Claude Code,
and from the Artifacts tab, with on-canvas editing and your design system included.» `[документация]`
Продукт Anthropic Labs; запуск 17.04.2026 вместе с Opus 4.7 (release notes 17.04). Презентации с 16.09 вынесены в отдельный шаблон:
«Presentations now have their own tool, Claude Slides.» (admin guide, 23.09) `[документация]`

| Вопрос | Ответ (дата) | Метка |
|---|---|---|
| Статус | 17.04: «research preview»; 23.09: «available in beta on Pro, Max, Team, and Enterprise plans» | `[документация]` |
| По умолчанию | «on by default on Pro, Max, and Team plans. On Enterprise plans, it's off by default until an owner turns it on in Organization settings > Artifacts» (23.09) | `[документация]` |
| Free | **За «только платные»** (4 источника): What are artifacts (24.09) — «Templates (Claude Design, Claude Slides, and Claude Docs) are in beta on paid plans only», у Free в таблице нет «Start from a template»; claude.com/product/design — «Claude Design is included in all paid plans»; claude.com/features/artifacts — «available in beta on paid plans»; блог 16.09 — «All three are in beta on paid plans». **Против** (1): release notes 16.09 — «Artifacts, including Claude Design, Claude Slides, and Claude Docs, are available on every plan, including Free». Позиция базы: на Free есть артефакты в чате, шаблона Design нет | `[спорно]` → позиция `[документация]` |
| Две точки входа | шаблон Design (чат, вкладка Artifacts, Claude Code) и standalone claude.ai/design — «a separate product from the Design template … Turning one on doesn't turn on the other. Users' existing projects stay at claude.ai/design and also appear in the Artifacts tab.» | `[документация]` |
| Облака-посредники | «Artifacts aren't available through third-party cloud platforms.» (Bedrock, Vertex, Foundry — нет) | `[документация]` |
| Регионы | отдельного списка стран для Claude Design нет; «Claude Design doesn't currently support data residency requirements.» | `[документация]` |
| Предусловие | «Artifacts require Cloud code execution and file creation to be turned on in Settings > Capabilities» (Free/Pro/Max) или Organization settings > Capabilities (Team/Ent) | `[документация]` |

**Где работает (Get started, 23.09.2026)** `[документация]`:

| Поверхность | Что можно |
|---|---|
| Чат (веб, десктоп) | «Ask Claude for a design, like "Make a one-pager from this proposal" or "Mock up the onboarding flow we just discussed."» Дизайн строится рядом с разговором; или **Output > Design** в поле ввода |
| Вкладка Artifacts | выбрать шаблон Design; все артефакты сохраняются там же |
| Claude Code | «Ask Claude to turn your idea into a design, or use /design to create, edit, and sync designs, on desktop or in the terminal.» В терминале — «Claude gives you a link to open it on the web» (What are artifacts, 24.09) |
| iOS, Android | попросить дизайн и посмотреть в Artifacts; «To start from a template, edit on the canvas, or change sharing settings, use Claude on web or desktop.» |
| claude.ai/design | «The standalone experience keeps working, and your existing projects stay where they are.» Только здесь — экспорт в Google Slides, аналитика DAU/WAU/MAU |

**Из Claude Code — продуктово** (code.claude.com/docs/en/artifacts, без даты, прочитано 25.09; подробно — `02-claude-code-bridge/`) `[документация]`:
«To mock up a UI, a screen flow, a landing page, or a poster rather than build a page, run `/design` with a brief. Claude drafts the
design as artboards on one canvas and publishes the canvas as a Design artifact.» Пример вендора: `/design a settings screen for a
mobile banking app`. «Open the published artifact in a desktop browser to review the artboards. Select an element on an artboard and
change it, and your edits save automatically. You can export each artboard as PNG or PDF.» Условия: Claude Code **v2.1.265+** (у
заказчика 2.1.281 `[проверено]`), тарифы Pro, Max, Team, Enterprise, сеанс с входом через `/login` — «Sessions using an API key,
gateway token, or cloud-provider credential cannot publish»; не на Bedrock, Vertex, Foundry; не при CMEK, HIPAA, ZDR; «Off by default in
Agent SDK, GitHub Action, and MCP-server contexts». Обычные артефакты Claude Code строит со встроенным design skill, который сначала
ищет дизайн-систему проекта (токены в `CLAUDE.md` или theme-файле); приоритет — «your design system as higher precedence than its own
choices, and your prompt as higher precedence than both».

**Админ-настройки (Team, Enterprise; admin guides, 23.09.2026)** `[документация]`:
- Шаблон Design: Organization settings > Artifacts > Templates (каждый шаблон — свой тумблер). Standalone: Organization settings >
  Claude Design > «Enable for your organization» под «Claude Design [standalone]».
- Enterprise, custom roles — отдельные capabilities: Artifacts, Design, Design systems, Docs, Slides и «Claude Design [standalone] |
  Access to standalone Claude Design at claude.ai/design». Орг-тумблер — главный: «If a feature is off at the organization level, no
  custom role can grant access to it.»
- Право **Claude Design Admin** (Product admin → «Can manage»): публикация дизайн-системы, выбор дефолтной, удаление. Не выдано
  никому — эти действия доступны всем с доступом к дизайн-системам.
- Artifact presence (кто ещё открыл артефакт) — включено по умолчанию на Team/Enterprise.
- Рекомендованный rollout — 4 фазы: 2–4 дизайнера строят дизайн-систему → вся дизайн-команда → продакты и UX → вся организация.

**Что делает (типы выходов).** Help center (23–24.09): «Visuals, mockups, prototypes, one-pagers, and landing pages, built with your
design system»; «on-brand designs, prototypes, and interactive microsites»; шаблон Design — «Lay out screens, flows, and graphics as
artboards they can edit by hand». Анонс 17.04 (сценарии команд): realistic prototypes, product wireframes and mockups, design
explorations, pitch decks (теперь — Claude Slides), marketing collateral (landing pages, social media assets, campaign visuals),
«Frontier design: Anyone can build code-powered prototypes with voice, video, shaders, 3D and built-in AI.» `[документация]`
`[мнение вендора]` для сценариев. По ролику 13.08 в standalone — «больше десятка» шаблонов (магазин, презентации, документ, резюме,
3D, HTML-письмо, флаер) `[V:uS7gmBLeUV0 01:18]` `[практика]`; ограничение 3D — «Сложную и технически точную модель не вывезет»
`[V:uS7gmBLeUV0 13:21]` `[мнение]`.

## 2. Модель и усилие (effort)

**Итог на 25.09.2026:** в Claude Design **есть переключатель модели** — Enterprise-статьи help center (21–23.09) ставят Claude Design
в один ряд с чатом, Cowork и Claude Code, а Fable 5 / 5.1 официально доступны «in Claude Design». **Какая модель стоит по умолчанию
и какие модели доступны именно в Claude Design, документация не пишет**; на старте (17.04) — Opus 4.7. «Opus 5.5 в Claude Design»
ни одним официальным текстом не подтверждён. `[документация]` `[спорно]`

| Факт | Цитата (источник, дата) | Метка |
|---|---|---|
| Модель на старте | «Claude Design is powered by our most capable vision model, Claude Opus 4.7» (анонс, 17.04) | `[документация]` |
| Переключатель модели | «When you set or change a default model, it replaces the model currently selected in each member's model picker. New conversations in chat, Cowork, Claude Code, Claude for Office, Claude Design, and Claude Science then start on the model you've chosen.» (15330088, 21.09) | `[документация]` |
| Набор моделей зависит от продукта | «Not all models are available in every product. If the selected model is not available in the product, Anthropic's recommendation is used as default.» (15330088); «Each product supports a different set of models» и Claude Design ✅ в таблице продуктов с ограничениями моделей (15694740, 23.09) | `[документация]` |
| Выбор запоминается | «By default, Claude remembers each user's last selection, so their next conversation starts on whichever model they last used.» (15330088) | `[документация]` |
| Effort | «Always start with the default model and effort level … This setting applies in chat, Cowork, Claude Code, Claude for Office, Claude Design, and Claude Science.» (15330088) → у разговоров Claude Design есть уровень effort; есть ли меню effort в холсте standalone — не сказано | `[документация]` косвенно; `[не проверено]` |
| Fable в Claude Design | «You can access Claude Fable 5 and Fable 5.1 on: … Claude Cowork · Claude Code · Claude Design …» (15424964, 02.09) | `[документация]` |
| Opus 5 и Claude Design | «Our latest Opus-class model, Claude Opus 5, is better than previous Opus models at reading charts, diagrams, and screenshots, making it powerful when paired with Claude Design» (блог, Nate Parrott, 24.07) — единственная связка «модель ↔ Claude Design» после запуска | `[мнение вендора]` |
| Opus 5.5 | анонс 22.09 и release notes о Claude Design молчат; ролик 24.09 «Opus 5.5 Just 10X'd Claude Design» по речи показывает Opus 5.5 в Claude, Claude Code и Codex | `[документация]`, `[мнение]` |
| Пустые места | 6 статей help center о Claude Design и артефактах (23–24.09) — 0 слов model / Opus / effort; 9 анонсов моделей (10 файлов кэша) — 0 упоминаний Claude Design (`grep` по кэшу, 25.09) | `[проверено]` |

**Effort в Claude (8664678, 22.09.2026)** `[документация]`: селектор есть у Opus 5.5, Fable 5.1, Opus 5, Sonnet 5, Fable 5, Opus 4.7,
Opus 4.6, Sonnet 4.6. Уровни: Low и Medium — «work well for routine tasks and stretch your usage further»; High — «the best overall
balance of quality and speed»; Extra high (xhigh) — Opus 4.7 и новее; Max — «the most thorough option». «Thinking cannot be turned off
in Claude when using Claude Opus 5.5, Claude Fable 5.1, or Claude Opus 5.» «Higher effort means more thorough responses, but they take
longer and use more tokens, so you'll reach your usage limits faster.» Модель и effort меняются посреди разговора — «Changes apply
starting with Claude's next response.» Effort в claude.ai появился 28.05 (вместе с Opus 4.8).

**Модели по умолчанию в чате (для справки)** `[документация]`: Sonnet 5 — Free и Pro (30.06); Opus 5 — «the new default model on
Claude Max, and the strongest model on Claude Pro» (24.07); Fable 5.1 — default effort Medium на claude.ai (01.09); Opus 5.5 — default
effort medium (22.09). Кто по умолчанию после 22.09 — не опубликовано. Enterprise: админ задаёт модель и effort по умолчанию
(Organization settings > Models) или «Use Anthropic's recommended default», который «updates automatically when new models are
released».

**Fable на тарифах (15424964, 02.09.2026)** `[документация]`: Max, premium-места Team и seat-based Enterprise — Fable 5 и 5.1 «a
standard part of your plan», «up to 50% of your weekly usage limits on Fable models at no extra cost», при этом они «use them faster
than other Claude models»; Pro и standard-места — только usage credits с первого сообщения; Free — недоступны. Промо «50 % недели на
Fable 5 для всех платных» закончилось 19.07.2026.

**Практика:** Иван (13.08, standalone) — «выбрал бы модель помощнее, типа Opus 5, Fable 5, и не экономил» `[V:uS7gmBLeUV0 03:08]`
`[практика]`; сторонний мок бэкенда Claude Design эмулирует путь `/v1/design/model-selection` (`03-practice-pipelines/` §9.1) `[мнение]`.

**Правило для оркестратора** `[не проверено]` → T-01: перед работой открыть переключатель модели в Claude Design и выбрать модель
явно, а не полагаться на дефолт; для дизайн-системы и первых макетов — Opus 5.5 (на 25.09 «performs at the level of Claude Fable 5.1
on most work and costs 40% less to run than Opus 5», входит в лимиты подписки) с effort High или Extra high; Fable 5.1 — только на Max
(≤ 50 % недельного лимита) или при включённых usage credits; модель и effort записывать в протокол каждого прогона.

**Что анонсы моделей говорят про визуальную работу** (Claude Design в них не упоминается):

| Модель, дата | Официально | Отзывы клиентов `[мнение вендора]` |
|---|---|---|
| Opus 4.7, 16.04 | «more tasteful and creative when completing professional tasks, producing higher-quality interfaces, slides, and docs»; зрение до 2 576 px, «pixel-perfect references» | «the best model in the world for building dashboards and data-rich interfaces. The design taste is genuinely surprising» |
| Opus 4.8, 28.05 | — | «better at carrying context and style direction across a long session … voice, taste, and technical execution» |
| Fable 5, 09.06 | Vision: «rebuilding a web app's source code from screenshots alone» | «Apps that took a hundred prompts a year ago, it now one-shots» |
| Opus 5, 24.07 | «Finally, Opus 5 is capable of producing much stronger visual outputs» | «the front end shows it first: the best animations, games, and 3D work we have seen from an Opus model»; «checks its own work the way a real frontend developer would … desktop and phone widths» |
| Fable 5.1, 01.09 | — | Canva: «in Canva Code it built a rhythm game with real music»; Hebbia: «the best decks of any model» |
| Opus 5.5, 22.09 | «had several Claude models build a game from a single prompt; Opus 5.5 scored higher than any other model on the strength of its graphics and polish» | Rogo: «its slides come out denser, more in line with industry standards» |

Арены на 23.09 (Opus 5.5 там ещё нет) — `03-practice-pipelines/` §5.1.

## 3. Холст и правка: чат, комментарии, прямая правка, «ручки», варианты, версии

Схема (Get started, 23.09): «Claude Design pairs a conversation with a canvas. You describe what you want, and Claude generates a
working design on the canvas beside the conversation. From there, you iterate—refining through conversation, inline comments, and
directly on the canvas until it's right.» Поток из 7 шагов: старт (чат, Artifacts, claude.ai/design) → подключить дизайн-систему →
контекст (скриншоты, кодовая база) → описание → просмотр на холсте → правка (chat / canvas / inline comments) → экспорт или шаринг.
`[документация]`

| Инструмент | Для чего (дословно) | Примеры вендора |
|---|---|---|
| Chat | «best for broad changes that affect the overall design»; «structural changes, new sections, or anything that requires explanation or context» | «Make the color scheme darker and more minimal.» · «Rearrange the dashboard so metrics are in the top row and the chart is below.» · «Add a settings panel on the right side.» · «Show me 2–3 alternative layouts for this page.» |
| Inline comments | «click directly on a specific part of the canvas and request a targeted change»; «targeted, component-level changes» | «Make this button padding larger.» · «Change this to a dropdown instead of radio buttons.» · «Use the primary brand color here.» · «Make this section collapsible.» |
| Edit directly | «Use rich layout controls for quick visual and aesthetic shifts, specifically to drag, resize, and align elements directly.» | — |

Все три — `[документация]`; работают ли так на деле — `[не проверено]`.

**«Ручки» — как называются.** Это два разных механизма, и имена у них менялись `[документация]`:
- **Слайдеры, которые делает Claude** (под конкретный дизайн): 17.04 — «custom sliders (made by Claude)», «adjustment knobs to tweak
  spacing, color, and layout live. Then ask Claude to apply your changes across the full design»; **сейчас** (claude.com/product/design)
  — «use the **adjustment sliders Claude creates** to tune spacing and color». Автор продукта просит их словами: «I asked Claude to let
  me tweak an app's color scheme with sliders and presets rather than describing colors in words»; «adjustable animation controls for
  dialing in the physics of the motion» (блог, 24.07) `[мнение вендора]`.
- **Ручная правка на холсте** (редактор с 17.06): «New, rich layout controls let you drag, resize, and align elements» (блог 17.06);
  help center 23.09 — «Use **rich layout controls** for quick visual and aesthetic shifts, specifically to drag, resize, and align
  elements directly». По ролику — текст, шрифт, размер, цвет, отступы, выравнивание, ширина, слои, контейнеры, сетка, «есть даже
  код» `[V:uS7gmBLeUV0 07:37]` `[практика]`.
- **В интерфейсе** панель слайдеров называется **«Tweaks»** — «Claude может добавить панель быстрых вариантов именно для этого проекта»
  (тема, фон, обводки, плотность, раскладка, переключение версий страницы) «без полной перегенерации»; если не появилась — попросить
  в чате `[V:uS7gmBLeUV0 06:59]` `[практика]`; у Mikey — «adjustment controls» (spacing, color, layout без промта) `[V:PjBfho9Knlw
  08:19]` `[практика]`. В официальных текстах слова «Tweaks» нет. Промт по умолчанию: «Add a Tweaks panel with sliders for spacing,
  color and density» `[не проверено]`.

**Применить ко всему дизайну:** анонс 17.04 — «ask Claude to apply your changes across the full design» `[документация]`; у Ивана —
один комментарий «замени его во всей презентации» `[V:uS7gmBLeUV0 10:02]` `[практика]`.

**Варианты:** «Show me 2–3 alternative layouts for this page.»; совет «Ask for variations … 2–3 options. Comparing alternatives is much
faster than guessing.» Анонс 17.04: «Designers can quickly create a wide range of directions to explore.» `[документация]`

**Версии и ветки:** «Save what we have and try a completely different approach.» — «Claude will save your current project and confirm
where it's saved»; ограничение «Claude Design doesn't have version history yet». В чате: «Edit an earlier message to create a
different version of the chat, with its own artifacts» (What are artifacts, 24.09). `[документация]`

**Самопроверка и ревью:** «Claude builds with your real design system components, checks its own output against your design system,
and makes corrections before you see them.»; «Claude can review your design for accessibility, contrast ratios, information
hierarchy, and general usability. Treat it as a design collaborator, not just a generator.» `[документация]`; насколько проверка
реальна — `[не проверено]`.

**Прототипы:** «Create prototypes and mockups: Describe a UI and get a working interactive prototype.» (admin guide); 17.04: «turn
static mockups into easily-shareable interactive prototypes … without code review or PRs». Переходы и состояния официально не
описаны; в ролике — рабочие переходы, корзина, мобильная версия по просьбе, первая генерация 3–4 мин `[V:uS7gmBLeUV0 05:50]`
`[практика]`.

**Носитель и границы (блог, Nate Parrott, 24.07; обновлён в сентябре)** `[мнение вендора]`: всё строится как HTML — «Claude is
really good with HTML … anything you can make in a slide deck, a video file, or a PDF, you can make in a web page» (прототип продукта —
«HTML playground»: чат слева, результат справа). Границы: «Claude Design doesn't have an image model and isn't built for image
generation, so it's a poor fit for logo design … bring in the logo and assets you already have»; «if you're shipping production
software, stick with Claude Code. Claude Code is for coding; Claude Design is for the other parts of the design work: early ideation,
collaboration, or getting buy-in on a direction». Поддерживает это ролик: для эффектной заставки «видеогенератор часто даст более
эффектный результат» `[V:uS7gmBLeUV0 14:25]` `[мнение]`.

**Совместная работа:** «Two or more people editing a design project at the same time is still basic and may not work reliably.»
(known limitations) `[документация]`. В комментариях внутри организации можно спрашивать Claude (внешним Commenter / Can edit это
недоступно — Share artifacts, 23.09) `[документация]`.

## 4. Дизайн-системы

**Что это (23.09):** «A design system captures your colors, typography, components, and layout patterns, so Claude applies them to
every new design and deck. Claude extracts them from the assets you provide, like codebases, slide decks, or other design
references.» Beta на Pro, Max, Team, Enterprise; на Enterprise включает owner (Design systems в Organization settings > Artifacts).
`[документация]`

| Путь создания | Как | Для чего лучше |
|---|---|---|
| Из чата | «Ask Claude to build a design system from your connected apps, uploaded files, Figma files, decks, logos, and fonts.» | «brand design systems with fonts, colors, and guidelines» |
| Из Claude Code | «If your design system already exists as React components, run /design-sync in Claude Code. It reads your tokens and components directly» | «product design systems in code» |
| Перенос из claude.ai/design | вкладка «Design» внизу сайдбара → баннер «Migrate team design systems»; каждая становится артефактом; баннер «Let Claude clean it up» чистит guide, tokens, components | существующие системы standalone |
| Standalone онбординг | организация в пикере проектов → онбординг → загрузка: Codebases (link/upload repo), Prototypes (screenshots, web flows, design files), Slide decks/documents (PowerPoint, PDF), Individual assets (logos, palettes, type specimens) | — |

Все строки — `[документация]` (Set up your design system, 23.09).

- **Результат** (standalone): Color palette, Typography, Components, Layout patterns. **Проверка:** тестовый проект — «Create a landing
  page for [your product].» · «Design a dashboard showing [relevant metrics].» · «Make a one-pager about [a topic your team commonly
  presents on].» **Публикация:** тумблер «Published» — проекты с домашнего экрана организации берут эту систему вместо дефолтной.
  **Обновление:** настройки организации в Claude Design → «Open» → «Remix» (чат слева). `[документация]`
- **Несколько систем:** «Organizations can have multiple design systems.» Список — Organization settings > Artifacts > Design systems
  (владелец, дата обновления); «Users see these when they start a new artifact, and the default is preselected.» Личное управление —
  Settings > Design systems (`claude.ai/settings/design-systems`). `[документация]`
- **История:** 17.06 — «We rebuilt the design system import to give you more flexibility and increase precision … a new admin role
  can approve one standard system and lock down edits» (блог); с 16.09 — «The new, integrated Claude Design has a revamped Design
  Systems feature» (FAQ страницы продукта); «Admins can lock a team to a single approved design system, so every design stays on brand
  no matter who's building it.» `[документация]`
- **Наследование:** «When you create a project, it automatically inherits your organization's design system.» `[документация]`
  Противоречие в ролике: автор Mikey на вопрос о новом проекте — «It's tied to that project so you'd set it up fresh for a new one»
  `[V:PjBfho9Knlw]` `[мнение]`; Иван — «Её можно подключать к любому новому проекту… одним выбором» `[V:uS7gmBLeUV0 04:12]`
  `[практика]`. Позиция базы: система организации наследуется, а правила, заданные прямо в проекте на холсте, — нет `[спорно]`.
- **Качество зависит от источника:** «Design system import is only as good as its source. A messy codebase or an incomplete file will
  show up in the output.»; «Include real examples, not just specs. A finished landing page or marketing site tells Claude more about
  your brand's feel than a color palette alone.» `[документация]`
- **Связь с Claude Code** (кратко; подробно — `02-claude-code-bridge/` §6): `/design-sync` синхронизирует локальную библиотеку компонентов с проектом
  дизайн-системы в claude.ai/design через инструмент `DesignSync` (методы, `@dsCard`, `_ds_manifest.json`, `.render-check.json` —
  `02-claude-code-bridge/` §6.1–§6.2) `[исходник]` (Claude Code 2.1.281). Help center упоминает только команды `/design-sync` и `/design`.

## 5. Импорт и контекст

| Что | Официально | Метка |
|---|---|---|
| Текст, картинки, документы | 17.04: «Start from a text prompt, upload images and documents (DOCX, PPTX, XLSX), or point Claude at your codebase.» 23.09: «Upload screenshots of existing designs, competitor products, wireframes, or visual inspiration. You can also attach an existing slide deck or document with a design style you want to replicate.» | `[документация]` |
| Кодовая база | «Link a code repository so Claude understands your existing components, architecture, and styling patterns. This makes prototypes more production-ready from the start.» Большие — через Claude Code: «Consider linking very large repositories from Claude Code to avoid lag or browser issues.» Способ подключения в UI (GitHub-ссылка, загрузка папки): у Ивана — «ссылка GitHub, код с компьютера, файл Figma, шрифты, логотипы, документы, фото» | `[документация]`, `[V:uS7gmBLeUV0 02:33]` |
| Figma | только как источник для дизайн-системы из чата («Figma files»); отдельной интеграции с Figma в статьях нет | `[документация]` |
| Web capture | 17.04: «use the web capture tool to grab elements directly from your website so prototypes look like the real product». В статьях help center 23–24.09 не упоминается — есть ли сейчас в шаблоне Design, неизвестно | `[документация]` `[не проверено]` |
| Подключённые приложения | артефакт может читать и писать в подключённые приложения (Asana, Google Calendar, Slack, custom connectors) — Pro и выше, веб и десктоп; «Everyone connects their own apps» | `[документация]` |
| Видео | в ролике: загрузил видео из Google Flow и «одной фразой попросил поставить его фоном» | `[V:uS7gmBLeUV0 08:32]` `[практика]` |
| Набросок от руки | «If you have a layout in your head and no words for it, draw it on paper and upload a photo.» (блог, 24.07) | `[мнение вендора]` |
| Контекст разговора | «If you ask for a design in the middle of a conversation, Claude builds from the files and analysis already in it and references your memory, projects, and skills. Connectors and web search work too» (блог, 24.07); существующий продукт: «connect GitHub, or work from your local codebase in Claude Code … with a few tries it can recreate your existing designs with pretty high fidelity» | `[мнение вендора]` |

## 6. Экспорт, шаринг, handoff в Claude Code

**Экспорт (кнопка Export справа вверху; Get started, 23.09)** `[документация]`: «Download as .zip» · «Export as PDF» · «Export as PPTX»
· «Export to Google Slides (available only at claude.ai/design)» · «Export as standalone HTML» · «Send to the tools you already use:
Adobe Experience Manager, Adobe for Creativity, Adobe Journey Optimizer, Base44, Canva, Gamma, HubSpot, Hyperframes, Lovable, Miro,
Netlify, Replit, v0, Vercel, and Wix» · «Handoff to Claude Code: Send to local coding agent / Send to Claude Code Web».
Admin FAQ: «export to HTML bundles, PPTX, and PDF, hand-off to Claude Code, and sending designs to the partner tools». На старте
(17.04): internal URL, «save as a folder», Canva, PDF, PPTX, standalone HTML. В ролике 13.08 ещё PNG и MP4 `[V:uS7gmBLeUV0 08:44]`
`[практика]` — в документации их нет `[не проверено]`.

**Партнёры и интеграции:** список коннекторов с 17.06 — «Adobe, Base44, Canva, Gamma, Lovable, Miro, Replit, Vercel, and Wix» (блог);
страница продукта: «Export reliably to PDF and PowerPoint or send your work to the apps you already use» `[документация]`. Отзывы
партнёров `[мнение вендора]`: Replit — «**The Claude Design MCP integration** is a natural next step: builders can now design on-brand
apps in Claude Design and build, refine, and ship them in Replit»; Wix — «connects seamlessly to Wix Headless»; Vercel — «push it
straight to Vercel to ship»; Gamma — «move straight into Gamma, fully editable». То есть у Claude Design есть MCP-интеграция для
партнёров (для моста с Claude Code — `02-claude-code-bridge/` §8) `[не проверено]`. Доступ через Claude Tag (Slack) — «coming soon» (FAQ страницы
продукта, 25.09).

**Handoff в Claude Code** `[документация]`:
- 17.04: «When a design is ready to build, Claude packages everything into a handoff bundle that you can pass to Claude Code with a
  single instruction.»
- 23.09: «When a design is ready to become software, you can hand it off to Claude Code, which continues from your existing work
  instead of starting over from a screenshot.»; admin guide: «Hand off to engineering: Export design intent for use with Claude Code or
  your existing development workflow.»
- Обратное направление (из Claude Code): «use /design to import a design into your codebase, export your code as a live prototype, or
  let Claude build the whole thing from start to finish.» Появилось 17.06 (блог: «Prefer to begin in Claude Code? Ask for a design from
  your session on desktop or in the terminal, or use /design to create, edit, and sync design projects»); страница артефактов: «Pull a
  prototype out of your coding session, then send it back in.»
- **Что внутри бандла, help center не описывает** (файлы, спецификации, формат) — разбор в `02-claude-code-bridge/` §8 `[не проверено]`. Отзыв Brilliant
  (17.04): «Including design intent in Claude Code handoffs has made the jump from prototype to production seamless.»
  `[мнение вендора]`. В роликах: при handoff «выбираете локальный агент или веб-сессию, можно добавить другие файлы и написать
  инструкции» `[V:uS7gmBLeUV0 08:58]`; после handoff — «We've hit a dev server failure», Claude Code чинит сам `[V:PjBfho9Knlw 13:13]`
  `[практика]`; совет — «open up the HTML, review the handoff, and test the result» `[V:PjBfho9Knlw 16:12]` `[мнение]`.

**Шаринг (Share artifacts, 23.09)** `[документация]`:

| Тариф | Кому | Права |
|---|---|---|
| Pro, Max | «Only you» / «Anyone with the link» + приглашение по email | Can view / Commenter / Can edit |
| Team, Enterprise | «Only people invited» / «Anyone at [org]» / «Anyone with the link» (если включён External sharing) | то же |

- «Designs start private to you.»; email-приглашения — beta, до 50 внешних людей на артефакт, приглашение живёт 30 дней.
- «People need a Claude account to open any artifact except a legacy artifact published from chat.»
- Внешние Commenter / Can edit не могут @упоминать и спрашивать Claude в комментарии; внешние с «Can edit» — «can upload only images
  and videos». Артефакты с подключёнными приложениями или вызовами Claude не могут быть «Anyone with the link».
- Ролик: «через Design Sync проект можно двигать в обе стороны» `[V:uS7gmBLeUV0 09:03]` — оспорено комментатором («синка нет в явном
  виде… Обратного пути нет, кроме как дать клод дизайну ссылку на гит») `[спорно]`; официально двусторонняя синхронизация описана
  только для дизайн-системы (`/design-sync`) и для импорта/экспорта через `/design`.

## 7. Лимиты и цена

- **Общий пул (Get started, 23.09):** «Claude Design counts toward the same usage limits as the rest of Claude. Design activity draws
  from the same pool as the rest of your work with Claude, including Claude Code, so there's no separate Claude Design allowance to
  track. Complex projects with large codebases or many iterations consume more usage.» `[документация]`
- **При исчерпании:** «If you reach your usage limits, Claude Design is unavailable until your limits reset. If you've enabled usage
  credits, you can keep working after reaching your included limits.» `[документация]`
- **Раньше было иначе:** «Claude Design previously had its own weekly allowance, separate from your other usage limits. All Claude
  Design activity now counts toward your plan's shared limits.» (help center). **Дата — 17.06.2026** (блог): «Claude Design also now
  shares usage limits with the rest of your work with Claude, including Claude Code, so most people will get much more headroom to
  create, and those hitting limits will do so less often.» `[документация]` Ролик 13.08 подтверждает: «Отдельного маленького лимита
  больше нет», а раньше «лимиты… могли закончиться буквально после двух генераций» `[V:uS7gmBLeUV0 00:15, 01:03]` `[практика]`.
- **Крупное дороже:** «Larger requests, like a full deck or design, use more of your limit than a typical message.» (FAQ страницы
  продукта) `[документация]`. **Ручная правка бесплатна:** «Use the direct editing tools (rearrange, delete, edit text, resize, change
  colors) for final touches instead of prompting for them. Direct edits use no tokens» (блог, Nate Parrott, 24.07) `[мнение вендора]`.
- **Effort:** «Higher effort means more thorough responses, but they take longer and use more tokens, so you'll reach your usage limits
  faster.» (8664678) `[документация]` — для Claude Design это значит: высокий effort — на дизайн-систему и первый макет, правки —
  на меньшем `[не проверено]`.
- **Team и seat-based Enterprise:** «Usage draws from each user's seat usage limits, including session and weekly limits. Admins can
  purchase usage credits»; **usage-based Enterprise:** «bills from your organization's consumption at standard API rates».
  `[документация]`
- **22.09 (анонс Opus 5.5):** «we're increasing five-hour usage limits on Pro, Max, Team, and seat-based Enterprise plans. We're also
  providing subscription users a rate limit reset, which you can now save and use whenever you choose.» Касается и Claude Design, раз
  пул общий. `[документация]`
- **Сколько стоит проект или генерация** — официальных чисел нет. Практика: «точечные изменения расходуются заметно спокойнее, чем
  полная перегенерация» `[V:uS7gmBLeUV0 10:35]` `[мнение]`. Отсюда правило: правки комментариями и Tweaks дешевле перегенерации
  `[не проверено]`.
- **Fable в Claude Design:** Max — до 50 % недельного лимита, Pro — только usage credits (§2). `[документация]`
- **Артефакты, вызывающие Claude,** тратят лимиты зрителя, а не автора; хранилище данных артефакта — 20 MB, только текст
  (What are artifacts, 24.09). `[документация]`

## 8. Данные, хранение, безопасность

- **Загруженные материалы (организации):** «Uploaded assets are stored persistently, and fall under the same data retention and deletion
  policies as other Anthropic products for organizations.»; «Claude Design doesn't currently support data residency requirements.»;
  «Removing someone from your organization … removes their access to artifacts at the same time.» (Artifacts admin guide, 23.09)
  `[документация]`
- **Превью:** «Claude Design project previews run inside a sandboxed iframe on a separate content domain that Anthropic operates … The
  code in a preview can't reach your Claude account, your login, or the editor.» Доступ — «signed tokens—short-lived passes … Claude
  re-checks these tokens against your sharing permissions every time someone opens the preview». (admin guide, 23.09) `[документация]`
- **Особые конфигурации:** CMEK, ZDR, HIPAA-ready — новые артефакты (шаблоны, дизайн-системы, приглашения) недоступны; standalone —
  без audit logs; Compliance API пишет события на уровне артефакта. `[документация]`
- **Mythos-класс (Fable 5, 5.1) для бизнес-клиентов:** «We will require 30-day retention for all traffic on Mythos-class models … We
  won't use this data to train new Claude models» (09.06) `[документация]`.
- **Потребительские тарифы (Free, Pro, Max, в том числе их Claude Code)** — privacy center; Claude Design в статьях отдельно не назван,
  поэтому применимость — вывод базы: дизайн в чате = чат, standalone — продукт той же подписки `[документация]` + `[не проверено]`:
  - обучение — только если: «You choose to allow us to use your chats and coding sessions to improve Claude»; разговор помечен для
    safety review; явный opt-in (Trusted Tester). В обучающие данные входит «the entire related conversation, along with any content»,
    но не «raw content from connectors … though data may be included if it's directly copied into your conversation» (16.03.2026);
  - переключатель: Settings > Privacy > «Help Improve our AI models» (`claude.ai/settings/data-privacy-controls`); выключение
    действует на будущее: «Your data will still be included in model training that has already started» (03.08.2026);
  - сроки (01.07.2026): удалённый разговор — «Removed from your chat history immediately», «Deleted from our back-end storage systems
    within 30 days»; при включённом model improvement — «up to 5 years» в обезличенном виде; помеченное нарушение Usage Policy — входы
    и выходы до 2 лет, скоринги до 7 лет; фидбек (thumbs up/down) — 5 лет; Incognito-чаты в обучение не идут;
  - **для заказчика:** если дизайны и дизайн-система клиента не должны попасть в обучение — выключить «Help Improve our AI models» до
    загрузки материалов `[не проверено]` (как это распространяется на standalone claude.ai/design — не описано).
- **Удаление:** удалённый артефакт — «Everyone you invited loses access»; внешние «Can edit» удалить артефакт не могут; снятие legacy-
  артефакта с публикации «permanently deletes any personal and shared storage data» (Share artifacts, 23.09). Отдельной инструкции
  «удалить проект Claude Design» в help center нет `[документация]`.
- **Коммерческие тарифы (Team, Enterprise, API; privacy center, 18.08.2026):** «By default, we will not use your inputs or outputs from
  our commercial products (e.g. Claude for Work, Anthropic API, Claude Gov, etc.) to train our models.» Исключение — фидбек (thumbs
  up/down) и явное согласие; owner может выключить «Rate chats» в Organization settings > Data and Privacy `[документация]`.
  Mythos-класс требует 30-дневного хранения (выше).

## 9. Официальные советы по промтам и процессу (дословно)

**Формула промта (Get started, 23.09):** «A good prompt includes the goal (what you're building), the layout (how things should be
arranged), the content (what information to display), and the audience (who will use it). Claude will also ask clarifying questions if
it needs more information.» `[документация]`

Примеры вендора:
```
Create a dashboard showing monthly revenue with filters for region and product line.
Design a mobile app onboarding flow with 4 screens that walks users through our core features.
Build a landing page for our new API product with a hero section, code examples, and pricing.
Create a form for collecting customer feedback with conditional questions based on category.
Design an internal tool for our ops team to review and approve content submissions.
```

**Tips for best results (7, дословно заголовки):** «Import a complete design system.» · «Start simple, then layer in complexity.»
(«Claude responds well to incremental requests.») · «Be specific in your feedback.» («"Tighten the spacing between form fields to 8px"
gives Claude exactly what it needs.») · «Reference your design system.» («"Use the Primary Button component" or "Apply the Card layout
pattern."») · «Think about responsiveness early.» · «Ask for variations.» · «Ask Claude for feedback.» `[документация]`

**Дизайн-система:** «Include real examples, not just specs.» · «Iterate. If the first extraction doesn't capture your brand well, try
uploading additional or different assets.» Для организаций: «The single most important thing you can do before rolling out Claude
Design is have an experienced designer set up your organization's design system.»; «pulling in designers across both brand and product
design». `[документация]`

**Контекст:** «The more context you give Claude, the better your output will be. You can attach reference material at any point during
a project.» `[документация]`

**Старт без идей (блог 17.06, раздел Getting started):** «No ideas? Ask for three directions on your next landing page, and pick the
one worth refining.» `[документация]`

**10 правил автора продукта** (Nate Parrott, product designer Anthropic, блог 24.07; «expresses his opinions») `[мнение вендора]`:

| # | Правило (дословно) | Суть и приём |
|---|---|---|
| 1 | «Do the thinking before you prompt.» | промт готовить заранее; можно диктовать — «Sometimes I dictate them in Claude Design with the voice button» |
| 2 | «Tell Claude what it should look like.» | «Left undirected, Claude picks one of its favorite aesthetics.» → задать шрифты и цвета, дать мудборд или попросить Claude «brainstorm font-and-color pairings» и выбирать |
| 3 | «Turn recurring work into a design system.» | логотипы, деки, скриншоты, типографика — как raw uploads, design files или GitHub-репозиторий; систем может быть несколько |
| 4 | «Ask for ten options, then remix.» | «Most of them won't be good, and that's fine; one or two will be.» Затем: «I like option B and a little of option D. Give me five riffs that smoosh those together.» |
| 5 | «Sketch what you can't describe.» | нарисовать на бумаге и загрузить фото |
| 6 | «Point and talk.» | кликнуть по элементу, выбрать «comment» и надиктовать |
| 7 | «Wireframe first when fidelity doesn't matter.» | «Asking for wireframes is much faster, and it keeps Claude focused on the higher-level structure» |
| 8 | «Make the last mile manual.» | финальные мелочи — прямой правкой: «Direct edits use no tokens» |
| 9 | «Give Claude your real context.» | GitHub или локальная кодовая база в Claude Code; в разговоре — файлы, memory, projects, skills, коннекторы, веб-поиск |
| 10 | «Keep working alongside Claude.» | «You can queue up multiple messages at once, or keep talking while Claude is still working on the previous turn.» |

Там же — пример объёма: «generating 15 versions of a flow to collect feedback from colleagues».

**Вебинар Anthropic «Getting Started with Claude Design»** (03.09.2026, запись за регистрацией — не смотрели): «when to use it» (деки,
one-pagers, social graphics, mockups), «How to import your design system. The one setup step that keeps every deck, doc, and graphic
on brand», «brief to final export» `[документация]` — кандидат для заказчика.

**Смежное официальное (гайды platform.claude.com для API; разбор — `03-practice-pipelines/` §4):** «Prompting Claude Opus 5.5» — запрет
«avoid a generic AI look» «mostly swaps one default for another», перечислять приметы («Do not use a cream or off-white background,
italic accent words in headlines, numbered "01/02/03" section labels, monospace labels, or pill-shaped buttons.»); «Prompting Claude
Opus 4.8» — «propose 4 distinct visual directions … Ask the user to pick one». Перенос в Claude Design `[не проверено]`.

## 10. Известные ограничения (Get started, 23.09.2026, дословно) и прочие оговорки

«Claude Design is now available in beta. A few things to be aware of:» `[документация]`
1. «Comment persistence: Inline comments occasionally don't appear on the page, but you can still see them by opening the comments
   view.» + заметка: «If your comments aren't being picked up, paste the feedback directly into the chat instead. This is a known
   workaround for an intermittent issue where comments can disappear before Claude reads them.»
2. «Large codebases: Consider linking very large repositories from Claude Code to avoid lag or browser issues. To sync a design system,
   use /design-sync from Claude Code.»
3. «Chat errors: If you hit a "chat upstream error," try starting a new chat tab within the same project.»
4. «Mobile: … Editing on the canvas and changing sharing settings need Claude on web or desktop.»
5. «Multi-person editing: Two or more people editing a design project at the same time is still basic and may not work reliably.»
6. «Design system import: Design system import is only as good as its source.»
7. «Version history: Claude Design doesn't have version history yet.»

Прочее `[документация]`: нет audit logs у standalone, нет data residency, CMEK/ZDR/HIPAA без новых артефактов (§8); Education/K-12 —
без email-приглашений; Analytics > Claude Design — только claude.ai/design; ошибки — «Try fixing with Claude», «success isn't guaranteed».

## 11. Хронология апрель → сентябрь 2026 и «2.0» / «3.0»

| Дата | Событие | Источник, метка |
|---|---|---|
| 16.04 | Opus 4.7: «more tasteful and creative … producing higher-quality interfaces, slides, and docs»; зрение до 2 576 px по длинной стороне | анонс Opus 4.7 `[документация]` |
| 17.04 | Запуск Claude Design (Anthropic Labs), research preview, «powered by our most capable vision model, Claude Opus 4.7»; Pro, Max, Team, Enterprise (Ent — выкл.); отдельный недельный лимит | анонс, release notes `[документация]` |
| 28.04 | «Claude for Creative Work»: Claude Design «built to export the results to other tools, starting with Canva» | анонс «Claude for Creative Work» `[документация]` |
| 28.05 | Opus 4.8; **effort control в claude.ai и Cowork** «alongside the model selector», на всех тарифах | анонс Opus 4.8 `[документация]` |
| 09.06 | Fable 5 (Mythos-класс): на подписках бесплатно до 22.06, дальше usage credits; 12.06 доступ приостановлен (экспортный контроль США) | анонсы `[документация]` |
| 12.06 | «Edit Claude's drafts in place» — правка выделением в артефактах чата | release notes `[документация]` |
| **17.06** | **«Claude Design now stays on brand for daily work»**: переписан импорт дизайн-систем (несколько систем, GitHub, design files, raw uploads; самопроверка; админ-роль для единой системы); `/design-sync` и `/design` в Claude Code; handoff «continues from your existing work instead of starting over from a screenshot»; новый редактор с «rich layout controls» и «hundreds of stability fixes»; **общий лимит с чатом и Claude Code**; коннекторы Adobe, Base44, Canva, Gamma, Lovable, Miro, Replit, Vercel, Wix; место в сайдбаре десктопа; «Over one million people used Claude Design in its first week». В release notes записи нет | блог claude.com `[документация]` |
| 30.06–01.07 | Sonnet 5 — модель по умолчанию на Free и Pro; Fable 5 возвращён (до 50 % недельного лимита «through July 7», затем промо продлили до 19.07); Enterprise — model entitlements (модели и effort) | анонсы, release notes `[документация]` |
| 07.07 | Cowork на вебе и мобильных; «Chat and Cowork also share one home now, with one place for your projects and artifacts» | release notes `[документация]` |
| 19–20.07 | Промо «до 50 % недели на Fable 5» для всех платных закончилось 19.07; дальше Fable — стандарт Max, на Pro — usage credits | help center 15424964 `[документация]` |
| 24.07 | Opus 5 — «the new default model on Claude Max, and the strongest model on Claude Pro»; «much stronger visual outputs»; в тот же день пост Nate Parrott: Opus 5 «powerful when paired with Claude Design», 10 правил работы | анонс Opus 5, блог `[документация]` `[мнение вендора]` |
| 05.08 | Ролик «Claude Design 3.0 Can NOW Build 3D Animated Websites» (Zinho Automates) | ролик заказчика, `91-videos/` |
| 13.08 | Ролик «Полный гайд по новому Claude Design 2.0» (Иван): общий лимит, «больше десятка» шаблонов в claude.ai/design, выбор модели, панель Tweaks — то есть состояние после 17.06 | `[V:uS7gmBLeUV0 00:00–01:18]` `[практика]` |
| 19.08 | Артефакты Cowork до этой даты становятся live artifacts (новый формат артефактов) | What are artifacts `[документация]` |
| 01.09 | Fable 5.1 / Mythos 5.1; Fable 5.1 по умолчанию High effort в Claude Code, Medium в Cowork и claude.ai; доступен в Claude Design (Pro — за usage credits) | анонс, help center `[документация]` |
| 03.09 | Вебинар Anthropic «Getting Started with Claude Design» (запись по регистрации) | anthropic.com/webinars `[документация]` |
| 16.09 | **«Create designs, decks, and docs in any conversation»**: Claude Design внутри разговоров «with all of its features, including on-canvas editing and importing your design system»; Claude Slides и Claude Docs; дизайн по просьбе в любом чате и сеансе Claude Code; legacy-артефакты — сделанные до 16.09 | release notes, help center `[документация]` |
| 17.09 | Ролик Mikey «… Master 95% of Claude Design» (теги «claude design 2.0») | `91-videos/` |
| 22.09 | Opus 5.5: «performs at the level of Claude Fable 5.1 on most work and costs 40% less to run than Opus 5»; выше пятичасовые лимиты подписок, сохраняемый сброс лимита. Про Claude Design — ни слова | анонс, release notes `[документация]` |
| 23–24.09 | Статьи help center о Claude Design и артефактах переписаны под новый формат (beta, шаблоны, общие лимиты) | help center `[документация]` |
| 24.09 | Ролик «Opus 5.5 Just 10X'd Claude Design» — по речи работа в основном в Claude, Claude Code и Codex, а не в холсте Claude Design | ролик заказчика `[мнение]` |

**«2.0» и «3.0».** Нумерованных версий у Claude Design нет ни в release notes, ни в help center, ни в блоге; в release notes между
17.04 и 16.09 записей про Claude Design нет вовсе `[документация]`. Единственное крупное официальное обновление между ними — **пост
17.06** (новый редактор, дизайн-системы, `/design-sync` и `/design`, общий лимит, коннекторы). Его содержимое совпадает с тем, что
Иван 13.08 называет «2.0»: «шаблоны + общий лимит + доработали шаблоны, интерфейс и интеграции» `[V:uS7gmBLeUV0 00:00–00:31]`;
теги «claude design 2.0» у Mikey (17.09) — тот же ярлык. «3.0» (Zinho, 05.08) — название ролика про 3D-сайты без отдельного
официального события в эти даты. Позиция базы: «2.0» ≈ обновление 17.06, «3.0» — ярлык блогера; в ссылках указывать дату, а не
«версию» `[документация]` + `[мнение]`.

## Частые ошибки

1. **Считать «2.0» и «3.0» версиями Anthropic.** Это ярлыки роликов; ссылаться на даты (17.04, 17.06, 16.09). → §11
2. **Считать, что Claude Design «работает на Opus 5.5», потому что так сказано в названии ролика 24.09.** Официально — переключатель
   модели без названного дефолта; модель проверять в интерфейсе и писать в протокол. → §2
3. **Начинать с экранов без дизайн-системы.** Вендор: «functional but generic output»; у Mikey расплывчатый промт «build a home screen
   for the recipe app and make it modern and clean» дал generic-результат, после чего он откатил и дал бриф по формуле
   `[V:PjBfho9Knlw 04:25–05:40]` `[практика]`. → §4, §9
4. **Размытые правки** («Make it premium», «Make it modern» — «leave Claude guessing» `[V:PjBfho9Knlw 15:48]`; «This doesn't look right»
   — «hard to act on», help center). Правка = конкретное значение («8px», имя компонента, референс). → §9
5. **Не задавать эстетику.** «Left undirected, Claude picks one of its favorite aesthetics» (Nate Parrott); практики видят «Claude
   fingerprints»: «That font is very Claude» `[V:HOXrLsVqinY 09:50]`, «даже с дизайн-системой видно, что сделано в Клоде» (комментарий к
   ролику Ивана). Шрифты, цвета, мудборд — в первый промт. → §9
6. **Доверять инлайн-комментариям без проверки.** Известный сбой: комментарии пропадают до того, как Claude их прочтёт. → §10
7. **Не проверять экспорт.** «the canvas can look exactly how you want it, but you still need to check what actually gets exported»
   `[V:PjBfho9Knlw 16:12]`; после handoff у Mikey — «dev server failure» `[V:PjBfho9Knlw 13:13]`. → §6
8. **Путать сущности:** шаблон Design и standalone claude.ai/design (разные тумблеры; Google Slides и аналитика — только standalone);
   Claude Design и плагин «Design» из маркетплейса (claude.com/plugins/design — critique, UX writing, a11y-аудит); Claude Design и Claude
   Slides (деки с 16.09 — отдельный шаблон). → §1
9. **Ждать картинок и логотипов.** Модели изображений нет; свои ассеты приносить. → §3
10. **Считать лимит Claude Design отдельным** (было до 17.06) или думать, что Fable «бесплатен» на Pro — там Fable идёт за usage credits
    с первого сообщения. → §2, §7
11. **Верить в «синк в обе стороны»** из ролика `[V:uS7gmBLeUV0 09:03]`: официально двусторонне связаны дизайн-система (`/design-sync`) и
    импорт/экспорт через `/design`; обычный проект сам в код не синхронизируется. → §6
12. **Чинить проект вместо дизайн-системы.** Иван: при системной ошибке править систему, а не отдельный проект `[V:uS7gmBLeUV0 11:06]`
    `[практика]`; вендор: «Design system import is only as good as its source». → §4
13. **Не давать реальные данные.** «Если вы не дали реальные данные, Claude подставит правдоподобные примеры» `[V:uS7gmBLeUV0 10:02]` —
    в прототипах для заказчика подставлять реальный контент или явно помечать заглушки. → §9
14. **Запускать `/design` из скрипта с API-ключом или из Agent SDK** — публикация не сработает (нужен `/login`; в SDK выключено по
    умолчанию). → §1

## Что проверить в тестах

Всё ниже заявлено вендором или практиками, но подтверждается только запуском на аккаунте заказчика. Формат: гипотеза → как → успех.

1. **T-01 Модель и effort.** В Claude Design (standalone и Output > Design в чате) есть выбор модели и effort, Opus 5.5 доступен → открыть
   переключатель, записать список, дефолт, effort → скриншот и протокол; Opus 5.5 выбирается.
2. **T-02 Дизайн-система из кода.** `/design-sync` переносит токены и React-компоненты → проект «Create a landing page for [product]»,
   сверить CSS-переменные экспорта HTML с `tokens.css` → цвета, шрифты, радиусы, компоненты совпадают, выдуманных компонентов нет.
3. **T-03 Самопроверка по системе.** «checks its own output … makes corrections» → попросить нарушение («use a red primary button») →
   зафиксировано: исправил, предупредил или выполнил молча.
4. **T-04 Управляемость правок.** 10 атомарных правок (5 комментариями, 5 чатом), diff HTML до/после → ≥ 9 из 10 без побочных
   изменений; посчитаны пропавшие комментарии.
5. **T-05 Tweaks / слайдеры.** «Add a Tweaks panel with sliders for spacing, color and density», затем «apply these values across the
   full design» → панель есть, значения применились ко всему дизайну, движение слайдеров почти не тратит лимит.
6. **T-06 Варианты.** «Show me 3 directions» и «ten options, then remix» на одном брифе → варианты различимы (сетка, типографика), все в
   рамках системы; время записано.
7. **T-07 Handoff.** «Send to local coding agent» и «Send to Claude Code Web» с одного дизайна против .zip и standalone HTML → ясно,
   что приходит в Claude Code; страница собирается без ручной переделки (скриншоты 1440 и 390).
8. **T-08 `/design` из Claude Code 2.1.281.** `/design a settings screen for a mobile banking app` в сеансе с `/login`, правка артборда,
   экспорт PNG/PDF → артефакт опубликован и правится; с API-ключом публикация не проходит (подтвердить).
9. **T-09 Лимиты.** Замер usage до/после: первый экран, правка чатом, комментарием, прямая правка, 5 вариантов; Opus 5.5 High против
   Medium → таблица «доля 5-часового окна Pro/Max на шаг»; проверено «Direct edits use no tokens».
10. **T-10 Скорость.** Секундомер на первую генерацию и правки → цифры против «3–4 минуты» `[V:uS7gmBLeUV0 05:50]`.
11. **T-11 Экспорт.** PDF, PPTX, standalone HTML, .zip, PNG и MP4 (есть ли) против холста по скриншотам → описаны расхождения; ясно,
    какой формат отдавать в код, какой заказчику.
12. **T-12 Web capture.** Искать инструмент в standalone и в шаблоне → есть или нет, как работает.
13. **T-13 Большой репозиторий.** Подключить репозиторий заказчика в браузере и через Claude Code → лаги зафиксированы или их нет.
14. **T-14 Совместная работа.** Второй аккаунт: комментарий, «ask Claude in a comment», одновременная правка → что работает.
15. **T-15 Качество на брифе.** Один бриф — Claude Design и Claude Code + `frontend-design`;
    слепая оценка по `../ui/13-evaluation-checklists/` → ранжирование с оценками.
16. **T-16 Приватность.** «Help Improve our AI models» выключен до загрузки материалов клиента; есть ли отдельная настройка у standalone
    → скриншот настроек.

## Открытые вопросы и противоречия

1. **Модель по умолчанию и набор моделей в Claude Design** не опубликованы («Not all models are available in every product»);
   упоминание Opus 5.5 в связке с Claude Design — только в ролике. → T-01 `[спорно]`
2. **Effort в холсте standalone** — упомянут только косвенно (Enterprise-настройка «default model and effort level» для Claude Design).
3. **Free:** release notes 16.09 («every plan, including Free») против 4 источников («paid plans»). Позиция: шаблон Design — только
   платные. `[спорно]`
4. **Что внутри handoff bundle** (файлы, design intent, спецификации) — help center не описывает; разбор — `02-claude-code-bridge/` §8. `[не проверено]`
5. **Web capture** есть в анонсе 17.04, нет в статьях 23–24.09 и на странице продукта. `[не проверено]`
6. **Экспорт PNG и MP4:** у Ивана есть, в help center нет (PNG — только для артбордов `/design` в документации Claude Code).
7. **Когда статус сменился с research preview на beta** — вероятно 17.06 (картинка поста «Claude-Design-beta-static»), прямой фразы нет.
8. **«Claude Design MCP integration»** (Replit, 17.06) — только для партнёров или доступна и Claude Code? → `02-claude-code-bridge/` §8.
9. **Наследование дизайн-системы в новый проект:** help center — наследуется системой организации; Mikey — «tied to that project».
10. **Приватность standalone claude.ai/design** на потребительских тарифах — privacy center Claude Design не упоминает.
11. **Release notes неполны:** обновления 17.06 в них нет; для хронологии Claude Design главный источник — блог claude.com.
12. **Стоимость шага в лимитах** — официальных чисел нет, только «Larger requests … use more of your limit» и «Direct edits use no tokens».

## Источники

Дата чтения — 25.09.2026 для всех.

| # | Источник (URL) | Дата публикации / обновления | Метка | Где | Кэш |
|---|---|---|---|---|---|
| 1 | support.claude.com/en/articles/14604416 Get started with Claude Design | 23.09.2026 | `[документация]` | §1, §3, §5–§7, §9, §10 | `support.claude.com_en_articles_14604416-…_62319f96.md` |
| 2 | support.claude.com/en/articles/14604397 Set up your design system | 23.09.2026 | `[документация]` | §4, §9 | `…14604397-…_2a6a6761.md` |
| 3 | support.claude.com/en/articles/14604406 Claude Design admin guide | 23.09.2026 | `[документация]` | §1, §4, §6, §8 | `…14604406-…_0def528d.md` |
| 4 | support.claude.com/en/articles/16994751 Artifacts admin guide | 23.09.2026 | `[документация]` | §1, §4, §7, §8, §10 | `…16994751-…_4fd6edc8.md` |
| 5 | support.claude.com/en/articles/17153992 What are artifacts | 24.09.2026 | `[документация]` | §1, §3, §7 | `…17153992-…_b3c7ed61.md` |
| 6 | support.claude.com/en/articles/9547008 Share artifacts | 23.09.2026 | `[документация]` | §6, §8 | `…9547008-share-artifacts_3d89cd3b.md` |
| 7 | support.claude.com/en/articles/12138966 Release notes | 24.09.2026 | `[документация]` | §1, §11 | `…12138966-release-notes_93202da0.md` |
| 8 | support.claude.com/en/articles/15694740 Manage model access | 23.09.2026 | `[документация]` | §2 | `…15694740_511fcd8b.md` (таблица — из HTML) |
| 9 | support.claude.com/en/articles/15330088 Set a default model | 21.09.2026 | `[документация]` | §2 | `…15330088_600453f4.md` |
| 10 | support.claude.com/en/articles/8664678 Change the model, effort, and thinking | 22.09.2026 | `[документация]` | §2, §7 | `…8664678_a8b5aa24.md` |
| 11 | support.claude.com/en/articles/15424964 Claude Fable models on your plan | 02.09.2026 | `[документация]` | §2, §7 | `…15424964-…_5e71f411.md` |
| 12 | privacy.claude.com/en/articles/10023580 Is my data used for model training? (consumer) | 16.03.2026 | `[документация]` | §8 | `privacy.claude.com_…10023580…_9a4778fa.md` |
| 13 | privacy.claude.com/en/articles/10023548 How long do you store my data? | 01.07.2026 | `[документация]` | §8 | `…10023548…_a2a83e89.md` |
| 14 | privacy.claude.com/en/articles/12109829 Model improvement settings | 03.08.2026 | `[документация]` | §8 | `…12109829…_22472ab8.md` |
| 15 | privacy.claude.com/en/articles/7996868 Model training (commercial) | 18.08.2026 | `[документация]` | §8 | `…7996868…_c3499e60.md` |
| 16 | anthropic.com/news/claude-design-anthropic-labs | 17.04.2026 | `[документация]`, отзывы `[мнение вендора]` | §1–§7, §11 | — |
| 17 | anthropic.com/news/claude-opus-4-7 | 16.04.2026 | `[документация]` | §2, §11 | `www.anthropic.com_news_claude-opus-4-7_b5232cfa.md` |
| 18 | anthropic.com/news/claude-opus-4-8 | 28.05.2026 | `[документация]` | §2, §11 | `…claude-opus-4-8_5f3a9a51.md` |
| 19 | anthropic.com/news/claude-fable-5-mythos-5 | 09.06.2026 | `[документация]` | §2, §8, §11 | `…claude-fable-5-mythos-5_11c4ac33.md` |
| 20 | anthropic.com/news/fable-mythos-access | 12.06.2026 | `[документация]` | §11 | `…fable-mythos-access_e8bdc063.md` |
| 21 | anthropic.com/news/redeploying-fable-5 | 30.06.2026 | `[документация]` | §2, §11 | `…redeploying-fable-5_24a872ed.md` |
| 22 | anthropic.com/news/claude-sonnet-5 | 30.06.2026 | `[документация]` | §2, §11 | `…claude-sonnet-5_9b2ad380.md` |
| 23 | anthropic.com/news/claude-opus-5 | 24.07.2026 | `[документация]`, отзывы `[мнение вендора]` | §2, §11 | `…claude-opus-5_1445d8a4.md` |
| 24 | anthropic.com/claude-fable-and-mythos-5-1 | 01.09.2026 | `[документация]` | §2, §11 | `www.anthropic.com_claude-fable-and-mythos-5-1_9c85c9bd.md` |
| 25 | anthropic.com/news/claude-opus-5-5 (дубль anthropic.com/claude-opus-5-5) | 22.09.2026 | `[документация]` | §2, §7, §11 | `…news_claude-opus-5-5_773a3a73.md` |
| 26 | anthropic.com/webinars/getting-started-with-claude-design | 03.09.2026 (запись) | `[документация]` | §9, §11 | `www.anthropic.com_webinars_getting-started-with-claude-design_d99c7548.md` |
| 27 | claude.com/product/design | без даты (FAQ — после 16.09) | `[документация]`, отзывы `[мнение вендора]` | §1, §3, §4, §6, §7 | `claude.com_product_design_e2b936bf.md` |
| 28 | claude.com/features/artifacts | без даты | `[документация]` | §1, §6 | `claude.com_features_artifacts_24595f4c.md` |
| 29 | claude.com/blog/claude-design-stays-on-brand-for-daily-work | 17.06.2026 (апдейт — сентябрь) | `[документация]` | §3–§7, §9, §11 | `claude.com_blog_claude-design-stays-on-brand-for-daily-work_22f7359a.md` |
| 30 | claude.com/blog/how-the-product-designer-who-built-claude-design-uses-it-… (Nate Parrott) | 24.07.2026 (обновлён в сентябре) | `[мнение вендора]` | §2, §3, §5, §7, §9 | `claude.com_blog_how-the-product-designer-…_bd95594d.md` |
| 31 | claude.com/blog/cowork-is-now-claude | 16.09.2026 | `[документация]` | §1, §11 | `claude.com_blog_cowork-is-now-claude_dc7fec7f.md` |
| 32 | claude.com/plugins/design | без даты | `[документация]` | Частые ошибки | `claude.com_plugins_design_2935d306.md` |
| 33 | code.claude.com/docs/en/artifacts | без даты | `[документация]` | §1 | `code.claude.com_docs_en_artifacts_2da616de.md` |
| 34 | «Claude for Creative Work» (28.04.2026); platform.claude.com, руководства по промтам (~23.09); Hacker News | — | `[документация]`, `[мнение]` | §9, §11 | — |
| 35 | Ролики заказчика uS7gmBLeUV0, PjBfho9Knlw, HOXrLsVqinY; мок claude-code-router и гайды Opus 4.8 / 5.5 — `03-practice-pipelines/` §4, §9.1 | 25.09.2026 | `[V:…]`, `[мнение]` | §2–§11 | — |
