# 02-site-types — типы сайтов и страниц, словарь системы, замер живых страниц

Владельцы: B (типы, словарь, таблица соответствия — волна 1; v1 — J, волна 3), M (замер живых страниц — волна 1).

## Файлы

| Файл | Что | Агент |
|---|---|---|
| `01-site-and-page-taxonomy.md` | 9 типов сайтов и 33 типа страниц: цель, действие, трафик, длина и формы, обязательные страницы, право, примеры; дерево выбора по брифу; пограничные случаи (372 строки) | B |
| `02-vocabulary-and-crosswalk.md` | принципы словаря, 15 пространств имён, как добавлять id, сведение с text и соседями, предложения соседям, `vocab_lint.py` в конвейере, S0 для сестёр (363 строки) | B |
| `vocabulary.yaml` | словарь v1 (released): 445 id в 17 пространствах — `site_type`, `page_type`, `section_role`, `block_family`, `block`, `slot_kind`, `slot`, `macrostructure`, `first_screen_policy`, `action`, `awareness`, `traffic_temperature`, `traffic_source`, `jurisdiction`, `ambition_level`, `conversion_channel`, `procedure_step`; v0 r2 — 406 id | B, J |
| `crosswalk.tsv` | 709 строк соответствия словарям text, ai-media, claude-design, 3d, ux, Hallmark, `landing.csv`, Relume, Tilda, schema.org, Unbounce и карточке брифа jack-roberts; сверяет `../../../scripts/site/vocab_lint.py --check-crosswalk` | B |
| `03-live-pages-measured.md`, `pages.csv` | замер 72 живых страниц × десктоп и телефон (`page_anatomy.py` v1.1): секции и роли, призывы, формы и согласия, шапка и подвал, мета и JSON-LD, трекинг до выбора и cookie-баннеры, LCP, CLS, TBT, лабораторный INP, текст без JS; точность классификатора (M/04); выжимка 22 правил; 144 строки CSV × 132 колонки (`valid`, `speed_valid`, `seg_flag`) | M, M2 |

Утилита: `../../scripts/site/vocab_lint.py` (id вне словаря в YAML, JSON, Markdown; `--selftest`). Опыты: `99-raw/experiments/B/`.

## Выжимка

1. Тип — две оси: `site_type` (весь сайт) и `page_type` (страница); форма (`macrostructure`) и уровень подачи — отдельно.
2. Сначала главное действие (`action`), потом тип: одна посадочная — одно macro-действие.
3. Приоритеты заказчика: `landing-lead-services` / `services-site`, `landing-saas` / `saas-marketing-site`,
   `landing-campaign` (L2), `corporate-site`.
4. У каждой формы — `thank-you-page` и ссылка на политику ПД (152-ФЗ ст. 18.1 ч. 2); у сайта — `legal-page` и 404.
5. Трафик Директа: без pop-up и pop-under, реквизиты для тематик из списка площадки.
6. Id — только из `vocabulary.yaml`, kebab-case; не переименовываются (deprecated + замена); новые — через «## Для B / J».
7. Роль секции ≠ блок; раскладка — вариант блока (E); текстовые слоты site = `slot_type` text (69 из 69 equal).
8. Слот `data` — ссылка на факт `fact:<id>`; значения `treatment` и уровней — creative.
9. Чужой термин → наш id — по `crosswalk.tsv` (equal → narrower → related → broader).
10. Проверка перед сдачей любого YAML базы: `python3 ../../scripts/site/vocab_lint.py <файлы>`.
