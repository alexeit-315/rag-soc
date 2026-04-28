# HDX Converter

A modular tool for converting HDX documentation to multiple formats (TXT, MD, JSON) with comprehensive metadata extraction.

## Features

- Extracts content from HDX (HTML) files
- Preserves internal links and navigation
- Generates structured metadata in JSON format (schema 1.2)
- Converts to multiple formats: TXT, Markdown, HTML backup
- Validates metadata completeness
- Handles images and tables
- Provides detailed statistics and reporting
- Modular architecture for easy extension

## Текущее состояние
2. Общее описание для и смежных процессов

2.1 Общее описание процесса конвертации

Конвертер преобразует HDX архивы с технической документацией в структурированный JSON формат, пригодный для:
- Индексации в поисковых системах
- RAG (Retrieval-Augmented Generation) ботов
- Автоматической обработки и анализа

**Входные данные:**
- HDX файл (ZIP-архив с HTML файлами документации)

**Выходные данные:**
- `json_data/*.json` — структурированные данные статей
- `meta_data/*.json` — метаданные (заголовки, иерархия, ссылки)
- `md_data/*.md` — Markdown версия для человеческого чтения
- `txt_data/*.txt` — текстовая версия
- `html_backup/*.html` — резервные копии исходных HTML
- `images/*` — скопированные изображения

2.2 Принятые принципиальные решения

2.2.1 Семантическая структура, а не копия HTML

HTML решает задачу форматирования. JSON сохраняет **смысл**, а не оформление. Теги HTML обрабатываются только если несут семантическую нагрузку.

2.2.2 Секции как основные контейнеры

Документ состоит из:
- **Заголовок статьи** (`h1.topicTitle-h1`)
- **Секции** — логические блоки с заголовками (`h2-h6.sectiontitle`)
- **Навигация** — ссылки parent/previous/next

2.2.3 Плоская структура секций

Секции **не могут быть вложены** друг в друга. Все секции находятся на одном уровне в массиве `content`.

2.2.4 Секция Content

Секция с заголовком `"Content"` создается **только** при наличии текста (в широком понимании) вне каких-либо секций. Если весь текст внутри секций — секция Content не создается.

2.2.5 Игнорирование стилевых классов

Классы CSS (`clearfix`, `tableBorder`, `cellrowborder` и т.д.) игнорируются, так как не несут семантики.

2.3 Схема маппинга HTML → JSON

2.3.1 Секции

| HTML | JSON тип | Условие |
|------|----------|---------|
| `div.context` | `section` | Есть заголовок `h4.sectiontitle` |
| `div.steps`, `div.steps-unordered` | `steps` | Есть заголовок |
| `div.example` | `example` | Есть заголовок |
| `div.postreq` | `postrequisite` | Есть заголовок |
| `div.prereq` | `prerequisite` | Есть заголовок |
| `div.result` | `result` | Есть заголовок |
| `div.impactonsystem` | `impact` | Есть заголовок |
| `div.possiblecauses` | `cause` | Есть заголовок |
| `div.note`, `div.caution`, `div.danger`, `div.warning`, `div.notice` | `admonition` | Без заголовка |
| `div.logRefMessage` и связанные | `log_message` | Без заголовка |
| `div.section` | `section` | Есть заголовок |
| `div.clifunc`, `div.cliformat`, `div.cliparam`, `div.cliview`, `div.cliexample` | `section` | Через общую обработку |

2.3.2 Контент внутри секций

| HTML | JSON тип | Особенности |
|------|----------|-------------|
| `<p>` | `paragraph` | Может содержать смешанный контент |
| `<ul>`, `<ol>` | `list` | `list_type`: "unordered"/"ordered" |
| `<li>` | `list_item` | Может содержать вложенные элементы |
| `<a>` (внешняя) | `link` | `link_type: "external"` |
| `<a>` (внутренняя) | `link` | `link_type: "internal"`, href → .json |
| `<pre class="screen">` | `code_block` | `language: "cli"` |
| `<img>` | `image` | `src`, `alt` |
| `<td> | `table` | `caption`, `header`, `rows` |
| `<span>`, текст, форматирование | `text` | Может иметь `semantic_role` |
| `div.fignone` | `figure` | Связывает `img` и `figcap` |

2.3.3 Атрибуты semantic_role для `text`

| HTML класс | semantic_role |
|------------|---------------|
| `cmdname` | `cmdname` |
| `varname` | `varname` |
| `uicontrol` | `uicontrol` |
| `parmname` | `parmname` |
| `keyword` | `keyword` |

2.4 Структура сервиса

```
hdx_converter/
├── cli.py                    # Командная строка, аргументы
├── core/
│   ├── converter.py          # Основной класс конвертера
│   ├── content_processor.py  # Обработка контента (ядро)
│   ├── metadata_manager.py   # Управление метаданными
│   ├── stats_collector.py    # Сбор статистики
│   └── validator.py          # Валидация метаданных
├── parsers/
│   ├── html_parser.py        # Парсинг HTML
│   ├── metadata_parser.py    # Извлечение метаданных
│   ├── navigation_parser.py  # Обработка навигации
│   └── link_processor.py     # Обработка ссылок
├── writers/
│   ├── file_writer.py        # Запись файлов
│   ├── json_writer.py        # Запись JSON
│   ├── markdown_writer.py    # Конвертация в Markdown
│   ├── text_writer.py        # Конвертация в TXT
│   └── html_backup_writer.py # Резервное копирование HTML
├── models/
│   ├── schemas.py            # Pydantic модели
│   ├── config.py             # Конфигурация
│   └── statistics.py         # Модели статистики
└── utils/
    ├── logger.py             # Логирование
    ├── file_utils.py         # Работа с файлами
    ├── naming_utils.py       # Генерация имен
    ├── image_processor.py    # Обработка изображений
    └── path_resolver.py      # Разрешение путей
```

2.5 Основные алгоритмы

2.5.1 Обход контента

```python
def _extract_sections_flat(element, source_file):
    """Рекурсивно извлекает секции, сохраняя плоскую структуру"""
    result = []
    pending_content = []
    
    for child in element.children:
        if is_section(child):
            # Сохраняем накопленный текст как секцию Content
            if pending_content:
                result.append(create_content_section(pending_content))
                pending_content = []
            # Обрабатываем секцию
            result.append(process_section(child))
        elif contains_sections(child):
            # Сохраняем накопленный текст
            if pending_content:
                result.append(create_content_section(pending_content))
                pending_content = []
            # Рекурсивно обрабатываем контейнер
            result.extend(_extract_sections_flat(child))
        else:
            # Накопливаем обычный контент
            pending_content.append(child)
    
    if pending_content:
        result.append(create_content_section(pending_content))
    
    return result
```

2.5.2 Обработка таблиц

Таблицы обрабатываются с поддержкой вложенных элементов:
- Списки (`ul`, `ol`) внутри ячеек
- Блоки кода (`pre.screen`) внутри ячеек
- Ссылки (`a`) внутри ячеек

2.6 Рекомендации для смежных процессов

2.6.1 Индексация

- Использовать поле `content` для извлечения текста
- Поле `links.internal` для построения графа связей
- Поле `navigation` для навигации по иерархии
- `semantic_role` для точного поиска команд, переменных, ключевых слов

2.6.2 RAG бот

- Разбивать документ на секции (каждая секция — отдельный контекст)
- Использовать `type` секции для определения типа контента (`steps`, `example`, `admonition`)
- Использовать `semantic_role` для точного извлечения команд

2.6.3 Адаптация для других наборов данных

При добавлении новых типов HTML тегов:
1. Определить, несут ли они семантическую нагрузку
2. Добавить класс в `_is_section_element` если это секция
3. Добавить обработчик в `_process_section_by_class`
4. Обновить схему JSON и документацию


### Структура метаданных, сохраняемая в JSON для каждой статьи (версия 1.3)
```json
{
  "metadata_version": "1.3",                                 // Версия схемы метаданных (обязательное)
  "source": {                                                // Информация об источнике
    "hdx_filename": "HiSecEngine_USG6000F_V600R024C10_04_en_AEP01098.hdx",
    "html_filename": "vrp_ospf_cfg_0087_EN-US_TASK_0000001176663005.html", // Имя HTML файла статьи с DC.Identifier (обязательное)
    "html_path": "resources\\vrp\\vrp_ospf_cfg_0087_EN-US_TASK_0000001176663005.html", // Путь к HTML файлу относительно корня html_backup (обязательное)
    "extraction_date": "2026-01-15T12:41:44.647260",         // Дата и время извлечения (ISO формат)
    "json_filename": "Enabling OSPF-BGP Synchronization_EN-US_TASK_0000001176663005.json",  // Имя соответствующего JSON файла (обязательное)
    "md_filename": "Enabling OSPF-BGP Synchronization_EN-US_TASK_0000001176663005.md",  // Имя соответствующего MD файла (опционально)
    "hdx_hash": "7724de60461f8f33ea0bf1e3b8ea2368"           // Хеш HDX файла
  },
  "article": {                                               // Метаданные статьи
    "title": "Enabling OSPF-BGP Synchronization",            // Заголовок статьи (обязательное)
    "json_filename": "Enabling OSPF-BGP Synchronization_EN-US_TASK_0000001176663005.json",  // Имя JSON файла (обязательное)
    "dc_identifier": "EN-US_TASK_0000001176663005",          // Уникальный идентификатор документа (DC.Identifier, обязательное)
    "document_type": "configuration_guide",                  // Тип документа: configuration_guide, cli_command, concept
    "language": "en-us",                                     // Язык документа
    "hierarchy": [                                           // Полная цепочка навигации (обязательное)
      {
        "title": "IP Routing Configuration",                 // Заголовок элемента иерархии
        "dc_identifier": "EN-US_CONCEPT_0000001234567890",   // Уникальный идентификатор элемента иерархии
        "html_filename": "ip_routing_cfg_001_EN-US_CONCEPT_0000001234567890.html",  // Имя HTML файла элемента иерархии
        "json_filename": "IP Routing Configuration_EN-US_CONCEPT_0000001234567890.json" // Имя JSON файла элемента иерархии
      },
      // ... остальные элементы иерархии
    ],
    "section_structure": [                                   // Структура разделов статьи
      {
        "section_id": "section_1",                           // ID раздела (если есть в HTML)
        "title": "Context",                                  // Заголовок раздела
        "type": "content"                                    // Тип раздела: content, function, format, parameters, example
      }
    ],
    // ... остальные поля статьи
  },
  // ... technical_metadata, validation без изменений
  "relations": {                                             // Связи с другими статьями
    "parent_article": {                                      // Родительская статья
      "title": "OSPF Configuration",                         // Заголовок родительской статьи
      "dc_identifier": "EN-US_CONCEPT_0000001234567891",     // Уникальный идентификатор родительской статьи (обязательное)
      "html_filename": "ospf_cfg_002_EN-US_CONCEPT_0000001234567891.html", // Имя HTML файла родительской статьи (обязательное)
      "html_path": "resources\\vrp\\ospf_cfg_002_EN-US_CONCEPT_0000001234567891.html", // Путь к HTML файлу родительской статьи (обязательное)
      "json_filename": "OSPF Configuration_EN-US_CONCEPT_0000001234567891.json"  // Имя JSON файла родительской статьи (обязательное)
    },
    "previous_article": {                                    // Предыдущая статья в навигации
      "title": "Previous: Configuring OSPF Stub Areas",      // Заголовок предыдущей статьи
      "dc_identifier": "EN-US_CONCEPT_0000001234567890",     // Уникальный идентификатор предыдущей статьи
      "html_filename": "ospf_cfg_001_EN-US_CONCEPT_0000001234567890.html", // Имя HTML файла предыдущей статьи
      "html_path": "resources\\vrp\\ospf_cfg_001_EN-US_CONCEPT_0000001234567890.html", // Путь к HTML файлу предыдущей статьи
      "json_filename": "Configuring OSPF Stub Areas_EN-US_CONCEPT_0000001234567890.json"  // Имя JSON файла предыдущей статьи
    },
    "next_article": {                                        // Следующая статья в навигации
      "title": "Next: Verifying OSPF-BGP Synchronization",   // Заголовок следующей статьи
      "dc_identifier": "EN-US_TASK_0000001176663006",        // Уникальный идентификатор следующей статьи
      "html_filename": "vrp_ospf_cfg_0088_EN-US_TASK_0000001176663006.html", // Имя HTML файла следующей статьи
      "html_path": "resources\\vrp\\vrp_ospf_cfg_0088_EN-US_TASK_0000001176663006.html", // Путь к HTML файлу следующей статьи
      "json_filename": "Verifying OSPF-BGP Synchronization_EN-US_TASK_0000001176663006.json"  // Имя JSON файла следующей статьи
    },
    "internal_links": [                                      // Внутренние ссылки в статье
      {
        "text": "display ospf peer",                         // Текст ссылки
        "dc_identifier": "EN-US_CMD_0000001234567893",       // Уникальный идентификатор целевой статьи
        "html_filename": "vrp_ospf_cmd_1234_EN-US_CMD_0000001234567893.html", // Имя HTML файла целевой статьи
        "html_path": "resources\\vrp\\vrp_ospf_cmd_1234_EN-US_CMD_0000001234567893.html", // Путь к HTML файлу целевой статьи
        "json_filename": "OSPF Peer Display Commands_EN-US_CMD_0000001234567893.json"  // Имя JSON файла целевой статьи
      }
    ],
    "external_links": [                                      // Внешние ссылки
      {
        "text": "RFC 2328",                                  // Текст ссылки
        "url": "https://tools.ietf.org/html/rfc2328"        // URL внешней ссылки
      }
    ]
  },
  // ... validation
}
```

### Структура данных, сохраняемая в JSON для каждой статьи (версия 1.2)
#### 1. Полная таблица маппинга HTML тегов на типы JSON

1.1 Секции (контейнеры верхнего уровня)

| HTML тег | JSON тип | Где обрабатывается |
|----------|----------|---------------------|
| `div.context` | `section` | `_process_task_section` |
| `div.steps` | `steps` | `_process_steps_section` |
| `div.steps-unordered` | `steps` | `_process_steps_section` |
| `div.example` | `example` | `_process_example_section` |
| `div.postreq` | `postrequisite` | `_process_postrequisite_section` |
| `div.prereq` | `prerequisite` | `_process_prerequisite_section` |
| `div.result` | `result` | `_process_result_section` (**НОВЫЙ**) |
| `div.impactonsystem` | `impact` | `_process_impact_section` (**НОВЫЙ**) |
| `div.possiblecauses` | `cause` | `_process_cause_section` (**НОВЫЙ**) |
| `div.note` | `admonition` | `_process_admonition_section` |
| `div.caution` | `admonition` | `_process_admonition_section` |
| `div.danger` | `admonition` | `_process_admonition_section` |
| `div.warning` | `admonition` | `_process_admonition_section` |
| `div.notice` | `admonition` | `_process_admonition_section` |
| `div.logRefMessage` (и связанные) | `log_message` | `_process_log_message_section` |
| `div.section` | `section` | `_process_section` |
| `div.clifunc`, `cliformat`, `cliparam`, `cliview`, `cliexample` | `section` | `_process_general_content` (через `special_classes`) |
| `div.fignone` | `figure` | `_process_figure_section` (внутри секции) |
| `div.footerNavBar` | `navigation` | `_process_footer_navigation` (отдельно) |

1.2 Базовые типы контента (могут быть вложены в секции)

| HTML тег | JSON тип | Обязательные поля |
|----------|----------|-------------------|
| `<p>` | `paragraph` | `content` |
| `<ul>` | `list` | `list_type` ("unordered"), `items` |
| `<ol>` | `list` | `list_type` ("ordered"), `items` |
| `<li>` | `list_item` | `text` или `content` |
| `<a>` (внутренняя) | `link` | `text`, `href`, `link_type: "internal"` |
| `<a>` (внешняя) | `link` | `text`, `href`, `link_type: "external"` |
| `<pre class="screen">` | `code_block` | `content`, `language: "cli"` |
| `<img>` | `image` | `src`, `alt` |
| `<table> | `table` | `caption`, `header`, `rows` |
| текстовые узлы, `<span>`, `<b>`, `<strong>`, `<i>`, `<em>` | `text` | `content` |

1.3 Атрибуты `semantic_role` для `text`

| HTML класс | semantic_role |
|------------|---------------|
| `cmdname` | `cmdname` |
| `varname` | `varname` |
| `uicontrol` | `uicontrol` |
| `parmname` | `parmname` |
| `keyword` | `keyword` |

---

#### 2. Обновленная схема JSON для данных

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["metadata", "content", "navigation", "links"],
  "properties": {
    "metadata": {
      "type": "object",
      "required": ["source_file", "source_path", "extraction_date", "article_title", "content_type", "version"],
      "properties": {
        "source_file": {"type": "string"},
        "source_path": {"type": "string"},
        "extraction_date": {"type": "string", "format": "date-time"},
        "article_title": {"type": "string"},
        "content_type": {"type": "string", "enum": ["structured_article"]},
        "version": {"type": "string", "enum": ["1.2"]}
      }
    },
    "content": {
      "type": "array",
      "items": {
        "oneOf": [
          {"$ref": "#/definitions/section"},
          {"$ref": "#/definitions/steps"},
          {"$ref": "#/definitions/example"},
          {"$ref": "#/definitions/postrequisite"},
          {"$ref": "#/definitions/prerequisite"},
          {"$ref": "#/definitions/result"},
          {"$ref": "#/definitions/impact"},
          {"$ref": "#/definitions/cause"},
          {"$ref": "#/definitions/admonition"},
          {"$ref": "#/definitions/log_message"}
        ]
      }
    },
    "navigation": {
      "type": "array",
      "description": "Навигационные ссылки (parent, previous, next)",
      "items": {"$ref": "#/definitions/link"}
    },
    "links": {
      "type": "object",
      "required": ["internal", "external"],
      "description": "Все ссылки в документе (включая навигационные)",
      "properties": {
        "internal": {
          "type": "array",
          "items": {"$ref": "#/definitions/link"}
        },
        "external": {
          "type": "array",
          "items": {"$ref": "#/definitions/link"}
        }
      }
    }
  },
  "definitions": {
    "section": {
      "type": "object",
      "required": ["type", "title", "content"],
      "properties": {
        "type": {"type": "string", "enum": ["section"]},
        "title": {"type": "string"},
        "content": {"type": "array", "items": {"$ref": "#/definitions/content_item"}}
      }
    },
    "steps": {
      "type": "object",
      "required": ["type", "title", "content"],
      "properties": {
        "type": {"type": "string", "enum": ["steps"]},
        "title": {"type": "string"},
        "content": {"type": "array", "items": {"$ref": "#/definitions/content_item"}}
      }
    },
    "example": {
      "type": "object",
      "required": ["type", "title", "content"],
      "properties": {
        "type": {"type": "string", "enum": ["example"]},
        "title": {"type": "string"},
        "content": {"type": "array", "items": {"$ref": "#/definitions/content_item"}}
      }
    },
    "postrequisite": {
      "type": "object",
      "required": ["type", "title", "content"],
      "properties": {
        "type": {"type": "string", "enum": ["postrequisite"]},
        "title": {"type": "string"},
        "content": {"type": "array", "items": {"$ref": "#/definitions/content_item"}}
      }
    },
    "prerequisite": {
      "type": "object",
      "required": ["type", "title", "content"],
      "properties": {
        "type": {"type": "string", "enum": ["prerequisite"]},
        "title": {"type": "string"},
        "content": {"type": "array", "items": {"$ref": "#/definitions/content_item"}}
      }
    },
    "result": {
      "type": "object",
      "required": ["type", "title", "content"],
      "properties": {
        "type": {"type": "string", "enum": ["result"]},
        "title": {"type": "string"},
        "content": {"type": "array", "items": {"$ref": "#/definitions/content_item"}}
      }
    },
    "impact": {
      "type": "object",
      "required": ["type", "title", "content"],
      "properties": {
        "type": {"type": "string", "enum": ["impact"]},
        "title": {"type": "string"},
        "content": {"type": "array", "items": {"$ref": "#/definitions/content_item"}}
      }
    },
    "cause": {
      "type": "object",
      "required": ["type", "title", "content"],
      "properties": {
        "type": {"type": "string", "enum": ["cause"]},
        "title": {"type": "string"},
        "content": {"type": "array", "items": {"$ref": "#/definitions/content_item"}}
      }
    },
    "admonition": {
      "type": "object",
      "required": ["type", "title", "content"],
      "properties": {
        "type": {"type": "string", "enum": ["admonition"]},
        "title": {"type": "string"},
        "content": {"type": "array", "items": {"$ref": "#/definitions/content_item"}}
      }
    },
    "log_message": {
      "type": "object",
      "required": ["type", "title", "content"],
      "properties": {
        "type": {"type": "string", "enum": ["log_message"]},
        "title": {"type": "string"},
        "content": {"type": "array", "items": {"$ref": "#/definitions/content_item"}}
      }
    },
    "content_item": {
      "oneOf": [
        {"$ref": "#/definitions/paragraph"},
        {"$ref": "#/definitions/list"},
        {"$ref": "#/definitions/list_item"},
        {"$ref": "#/definitions/link"},
        {"$ref": "#/definitions/code_block"},
        {"$ref": "#/definitions/image"},
        {"$ref": "#/definitions/table"},
        {"$ref": "#/definitions/text"},
        {"$ref": "#/definitions/figure"}
      ]
    },
    "paragraph": {
      "type": "object",
      "required": ["type", "content"],
      "properties": {
        "type": {"type": "string", "enum": ["paragraph"]},
        "content": {"oneOf": [{"type": "string"}, {"type": "array", "items": {"$ref": "#/definitions/content_item"}}]}
      }
    },
    "list": {
      "type": "object",
      "required": ["type", "list_type", "items"],
      "properties": {
        "type": {"type": "string", "enum": ["list"]},
        "list_type": {"type": "string", "enum": ["unordered", "ordered"]},
        "items": {"type": "array", "items": {"$ref": "#/definitions/list_item"}}
      }
    },
    "list_item": {
      "type": "object",
      "required": ["type"],
      "properties": {
        "type": {"type": "string", "enum": ["list_item"]},
        "text": {"type": "string"},
        "content": {"type": "array", "items": {"$ref": "#/definitions/content_item"}}
      }
    },
    "link": {
      "type": "object",
      "required": ["type", "text", "href", "link_type"],
      "properties": {
        "type": {"type": "string", "enum": ["link"]},
        "text": {"type": "string"},
        "href": {"type": "string"},
        "link_type": {"type": "string", "enum": ["internal", "external"]}
      }
    },
    "code_block": {
      "type": "object",
      "required": ["type", "content", "language"],
      "properties": {
        "type": {"type": "string", "enum": ["code_block"]},
        "content": {"type": "string"},
        "language": {"type": "string"}
      }
    },
    "image": {
      "type": "object",
      "required": ["type", "src", "alt"],
      "properties": {
        "type": {"type": "string", "enum": ["image"]},
        "src": {"type": "string"},
        "alt": {"type": "string"}
      }
    },
    "table": {
      "type": "object",
      "required": ["type", "caption", "header", "rows"],
      "properties": {
        "type": {"type": "string", "enum": ["table"]},
        "caption": {"type": "string"},
        "header": {"type": "array", "items": {"type": "string"}},
        "rows": {
          "type": "array",
          "items": {
            "type": "array",
            "items": {
              "oneOf": [
                {"type": "string"},
                {"$ref": "#/definitions/list"},
                {"$ref": "#/definitions/code_block"},
                {"$ref": "#/definitions/link"}
              ]
            }
          }
        }
      }
    },
    "text": {
      "type": "object",
      "required": ["type", "content"],
      "properties": {
        "type": {"type": "string", "enum": ["text"]},
        "content": {"type": "string"},
        "semantic_role": {"type": "string", "enum": ["cmdname", "varname", "uicontrol", "parmname", "keyword"]}
      }
    },
    "figure": {
      "type": "object",
      "required": ["type", "image", "caption"],
      "properties": {
        "type": {"type": "string", "enum": ["figure"]},
        "image": {"$ref": "#/definitions/image"},
        "caption": {"type": "string"}
      }
    }
  }
}
```

#### Ключевые изменения в схеме:

1. **`navigation`** вынесен из `content` в отдельное поле верхнего уровня (массив ссылок)
2. **`metadata.version`** добавлено поле (значение "1.2")
3. **Добавлены новые типы секций**: `result`, `impact`, `cause`
4. **Уточнена вложенность в `table.rows`** - ячейки могут содержать `list`, `code_block`, `link`

#### 3. Текущее состояние реализации схемы конвертации (на 21.04.2026)

### Обновленный анализ результатов конвертации (на основе 6 предоставленных JSON)

#### ✅ РЕШЕННЫЕ ЗАДАЧИ (подтверждено)

| № | Задача | Статус | Где подтверждено |
|---|--------|--------|------------------|
| 1 | **Обработка `div.prereq`** | ✅ | `(Optional) Configuring IP Database...` → `{"type": "prerequisite"}` |
| 2 | **Обработка `div.postreq`** | ✅ | Все 3 примера (PKI, IP Database, CLI-Example) → `{"type": "postrequisite"}` |
| 3 | **Обработка `div.steps`** | ✅ | Во всех task-статьях → `{"type": "steps"}` |
| 4 | **Обработка `div.example`** | ✅ | CLI-Example, PKI примеры → `{"type": "example"}` |
| 5 | **Обработка `div.note` как `admonition`** | ✅ | IP Database, PKI примеры → `{"type": "admonition"}` |
| 6 | **semantic_role для `cmdname`** | ✅ | `Locating Event Traps` → `"semantic_role": "cmdname"` |
| 7 | **semantic_role для `varname`** | ✅ | `Locating Event Traps` → `"semantic_role": "varname"` |
| 8 | **Таблицы с вложенными списками** | ✅ | `AD Packets` → таблицы содержат `list` в ячейках |
| 9 | **`div.fignone` как `figure`** | ✅ | Во всех статьях с рисунками |
| 10 | **`navigation` отдельным полем** | ✅ | Во всех JSON |
| 11 | **`version: "1.2"`** | ✅ | Во всех JSON |
| 12 | **`result` тип** | ✅ | `SM2 Digital Envelope` → `{"type": "result"}` |

#### ⚠️ ЧАСТИЧНО РЕШЕННЫЕ

| № | Задача | Проблема |
|---|--------|----------|
| 1 | **Структура `content`** | Весь контент обернут в `{"type": "section", "title": "Content"}` - избыточно |
| 2 | **Заголовки секций как `text`** | `AD Packets`: "Kerberos Packet Format" - `text`, не заголовок секции |
| 3 | **`div.result`** | ✅ РЕШЕНО (SM2 Digital Envelope) |
| 4 | **`div.impactonsystem`** | Не проверено (нет в примерах) |
| 5 | **`div.possiblecauses`** | Не проверено (нет в примерах) |
| 6 | **`div.logRef*`** | Не проверено (нет в примерах) |

#### 📋 ИТОГОВЫЙ ВЕРДИКТ

| Категория | Количество |
|-----------|------------|
| ✅ Полностью решено | 12 |
| ⚠️ Частично / Требует внимания | 2 |
| ❌ Не проверено (нет в примерах) | 3 |

**Основные замечания к текущей реализации:**

1. **Избыточная секция `{"type": "section", "title": "Content"}`** - все содержимое статьи обернуто в одну секцию, что нарушает структуру. Должны быть отдельные секции для Context, Procedure, Example и т.д.

2. **Заголовки секций в `AD Packets`** представлены как `{"type": "text"}`, а не как заголовки внутри `section`

3. **Остальные не проверенные типы** (`impactonsystem`, `possiblecauses`, `logRef*`) требуют тестирования на реальных данных

## Установка

### Создание и активация виртуального окружения
```bash
# Перейдите в директорию проекта
cd /path/to/rag-soc-core/services/rag-soc-converter

# Создание виртуального окружения
python3 -m venv venv_converter

# Активация виртуального окружения
# Для Windows (GitBash):
. venv_converter/Scripts/activate
```

### Установка зависимостей
```bash
# Убедитесь, что виртуальное окружение активировано
# В командной строке должно быть (venv_converter)

# Установка зависимостей
pip install fastapi uvicorn kafka-python prometheus-client

# Для работы с S3 (если нужно)
pip install boto3

# Если есть файл requirements.txt (рекомендованный способ)
pip install -r requirements.txt

pip install -e .
```

### Проверка установки
```bash
# Проверка установленных пакетов
pip list | grep -E "fastapi|uvicorn|kafka|prometheus"

# Ожидаемый вывод:
# fastapi              0.104.0
# kafka-python         2.0.2
# prometheus-client    0.19.0
# uvicorn              0.24.0
```

### Сборка контейнера
```bash
# Создание директорий для данных
mkdir -p /tmp/converter_input /tmp/converter_output

# Сборка образа
docker build -t rag-soc-converter:1.0.8 .
```

## Запуск API сервера

### Вариант 1: Минимальный запуск (без Kafka)
```bash
# Из корневой директории проекта
python -m hdx_converter.cli api --host 0.0.0.0 --port 8080
```

### Вариант 2: С указанием уровня логирования
```bash
# DEBUG режим для отладки
python -m hdx_converter.cli api --host 0.0.0.0 --port 8080 --log-level 3
```

### Вариант 3: С включенной Kafka интеграцией
```bash
# С локальным Kafka
python -m hdx_converter.cli api \
  --host 0.0.0.0 \
  --port 8080 \
  --kafka-enabled \
  --kafka-bootstrap-servers localhost:9092 \
  --log-level 3
```

### Вариант 4: В docker с выключенной Kafka
```bash
# Запуск контейнера
docker run -d \
  --name rag-soc-converter \
  -p 8080:8080 \
  -v /tmp/converter_input:/data/input:ro \
  -v /tmp/converter_output:/data/output \
  -e KAFKA_ENABLED=false \
  rag-soc-converter:1.0.8

# Просмотр логов
docker logs rag-soc-converter

# Остановка
docker stop rag-soc-converter 2>/dev/null || true

# Удаление
docker rm rag-soc-converter 2>/dev/null || true
docker rmi rag-soc-converter:1.0.8 2>/dev/null || true
```

### Вариант 5: Через docker compose c выключенной Kafka (рекомендованный способ)
```bash
# Запуск в фоне
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down

# Перезапуск
docker-compose restart
```

## Ручное развертывание в тестовой среде (Kubernetes)


### **Шаг 1. Клонирование репозитория на сервер**

```bash
cd ~
git clone https://github.com/alexeit-315/rag-soc-core.git
cd rag-soc-core
```

Убедитесь, что Dockerfile находится в подкаталоге `rag-soc-converter`:

```bash
ls -la services/rag-soc-converter/
```

Должен быть файл `Dockerfile`.

---

### **Шаг 2. Сборка Docker-образа локально**

Перейдите в директорию с Dockerfile и соберите образ:

```bash
cd services/rag-soc-converter
docker build -t rag-soc-converter:test .
```

Процесс займет несколько минут (будет скачиваться Python-образ и зависимости из `requirements.txt`).

После сборки проверьте:

```bash
docker images | grep rag-soc-converter
```

---

### **Шаг 3. Загрузка образа в kind-кластер**

**Важно:** чтобы узнать имя текущего кластера:

```bash
kind get clusters
```

kind не использует Docker-демон напрямую для запуска pods. Образ нужно загрузить в kind (для кластера rag-test):

```bash
kind load docker-image rag-soc-converter:test --name rag-test
```

---

### **Шаг 4. Создание PV и PVC**

#### 💾 4.1. PV (kind-aware local disk)

```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: PersistentVolume
metadata:
  name: converter-pv
spec:
  capacity:
    storage: 100Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteOnce
  storageClassName: local-hdd
  persistentVolumeReclaimPolicy: Retain
  local:
    path: /mnt/data/converter
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values:
          - rag-test-worker
EOF
```

#### 💾 4.2 Создание каталога на ноде (kind-aware local disk)
```bash
kubectl run --restart=Never --image=busybox converter-dir -n data-infra --overrides='
{
  "spec": {
    "nodeName": "rag-test-worker",
    "containers": [{
      "name": "creator",
      "image": "busybox",
      "command": ["sh", "-c", "mkdir -p /mnt/data/converter && chmod 777 /mnt/data/converter && echo done"]
    }],
    "restartPolicy": "Never"
  }
}'
```

#### 💾 4.3 Создание каталога на хосте

```bash
# Создание директории на хосте для Converter
sudo mkdir -p /mnt/data/k8s-storage/converter
sudo chmod 777 /mnt/data/k8s-storage/converter
```

---

#### 💾 4.4 Создание файла `converter-pvc.yaml`:

```bash
cat <<EOF > converter-pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: rag-converter-storage
  namespace: data-plane
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: local-hdd
  resources:
    requests:
      storage: 100Gi
  volumeName: converter-pv
EOF
```

Применение:

```bash
kubectl apply -f converter-pvc.yaml
```

Проверка:

```bash
kubectl get pv
kubectl get pvc -n data-plane
```

Статус должен быть `Bound`.

---

### **Шаг 5. Создание Deployment для сервиса**

Создайте файл `converter-deployment.yaml` с двумя вариантами параметризации (выберите один — я покажу оба):

#### **Вариант А: через аргументы командной строки (без args, запускаем по умолчанию)**

```bash
cat <<EOF > converter-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-soc-converter
  namespace: data-plane
spec:
  replicas: 1
  selector:
    matchLabels:
      app: rag-soc-converter
  template:
    metadata:
      labels:
        app: rag-soc-converter
    spec:
      nodeSelector:
        kubernetes.io/hostname: rag-test-worker
      tolerations:
      - key: "node.kubernetes.io/not-ready"
        operator: "Exists"
        effect: "NoExecute"
        tolerationSeconds: 300
      containers:
      - name: converter
        image: rag-soc-converter:test
        imagePullPolicy: IfNotPresent
        # Не передаем args — используем CMD из Dockerfile
        # Dockerfile CMD: ["hdx-converter-api", "--host", "0.0.0.0", "--port", "8080"]
        ports:
        - containerPort: 8080
          name: http
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "1"
            memory: "2Gi"
        volumeMounts:
        - name: storage
          mountPath: /data
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
      volumes:
      - name: storage
        persistentVolumeClaim:
          claimName: rag-converter-storage
EOF
```
#### **Вариант Б: через переменные окружения (env)**

Если сервис поддерживает env-переменные (например, `CONVERTER_HOST`, `CONVERTER_PORT`), используйте этот вариант:

```bash
cat <<EOF > converter-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-soc-converter
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: rag-soc-converter
  template:
    metadata:
      labels:
        app: rag-soc-converter
    spec:
      nodeSelector:
        kubernetes.io/hostname: rag-test-worker
      containers:
      - name: converter
        image: rag-soc-converter:test
        imagePullPolicy: IfNotPresent
        env:
        - name: CONVERTER_HOST
          value: "0.0.0.0"
        - name: CONVERTER_PORT
          value: "8080"
        ports:
        - containerPort: 8080
          name: http
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "1"
            memory: "2Gi"
        volumeMounts:
        - name: storage
          mountPath: /data
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
      volumes:
      - name: storage
        persistentVolumeClaim:
          claimName: rag-converter-storage
EOF
```

**Примените выбранный вариант:**

```bash
kubectl apply -f converter-deployment.yaml
```

---

### **Шаг 6. Создание Service для доступа с хоста и по сети**

Создайте файл `service.yaml` (NodePort для доступа с хоста):

```bash
cat <<EOF > converter-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: rag-soc-converter-svc
  namespace: data-plane
spec:
  type: NodePort
  selector:
    app: rag-soc-converter
  ports:
  - port: 8080
    targetPort: 8080
    nodePort: 30081
    protocol: TCP
EOF
```

Примените:

```bash
kubectl apply -f converter-service.yaml
```

---

### **Шаг 7. Проверка состояния развертывания**

```bash
kubectl get pods -n data-plane
kubectl get deployments -n data-plane
kubectl get svc -n data-plane
kubectl get pvc -n data-plane
```

Дождитесь, пока pod перейдет в статус `Running`:

```bash
kubectl wait --for=condition=ready pod -l app=rag-soc-converter --timeout=120s
```

---

### **Шаг 8. Проверка работоспособности сервиса**

#### **Проверка через localhost (с хоста)**

```bash
curl -v http://localhost:30080/health
```

Ожидаемый ответ: HTTP 200, JSON `{"status": "healthy", "version": "1.0.0", "components": {}}`

```bash
curl -v http://localhost:30080/ready
```

Ожидаемый ответ: HTTP 200, JSON `{"ready": true, "checks": {...}}` или `503`, если зависимости не готовы (в тестовой среде без Kafka/S3 это нормально).

#### **Проверка метрик**

```bash
curl http://localhost:30080/metrics
```

Должен вернуться текст в формате Prometheus.

#### **Проверка API конвертации (опционально)**

```bash
curl -X POST http://localhost:30080/convert \
  -H "Content-Type: application/json" \
  -d '{"source_uri": "file:///data/test.hdx", "log_level": 2}'
```

Ожидается HTTP 202 и `job_id`.

---

### **Шаг 9. Просмотр логов (при необходимости)**

```bash
kubectl logs -l app=rag-soc-converter -n data-plane --tail=50
```

---

## **Итог**

Сервис `rag-soc-converter` должен быть:
- Запущен в существующем kind-кластере
- Доступен по адресу `http://<IP_сервера>:30080` или `http://localhost:30080`
- С PVC 100 ГБ
- С лимитами CPU 1, RAM 2 ГБ
- С liveness и readiness probes

---

**Если на каком-то шаге возникает ошибка — остановитесь, скопируйте вывод терминала и покажите мне.**



## Тестирование

### Проверка работоспособности

В другом терминале выполните проверку

```bash
# Проверка health
curl http://localhost:8080/health

# Ожидаемый ответ:
# {"status":"healthy","version":"1.0.0","components":{}}

# Проверка ready
curl http://localhost:8080/ready

# Ожидаемый ответ:
# {"ready":true,"checks":{"object_storage":true,"kafka":true}}

# Проверка OpenAPI документации
# Откройте в браузере: http://localhost:8080/docs
```

### Тестирование API

#### Запуск конвертации

```bash
# Создайте тестовый HDX файл или используйте существующий
# Запустите конвертацию
curl -X POST http://localhost:8080/api/v1/convert \
  -H "Content-Type: application/json" \
  -d '{
    "source_uri": "../../source/HiSecEngine_USG6000F_V600R024C10_04_en_AEP01098.hdx",
    "output_uri": "../../../../output",
    "log_level": 2
  }'
```

Ожидаемый вывод:

``` json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "source_uri": "/path/to/your/test.hdx",
  "output_uri": "/path/to/output",
  "created_at": "2024-03-27T10:00:00Z"
}
```


#### Проверка статуса задачи

```bash
# Замените JOB_ID на полученный из предыдущего ответа
curl http://localhost:8080/api/v1/convert/JOB_ID/status
```

#### Получение списка задач

```bash
# Все задачи
curl http://localhost:8080/api/v1/convert

# Только завершенные
curl "http://localhost:8080/api/v1/convert?status=completed"

# С пагинацией
curl "http://localhost:8080/api/v1/convert?limit=10&offset=0"
```


