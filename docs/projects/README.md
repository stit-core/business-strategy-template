# Проекты

Корень решения: **несколько проектов** под одним бизнесом. Каждый проект —
папка `docs/projects/<project-slug>/`, внутри которой живёт вся аналитика
этого продукта: продуктовый слой (vision + реестр-хребет поверхностей +
kind, факты и голос продукта), UX-интерфейс (`interface/<surface>/`),
композиция экранов (`screens/<surface>/`) или диалогов телеграм-бота
(`telegram-bot-flow/<surface>/` — для bot-поверхностей), либо карта
мобильного приложения (`mobile/<surface>/` — для мобильных поверхностей,
композиция и мост к коду `<org>/mobile`), FSD-карта фронта
(`fsd/<surface>/` — для фронтовых поверхностей кабинета, мост к коду
`<org>/frontend`), слой страницы сайта и лендинга (`site/<surface>/` — вместо
интерфейса, экранов и FSD-карты, мост к коду `<org>/site`), облик продукта
(`design/`: бренд, дизайн-система, ассеты, макет) и сервисная топология
бэкенда (`services/`: сервисы, их паспорта и домены внутри них).
Рядом с проектами живёт общий **ИТ-периметр бизнеса**
(`infrastructure/`: сервера, рантаймы, общие платформенные ресурсы,
размещение сервисов) — один на все проекты.

**Поверхность (surface) — ось продукта.** Реестр `surface.md` объявляет
поверхности (web, mobile, бот, API …) с родом веб-поверхности (`web-kind`:
`landing`, `site`, `app`), а их slug'и партиционируют возможности,
интерфейс, композицию (экраны, слой страницы, диалоги бота или карта
мобильного приложения — по `type` и роду поверхности) и облик поверхности:
каждая поверхность описывается сверху вниз в своей папке. Точки стыка
**между проектами** одного бизнеса — в [`project-map.md`](project-map.md).

## Структура

```
docs/projects/
├── README.md            (этот файл)
├── project-map.md       ← карта стыков между продуктами бизнеса (singleton: канон формы + данные)
├── infrastructure/      ← ИТ-периметр бизнеса (один на все проекты: server.md, runtime.md, shared-platform.md, job.md, placement.md)
├── _template/           ← КАНОН формы (образец, не данные проекта)
│   ├── project/         канон продуктового слоя (vision + surface-реестр + kind)
│   ├── interface/       канон UX-слоя одной поверхности (who/stage/situation/scenario/…)
│   ├── screens/         канон слоя экранов одной поверхности (flow/screen/block/shell, map.md, texts.md)
│   ├── fsd/             канон FSD-карты одной фронтовой поверхности (8 файлов слайсов, мост к коду фронта)
│   ├── site/            канон слоя страницы одной поверхности сайта или лендинга (формы — схемы базы скилла)
│   ├── design/          канон облика продукта и его поверхностей (формы файлов без схемы — design/_template/)
│   ├── telegram-bot-flow/  канон слоя диалогов одной bot-поверхности (фичи: dialog/window/use-case + сквозные command/notification)
│   ├── mobile/          канон карты приложения одной мобильной поверхности (12 файлов: экраны, сценарии, фичи, входы, разрешения, системные действия, виджеты, фон; мост к коду приложения)
│   └── services/        канон сервисного слоя (реестры, паспорт, _templates/, _shared/)
└── <project-slug>/      ← ДАННЫЕ одного проекта
    ├── README.md        чем продукт, какие проблемы закрывает
    ├── vision.md        singleton + addresses-problem (M:N → business-problem)
    ├── surface.md       РЕЕСТР-ХРЕБЕТ поверхностей (type, web-kind)
    ├── user.md  object.md  action.md … market.md   кросс-поверхностные kind продукта
    ├── facts.yaml  voice.yaml  voice.product.yaml  voc.yaml   факты, голос, слова клиента (ведёт /design-deep-dive)
    ├── capability/<surface>.md   возможности по поверхности
    ├── interface/<surface>/      who/stage/situation/scenario/zone/block/ux-substrate/data-items (кроме web рода landing и site)
    ├── screens/<surface>/        map.md texts.md flows/ screens/ blocks/ shells/ assets/ (web рода app, admin, desktop, embed)
    ├── fsd/<surface>/            entities/features/pages/widgets/app/shared-* (web рода app, admin, desktop, embed)
    ├── site/<surface>/           site-brief.yaml meaning.yaml site-map.yaml hierarchy/ plans/ copy/  (web рода landing и site — вместо interface, screens, fsd)
    ├── telegram-bot-flow/<surface>/   command.md notification.md features/<feature>/{dialog.md,window.md,use-case.md}  (для type: bot — вместо screens)
    ├── mobile/<surface>/         entities/screens/flows/features/shell/entry-points/permissions/system-actions/widgets/background-tasks/shared-*  (для type: mobile — вместо screens)
    ├── design/          облик продукта: brand.yaml, дизайн-система, app-brief.yaml, паспорт визуала, _assets/, ARTIFACTS.md
    │   └── <surface>/   арт-дирекция, assets/, motion/, canvas/, input/, review/, ready.yaml  (web, admin, desktop, embed)
    └── services/        service.md + platform.md + architecture.md + _shared/
                         + <service-slug>/ (паспорт + domains/<ctx>/)
```

Канон формы живёт **один раз** в `_template/`; папки проектов держат только
данные. Скилы читают форму из `_template/<слой>/`, пишут данные в
`<project-slug>/...`. `_template/` — read-only образец: его не правят под
конкретный проект. Форма `_template/interface/`, `_template/screens/`,
`_template/fsd/`, `_template/site/`, `_template/telegram-bot-flow/` и
`_template/mobile/` — канон **одной папки поверхности**; в данных она
повторяется под каждый slug из реестра `surface.md` (композиция — по `type` и
роду поверхности: экраны, слой страницы, диалоги бота либо карта мобильного
приложения; FSD-карта — только у фронтовых поверхностей кабинета).

## Связь с проблемой (M:N)

Реестр проблем бизнеса (`business-problem` в `docs/business/`) — **общий
для всех проектов** слой. Каждый проект объявляет, какие проблемы он
закрывает, полем `addresses-problem` в своём `vision.md` (массив slug-рефов
на строки реестра `business-problem`). Проблему могут закрывать несколько
проектов, проект — несколько проблем (M:N). Авторская сторона связи —
продукт; обратную (какие проекты бьют в проблему) сводит `/cross-audit`.

## Взаимодействие проектов (project-map)

Проекты бизнеса не изолированы — продукты стыкуются (приложение лояльности
шлёт баллы в магазин, аналитика читает заказы). Каждый такой стык —
ребро в [`project-map.md`](project-map.md). Авторская сторона ребра —
`integration` проекта-инициатора (`target: sibling-project`); карта сводит
их в граф; техническое воплощение — порт/события в `services/`.
Согласованность трёх сторон сверяет `/cross-audit`.

## Выбор проекта и поверхности в скилах

Скилы слоёв project / interface / services / domain / screen / fsd / design /
telegram-bot-flow / mobile работают **в контексте одного проекта**;
interface, screen, fsd, telegram-bot-flow и mobile — ещё и **в контексте
одной поверхности**, а `design-deep-dive` — продукта (без поверхности: факты,
голос, бренд, дизайн-система) или одной поверхности (слой страницы, облик
поверхности). Аналитический скилл принимает `<project-slug>` первым
аргументом (`/interface-deep-dive <slug> [<surface>] …`); без аргументов —
пикеры по **человекочитаемым именам**: сначала проект (заголовок из
`vision`), затем поверхность (`surface.name`); у слоя страницы пикер
предлагает только `web` рода `landing` и `site`. Клиент-режим
(`/entrypoint-for-business`) всегда ведёт дружелюбными пикерами «какой
продукт» и «где он работает», без slug.

Новый проект заводит `/project-deep-dive` (копирует форму из
`_template/project/` в новую папку проекта); папки поверхностей под
`interface/`/`screens/`/`fsd/`/`site/`/`design/`/`telegram-bot-flow/`/`mobile/`
заводят их скилы (`/interface-deep-dive`, `/screen-deep-dive`,
`/fsd-deep-dive`, `/design-deep-dive`, `/telegram-bot-flow-deep-dive`,
`/mobile-deep-dive`) при первом заходе на поверхность — каталоги руками не
создаём.

## Каноны слоёв

- [`_template/project/README.md`](_template/project/README.md) — продукт (vision + surface-реестр + kind).
- [`_template/interface/README.md`](_template/interface/README.md) — интерфейс одной поверхности.
- [`_template/screens/README.md`](_template/screens/README.md) — экраны одной поверхности.
- [`_template/fsd/README.md`](_template/fsd/README.md) — FSD-карта одной фронтовой поверхности кабинета (мост к коду `<org>/frontend`).
- [`_template/site/README.md`](_template/site/README.md) — слой страницы одной поверхности сайта или лендинга и файлы уровня продукта (мост к коду `<org>/site`).
- [`_template/design/README.md`](_template/design/README.md) — облик продукта и его поверхностей: бренд, дизайн-система, ассеты, макет, пакет для кода.
- [`_template/telegram-bot-flow/README.md`](_template/telegram-bot-flow/README.md) — диалоги одной bot-поверхности.
- [`_template/mobile/README.md`](_template/mobile/README.md) — карта приложения одной мобильной поверхности (мост к коду `<org>/mobile`).
- [`_template/services/README.md`](_template/services/README.md) — сервисная топология и домены бэкенда.
- [`infrastructure/README.md`](infrastructure/README.md) — ИТ-периметр бизнеса (сервера · рантаймы · общие ресурсы · джобы · размещение).
- [`project-map.md`](project-map.md) — карта стыков между проектами (singleton, бизнес-язык).

## Anti-patterns

- ❌ Данные проекта в `_template/` (там только форма-образец).
- ❌ Дублирование канона в папку проекта (`<slug>/interface/README.md`
  и т.п.) — форма живёт один раз в `_template/`.
- ❌ Папка поверхности (`capability/<surface>.md`, `interface/<surface>/`,
  `screens/<surface>/`, `fsd/<surface>/`, `site/<surface>/`,
  `design/<surface>/`, `telegram-bot-flow/<surface>/`, `mobile/<surface>/`)
  для поверхности, которой нет в реестре `surface.md`.
- ❌ `screens/<surface>/` или `fsd/<surface>/` для мобильной поверхности —
  её композиция и мост к коду живут в `mobile/<surface>/`.
- ❌ `site/<surface>/` у поверхности не рода `landing` или `site`.
- ❌ `interface/`, `screens/`, `fsd/` у поверхности рода `landing` или `site` —
  на их месте слой страницы.
- ❌ `design/<surface>/` у `mobile`, `bot`, `api`, `other` — их облик — токены
  дизайн-системы продукта и голос.
- ❌ Создание каталога проекта или папки поверхности руками вместо скила.
- ❌ Жёсткие slug-валидации между проектом и `business-problem`. Связь
  семантическая (`addresses-problem`), ловит `/cross-audit`.
- ❌ Стык между продуктами бизнеса как обычная внешняя `integration`
  (`target: external`) — для соседнего проекта `target: sibling-project`
  + ребро в `project-map.md`.
- ❌ Домены в корне папки продукта мимо сервиса. Bounded context живёт внутри
  сервиса-владельца: `services/<svc>/domains/<ctx>/`.
- ❌ Размещение (сервер/рантайм) в слоях проекта. «Кто где живёт» — только
  `infrastructure/placement.md`.
