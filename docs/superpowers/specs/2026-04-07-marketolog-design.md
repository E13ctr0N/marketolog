# Marketolog - AI-маркетолог для бизнеса в Рунете

**Дата:** 2026-04-07
**Статус:** Draft

---

## 1. Обзор продукта

**Marketolog** — MCP-сервер на Python + система ролевых промптов для Claude. Универсальный AI-маркетолог, ориентированный на Рунет (Яндекс, VK, Telegram, MAX, Дзен). Подключается к Claude Desktop, Claude Code или claude.ai.

### Ценностное предложение

Бизнес получает "маркетолога в терминале" — агент анализирует проект, предлагает стратегию продвижения, выполняет задачи (SEO-аудит, контент-план, публикации в соцсети) после одобрения. Не нужен отдельный UI — всё через диалог с Claude.

### Целевая аудитория

- Соло-предприниматели и инди-разработчики
- Малый и средний бизнес
- Любой бизнес без выделенного маркетолога или с ограниченным бюджетом на маркетинг

### Режим работы

Стратег + исполнитель. Claude с промптами маркетолога:
1. Анализирует контекст проекта
2. Предлагает план действий
3. Ждёт одобрения
4. Выполняет через MCP-инструменты
5. Отчитывается о результатах

Агент адаптирует глубину рекомендаций под масштаб проекта: бюджет, размер команды, стадию развития.

---

## 2. Архитектура

### Высокоуровневая схема

```
Пользователь
    |
Claude (с системными промптами маркетолога)
    |
MCP-сервер "Marketolog" (один процесс, модульный внутри)
    |
    +-- Core           — проекты, контекст, конфигурация
    +-- Modules
    |   +-- SEO        — аудит, ключевые слова, позиции, конкуренты
    |   +-- Content    — контент-план, генерация, оптимизация
    |   +-- SMM        — VK, Telegram, MAX, Дзен
    |   +-- Analytics  — Яндекс.Метрика, Google Search Console
    |   +-- Strategy   — ЦА, позиционирование, маркетинг-план
    |
    +-- Prompts        — ролевые md-файлы
    +-- Utils          — кэш, парсинг, авторизация
```

### Принципы архитектуры

- **Один MCP-сервер** — простота для пользователя (один конфиг, один процесс)
- **Внутренняя модульность** — каждый модуль в своём Python-пакете, изолирован и тестируем
- **Мультипроектность** — YAML-файлы с контекстом проекта, переключение через tool
- **Graceful degradation** — если API-ключ не настроен, инструмент не падает, а возвращает инструкцию по настройке
- **Кросс-модульное взаимодействие** — модули могут использовать данные друг друга (SEO-данные для контента, контекст проекта для всех)
- **ToolAnnotations на каждом инструменте** — каждый tool аннотируется по спецификации MCP 2025-03-26: `readOnlyHint`, `destructiveHint`, `idempotentHint`. Это позволяет Claude автоматически одобрять безопасные вызовы и запрашивать подтверждение на мутирующие/деструктивные (публикации, удаления). Без аннотаций Claude либо спрашивает на каждый вызов, либо пропускает всё
- **Типизированные параметры** — все параметры tools описываются через `Annotated[type, Field(description=..., pattern=..., examples=[...])]` (Pydantic). Это создаёт self-documenting JSON schemas, которые Claude использует для корректного вызова инструментов
- **CSV по умолчанию для табличных данных** — инструменты, возвращающие таблицы (позиции, ключевые слова, метрики, статистика), форматируют ответ в CSV вместо JSON. Это экономит 40-60% токенов контекста. Утилита `format_tabular()` в `utils/formatting.py` конвертирует `list[dict]` → CSV-строку
- **Retry с exponential backoff** — все HTTP-запросы к внешним API проходят через утилиту `fetch_with_retry()` в `utils/http.py`. Автоматический retry при 429 (rate limit) и 5xx ошибках с экспоненциальной задержкой (1s, 2s, 4s, макс 3 попытки). Предотвращает сбои при временных проблемах API

---

## 3. Технический стек

| Компонент | Технология | Версия |
|---|---|---|
| Язык | Python | 3.11+ |
| MCP SDK | FastMCP (`fastmcp`) | 3.0+ |
| HTTP-клиент | `httpx` (async) | — |
| Парсинг HTML | `beautifulsoup4` + `lxml` (SEO-аудит, анализ страниц) | — |
| Семантический поиск | Exa API (опционально) | — |
| Хранение проектов | YAML-файлы (`pyyaml`) | — |
| Кэширование | Файловый TTL-кэш (без внешних зависимостей) | — |
| Тесты | `pytest` + `pytest-asyncio` | — |
| Пакетирование | `pyproject.toml` + `uv` | — |

### Внешние API

| API | Назначение | Авторизация |
|---|---|---|
| Яндекс.Метрика | Трафик, поведение, конверсии | OAuth 2.0 (Яндекс ID) |
| Яндекс.Вебмастер | Индексация, ошибки, поисковые запросы | OAuth 2.0 (Яндекс ID, scopes: `webmaster:hostinfo`, `webmaster:verify`) |
| Яндекс.Wordstat API | Частотность ключевых слов, топ запросов, динамика, регионы | OAuth 2.0 (Яндекс ID), бесплатно по заявке. Base URL: `api.wordstat.yandex.net`. Лимиты: 10 rps, 1000 req/день |
| Google Search Console | Запросы, клики, позиции, CTR | Google Service Account. До 25K строк/запрос, 200 req/100s, задержка данных 2-3 дня, хранение 16 месяцев |
| Google PageSpeed Insights v5 | Core Web Vitals (LCP, CLS, TBT, FCP), производительность, рекомендации | `GET pagespeedonline.googleapis.com/pagespeedonline/v5/runPagespeed`. API key опционален (увеличивает квоту). Бесплатно |
| VK API | Публикация постов, статистика сообществ | VK API Token (методы: `wall.post`, `stats.get`) |
| Telegram Bot API | Публикация в каналы, статистика | Bot Token (через BotFather) |
| MAX Bot API | Публикация в каналы, статистика | Bot Token (через dev.max.ru), `Authorization` header, base URL: `platform-api.max.ru`, Python: `max-messenger/max-botapi-python` (MIT, официальный) |
| Дзен | Публикация статей (через Telegram-синхробот `@zen_sync_bot`) | Нет открытого API. Работает через кросспостинг из Telegram |
| Яндекс.Поиск API v2 | Проверка позиций сайта в Яндексе (легальный способ) | API-ключ Yandex Cloud + Folder ID. Base URL: `https://searchapi.yandex.net/v2`. До 1000 req/день бесплатно. Параметры: `query`, `lr` (регион), `page` |
| Exa | Семантический поиск, исследование конкурентов, анализ контента | Exa API key (опционально). $7/1k search, $1/1k contents, 1000 req/мес бесплатно. Python SDK: `exa-py` |
| Google Trends | Анализ трендов | Exa API как основной источник трендов. `pytrends-modern` (MIT, v0.2.5) — опциональная зависимость (требует Selenium/DrissionPage, тяжёлые deps, 11 stars). Устанавливается отдельно: `pip install marketolog[trends]`. Без неё `trend_research` работает только через Exa |

### Авторизация Яндекс API

Используется единый OAuth-токен Яндекс ID. Пользователь:
1. Создаёт приложение на oauth.yandex.ru с нужными scopes
2. Получает токен по ссылке `https://oauth.yandex.ru/authorize?response_type=token&client_id=<ID>`
3. Вводит токен в конфигурацию Marketolog

Один токен покрывает Метрику и Вебмастер (при наличии нужных scopes).

**Wordstat API — отдельная регистрация:** Wordstat требует создания отдельного приложения (ClientID) на oauth.yandex.ru + подачу заявки на доступ к API. Одобрение ~24 часа. После одобрения OAuth-токен получается стандартным способом, но приложение должно быть одобрено именно для Wordstat. Это значит пользователю может понадобиться два OAuth-токена: один для Метрики/Вебмастера, другой для Wordstat (или одно приложение с обоими доступами, если Яндекс одобрит).

---

## 4. Структура проекта

```
marketolog/
├── src/marketolog/
│   ├── __init__.py
│   ├── __main__.py              # точка входа: python -m marketolog
│   ├── server.py                # FastMCP сервер, регистрация tools
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── projects.py          # CRUD проектов, переключение
│   │   ├── config.py            # загрузка конфигурации, API-ключи
│   │   └── context.py           # контекст активного проекта
│   │
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── seo/
│   │   │   ├── __init__.py
│   │   │   ├── audit.py         # технический SEO-аудит
│   │   │   ├── ai_seo.py        # проверка готовности к AI-поисковикам
│   │   │   ├── keywords.py      # keyword research + кластеризация
│   │   │   ├── positions.py     # проверка позиций
│   │   │   └── competitors.py   # анализ конкурентов, content gap
│   │   ├── content/
│   │   │   ├── __init__.py
│   │   │   ├── planner.py       # контент-план
│   │   │   ├── generator.py     # генерация текстов (article, post, meta, repurpose)
│   │   │   ├── optimizer.py     # SEO-оптимизация текста
│   │   │   └── analyzer.py      # анализ контента страницы
│   │   ├── smm/
│   │   │   ├── __init__.py
│   │   │   ├── telegram.py      # Telegram Bot API
│   │   │   ├── vk.py            # VK API
│   │   │   ├── max.py           # MAX Bot API
│   │   │   ├── dzen.py          # Дзен (обёртка над telegram_post)
│   │   │   ├── trends.py        # Google Trends, анализ трендов
│   │   │   └── calendar.py      # smm_calendar, best_time_to_post
│   │   ├── analytics/
│   │   │   ├── __init__.py
│   │   │   ├── metrika.py       # Яндекс.Метрика API (metrika_report, metrika_goals, traffic_sources, funnel_analysis)
│   │   │   ├── search_console.py # Google Search Console API
│   │   │   ├── ai_referral.py   # трафик с AI-поисковиков
│   │   │   ├── utm.py           # generate_utm — UTM-разметка ссылок
│   │   │   └── digest.py        # weekly_digest
│   │   └── strategy/
│   │       ├── __init__.py
│   │       ├── audience.py      # анализ ЦА (ICP)
│   │       ├── positioning.py   # позиционирование, УТП, channel_recommendation
│   │       ├── competitors.py   # competitor intelligence, brand_health, ai_visibility
│   │       └── planning.py      # маркетинг-план
│   │
│   ├── prompts/
│   │   ├── strategist.md        # основная роль маркетолога
│   │   ├── seo_expert.md        # роль SEO-специалиста
│   │   ├── content_writer.md    # роль контент-маркетолога
│   │   ├── smm_manager.md       # роль SMM-менеджера
│   │   └── analyst.md           # роль аналитика
│   │
│   └── utils/
│       ├── __init__.py
│       ├── cache.py             # файловый TTL-кэш
│       ├── parsing.py           # парсинг HTML, извлечение данных
│       ├── formatting.py        # format_tabular() — CSV-формат для табличных ответов
│       ├── http.py              # fetch_with_retry() — HTTP с exponential backoff
│       └── auth.py              # управление токенами + встроенный OAuth-флоу
│
├── tests/
│   ├── test_core/
│   ├── test_modules/
│   │   ├── test_seo/
│   │   ├── test_content/
│   │   ├── test_smm/
│   │   ├── test_analytics/
│   │   └── test_strategy/
│   └── conftest.py
│
├── pyproject.toml
├── .env.example
└── README.md
```

---

## 5. Модуль Core — управление проектами

### Tools

| Tool | Параметры | Описание |
|---|---|---|
| `create_project` | `name`, `url`, `niche`, `description` | Создаёт новый проект |
| `switch_project` | `name` | Переключает активный проект |
| `list_projects` | — | Список всех проектов |
| `update_project` | `field`, `value` | Обновляет данные проекта |
| `delete_project` | `name` | Удаляет проект (YAML-файл). `destructiveHint=True` — Claude запрашивает подтверждение |
| `get_project_context` | — | Полный контекст текущего проекта |

### Структура проекта (YAML)

Хранится в `~/.marketolog/projects/<name>.yaml`:

```yaml
name: "My SaaS"
url: "https://my-saas.ru"
niche: "управление проектами"
description: "Таск-трекер для малых команд"

target_audience:
  - segment: "фрилансеры"
    pain: "хаос в задачах"
  - segment: "малые команды 3-10 чел"
    pain: "нет единого места для задач"

competitors:
  - name: "Trello"
    url: "https://trello.com"
  - name: "YouGile"
    url: "https://yougile.com"

tone_of_voice: "дружелюбный, без канцелярита, на ты"

social:
  telegram_channel: "@mysaas_channel"
  telegram_dzen_channel: "@mysaas_dzen"  # канал с привязанным @zen_sync_bot для кросспостинга в Дзен
  vk_group: "mysaas"
  max_channel: "@mysaas_max"

seo:
  main_keywords:
    - "таск трекер"
    - "управление задачами"
  yandex_metrika_id: "12345678"
  webmaster_host: "https://my-saas.ru"
  search_console_url: "https://my-saas.ru"
```

Контекст проекта автоматически передаётся во все инструменты. При вызове `keyword_research()` агент уже знает нишу, конкурентов и текущие ключевые слова.

---

## 6. Модуль SEO

### Tools

| Tool | Параметры | Описание | Источник данных |
|---|---|---|---|
| `seo_audit` | `url?` | Технический аудит: скорость (Core Web Vitals), мета-теги, заголовки, битые ссылки, robots.txt, sitemap, schema markup (JSON-LD), canonical tags | PageSpeed API + парсинг (`beautifulsoup4`) |
| `ai_seo_check` | `url?` | Проверка готовности к AI-поисковикам: доступность для AI-краулеров (GPTBot, ClaudeBot, PerplexityBot), наличие llms.txt, schema markup, контент без JS | Парсинг robots.txt + анализ HTML |
| `keyword_research` | `seed_keywords?`, `count?` | Подбор ключевых слов: частотность, топ запросов, похожие формулировки, динамика | Яндекс.Wordstat API (официальный) |
| `keyword_cluster` | `keywords` | Кластеризация ключевых слов по интенту | Анализ поисковой выдачи |
| `check_positions` | `keywords?` | Позиции сайта в Яндекс и Google | Яндекс.Поиск API v2 (основной) + Яндекс.Вебмастер API (популярные запросы). Google — через Google Search Console (средняя позиция) |
| `analyze_competitors` | `competitor_urls?` | Анализ конкурентов: запросы, контент, структура | Парсинг + Exa (если доступен) |
| `content_gap` | `competitor_urls?` | Ключевые слова, по которым ранжируются конкуренты, но не ты | Сравнение выдачи |
| `webmaster_report` | — | Отчёт Яндекс.Вебмастера: индексация, ошибки, запросы | Яндекс.Вебмастер API |

### API Яндекс.Wordstat (официальный, с июня 2025)

- Base URL: `https://api.wordstat.yandex.net`
- Протокол: HTTPS, метод POST, формат JSON
- Авторизация: `Authorization: Bearer <OAuth-token>` (тот же Яндекс ID OAuth)
- Требуется заявка на доступ (одобрение ~24 часа)
- Лимиты: 10 запросов/сек, 1000 запросов/день (можно запросить увеличение)
- Методы:
  - `POST /v1/topRequests` — топ популярных и похожих формулировок по ключевому слову
  - `POST /v1/dynamics` — динамика интереса к теме (сезонность, тренды)
  - `POST /v1/regions` — срезы по регионам
  - `POST /v1/getRegionsTree` — дерево всех регионов Яндекса (не расходует квоту)
- Доступные данные: частотность, топ формулировок, динамика, срезы по регионам/устройствам/периодам
- Поддерживает язык запросов Wordstat (операторы `"`, `!`, `+`, `-`)

**Важно:** Парсинг Wordstat больше не нужен — есть официальный API. Это значительно надёжнее и не нарушает ToS.

### API Яндекс.Вебмастер

- Base URL: `https://api.webmaster.yandex.net/v4`
- Авторизация: `Authorization: OAuth <token>`
- Ключевые endpoints:
  - `GET /user/{user_id}/hosts` — список сайтов
  - `GET /user/{user_id}/hosts/{host_id}/search-queries/popular` — популярные запросы
  - `GET /user/{user_id}/hosts/{host_id}/diagnostics` — ошибки индексации
  - `GET /user/{user_id}/hosts/{host_id}/indexing/history` — история индексации

### API Яндекс.Метрика (для SEO-метрик)

- Base URL: `https://api-metrika.yandex.net`
- Полезные presets:
  - `sources_search_phrases` — поисковые фразы
  - `sources_summary` — источники трафика
- Пример запроса:
  ```
  GET /stat/v1/data?preset=sources_search_phrases&id={counter_id}
  ```

---

## 7. Модуль Content

### Tools

| Tool | Параметры | Описание |
|---|---|---|
| `content_plan` | `period?`, `topics_count?` | Контент-план: темы, форматы, ключевые слова, календарь |
| `generate_article` | `topic`, `keywords?`, `length?` | SEO-оптимизированная статья в tone of voice проекта |
| `generate_post` | `platform`, `topic?` | Пост для площадки (Telegram, VK, MAX, Дзен) |
| `optimize_text` | `text`, `target_keywords` | SEO-оптимизация текста: плотность ключей, структура, мета |
| `analyze_content` | `url` | Анализ контента страницы: читаемость, SEO-оценка |
| `generate_meta` | `url_or_text`, `keywords?` | Генерация title, description, H1 |
| `repurpose_content` | `text`, `formats?` | Репёрпосинг: статья → посты для Telegram/VK/MAX/Дзен, карусель, видео-скрипт |

### Кросс-модульные связи

- Получает ключевые слова из **SEO-модуля**
- Использует tone of voice из **Core** (контекст проекта)
- Готовый контент адаптируется **SMM-модулем** под площадки

### Как работает генерация текста

Tools `generate_article`, `generate_post`, `repurpose_content` **не генерируют текст сами** — они собирают контекст (SEO-данные, tone of voice, ключевые слова, формат площадки) и возвращают его Claude. Claude генерирует текст, используя этот контекст + ролевой промпт `content_writer.md`. Tool = данные, Claude = генерация.

---

## 8. Модуль SMM

### Tools

| Tool | Параметры | Описание | API |
|---|---|---|---|
| `telegram_post` | `channel`, `text`, `image?`, `schedule?` | Публикация/планирование в Telegram | Telegram Bot API |
| `telegram_stats` | `channel` | Статистика канала | Telegram Bot API |
| `vk_post` | `group`, `text`, `image?`, `schedule?` | Публикация в VK | VK API (`wall.post`) |
| `vk_stats` | `group`, `period?` | Статистика сообщества | VK API (`stats.get`) |
| `max_post` | `channel`, `text`, `image?`, `schedule?` | Публикация в MAX | MAX Bot API |
| `max_stats` | `channel` | Статистика канала MAX | MAX Bot API |
| `dzen_publish` | `text`, `image?` | Публикация в Дзен через Telegram-синхробот. Внутри вызывает `telegram_post` для канала, привязанного к Дзен (из project context `social.telegram_dzen_channel`). Заголовок = первое предложение поста (макс. 140 символов — требование Дзен) | Telegram Bot API → @zen_sync_bot |
| `trend_research` | `topic?`, `platform?` | Анализ трендов, популярные темы | Exa API (основной) + `pytrends-modern` (опционально, `pip install marketolog[trends]`) |
| `smm_calendar` | `period?` | Сводный календарь публикаций по всем площадкам | Агрегация данных |
| `best_time_to_post` | `platform?` | AI-рекомендация лучшего времени публикации. При наличии статистики — на основе данных аудитории (пиковая активность). Для новых проектов — отраслевые бенчмарки по нише из контекста проекта | Аналитика площадок + бенчмарки |

### Особенности

- **Адаптация контента** — один материал переформатируется: длинная статья для Дзен, структурированный пост для Telegram, визуальный для VK, адаптированный для MAX
- **Планирование** — `schedule` параметр: VK поддерживает нативно (`publish_date` в `wall.post`). Telegram и MAX не поддерживают scheduled messages через Bot API — для них используется файловая очередь (`~/.marketolog/scheduled/<timestamp>_<platform>.yaml`). При каждом запуске MCP-сервера проверяется очередь: посты с истёкшим временем отправляются сразу, будущие — остаются. Если пост просрочен более чем на 1 час, пользователь получает уведомление вместо автоматической отправки. Это проще, чем отдельный демон, и не зависит от постоянно работающего процесса
- **Безопасность публикации** — перед отправкой Claude показывает превью и ждёт подтверждения пользователя

### API-интеграции

**VK API:**
- Библиотека: `vk-api` v11.10+ (PyPI, Apache 2.0) или прямые HTTP-запросы
- Авторизация: токен сообщества с правами на публикацию
- Методы: `wall.post` (публикация), `wall.edit` (редактирование), `stats.get` (статистика)
- **Изменения с 27.08.2025:** `wall.post` теперь обязательно требует контент (текст/фото/видео/ссылка/статья), до 10 медиавложений, опрос не может быть единственным вложением, `newsfeed.getRecommended` и `newsfeed.getComments` отключены
- GIF: соотношение сторон от 0.66:1 до 2.5:1
- Сниппет ссылки: изображение мин. 500px ширина, для получения изображения — `wall.parseAttachedLink`

**Telegram Bot API (v9.3+):**
- Методы: `sendMessage`, `sendPhoto`, `sendDocument` (публикация), `getChatMemberCount` (подписчики), `getChatStatistics` (статистика канала, требует >500 подписчиков)
- Бот должен быть администратором канала с правом публикации
- Авторизация: Bot Token (через @BotFather)
- Python-библиотека: `aiogram` v3.22+ (async, самая популярная для Python)
- Для постинга в канал: `chat_id` = `@channel_username` или числовой ID

**MAX Bot API:**
- Документация: https://dev.max.ru/docs-api
- Base URL: `https://platform-api.max.ru`
- Авторизация: заголовок `Authorization: <access_token>` (токен из dev.max.ru → Чат-боты → Интеграция → Получить токен)
- Rate limit: 30 rps
- Ключевые методы:
  - `POST /messages` — отправка сообщения (параметры: `chat_id` или `user_id`, `text` до 4000 символов, `attachments`, `format`: markdown/html)
  - `GET /messages/{messageId}` — получение сообщения
  - `DELETE /messages` — удаление (до 24ч после отправки)
  - `PATCH /chats/{chatId}` — изменение информации о чате
  - `POST /answers` — ответ на callback (нажатие кнопки)
  - `PUT /chats/{chatId}/pin` — закрепление сообщения
- Поддерживает: Long Polling (для разработки), Webhook (для production, только HTTPS)
- Форматирование: Markdown (`**bold**`, `*italic*`, `~~strike~~`, `` `code` ``) и HTML
- Вложения: inline-клавиатура (до 210 кнопок), изображения, ссылки
- Python-библиотеки:
  - **Основная:** `max-messenger/max-botapi-python` (MIT, 47 stars) — официальный форк maxapi, поддерживается командой MAX. Установка: `pip install git+https://github.com/max-messenger/max-botapi-python.git`
  - Альтернатива на PyPI: `maxapi-python` v1.2.5 (MIT, ~900 загрузок/неделю). Установка: `pip install maxapi-python`
  - **Не использовать:** `PyMax` (162 stars) — это userbot API, не Bot API
- Каналы MAX: создание доступно только для юрлиц и ИП (резиденты РФ). Бот должен быть администратором канала для публикации

**Дзен (кросспостинг из Telegram):**
- У Дзен нет открытого API для автоматической публикации статей
- Рабочий механизм: официальный Telegram-синхробот (`@zen_sync_bot`)
- Настройка: пользователь добавляет синхробот в администраторы Telegram-канала, авторизует через Студию Дзен (Настройки → Кросспостинг → Telegram)
- После настройки все посты из Telegram автоматически дублируются в Дзен
- Поддерживает: текст, текст+изображения, текст+видео
- Не поддерживает: опросы, репосты, рекламные посты с ERID
- Tool `dzen_publish` фактически вызывает `telegram_post` для привязанного канала, а синхробот транслирует в Дзен
- Альтернатива: RSS-лента (требует домен) — может быть добавлена позже для пользователей с сайтом

---

## 9. Модуль Analytics

### Tools

| Tool | Параметры | Описание | API |
|---|---|---|---|
| `metrika_report` | `period?`, `metrics?` | Отчёт: визиты, источники, поведение, конверсии | Яндекс.Метрика API |
| `metrika_goals` | — | Список целей и конверсий | Яндекс.Метрика API |
| `search_console_report` | `period?` | Запросы, клики, позиции, CTR | Google Search Console API |
| `traffic_sources` | `period?` | Сводка по источникам: поиск, соцсети, прямые | Метрика + SC |
| `funnel_analysis` | `goal?` | Анализ воронки: откуда → что делают → где уходят | Яндекс.Метрика API |
| `weekly_digest` | — | Еженедельный дайджест: метрики, изменения, рекомендации | Все источники |
| `ai_referral_report` | `period?` | Трафик с AI-поисковиков: ChatGPT, Perplexity, Claude, Google AI Overviews | Яндекс.Метрика + Google SC (referrer analysis) |
| `generate_utm` | `url`, `source`, `medium`, `campaign?`, `term?`, `content?` | Генерация UTM-размеченных ссылок. Связывает SMM-публикации с аналитикой — без UTM `traffic_sources` не различит каналы | Локальная генерация |

### API Яндекс.Метрика — ключевые endpoints

Base URL: `https://api-metrika.yandex.net`

| Endpoint | Назначение |
|---|---|
| `GET /stat/v1/data` | Основной отчёт (dimensions + metrics + filters) |
| `GET /stat/v1/data/bytime` | Данные по времени (графики, тренды) |
| `GET /stat/v1/data/comparison` | Сравнение сегментов (день к дню, мобильные vs десктоп) |
| `GET /management/v1/counter/{id}/goals` | Список целей |

Ключевые dimensions:
- `ym:s:lastTrafficSource` — источник трафика
- `ym:s:searchEngine` — поисковая система
- `ym:s:regionCityName` — город

Ключевые metrics:
- `ym:s:visits` — визиты
- `ym:s:users` — посетители
- `ym:s:bounceRate` — отказы
- `ym:s:goalXconversionRate` — конверсия по цели X

### `weekly_digest` — ключевой инструмент

Собирает данные из всех модулей:

```
Недельный дайджест "My SaaS" (31 марта - 6 апреля)

Трафик: 1,245 визитов (+12% к прошлой неделе)
Источники: Яндекс 48%, прямые 22%, VK 15%, Telegram 10%, другие 5%
Позиции: "таск трекер" — 8 -> 6 в Яндекс (рост)
Конверсия: 2.3% -> 2.7% (цель: регистрация)
Контент: пост в Telegram от 02.04 — лучший охват (3,200)

Рекомендации:
1. Усилить VK — растущий канал, увеличить частоту постов
2. Страница /pricing медленная (LCP 4.2s) — теряем конверсии
3. Запрос "бесплатный таск трекер" — позиция 14, стоит написать статью
```

---

## 10. Модуль Strategy

### Tools

| Tool | Параметры | Описание |
|---|---|---|
| `analyze_target_audience` | — | Портреты ЦА (ICP): кто, боли, мотивация, каналы |
| `analyze_positioning` | — | Позиционирование: отличия от конкурентов, УТП, слабые стороны |
| `competitor_intelligence` | `competitor_urls?` | Глубокий анализ: продукт, цены, контент, соцсети, SEO, каналы |
| `marketing_plan` | `period?`, `budget?` | Маркетинговый план: цели, каналы, бюджет, метрики, календарь |
| `channel_recommendation` | — | Рекомендация каналов продвижения с прогнозом ROI |
| `brand_health` | — | Здоровье бренда: упоминания, отзывы, динамика |
| `ai_visibility` | `brand_name?` | Мониторинг упоминаний бренда в AI-ответах (ChatGPT, Claude, Perplexity). Источник: Exa + прямые запросы |

### Роль модуля

Strategy — "мозг" агента. Работает на уровне "зачем", а не "как":
- SEO-модуль: "позиция по запросу X = 14"
- Strategy-модуль: "этот сегмент стоит занять, потому что конкуренты его упускают, ЦА там ищет, стоимость привлечения ниже"

### Сценарий первого запуска

1. `create_project()` — создаёт проект, парсит сайт для базового контекста
2. Claude задаёт 3-5 уточняющих вопросов (бюджет, цели, сроки)
3. `analyze_target_audience()` — портреты ЦА
4. `competitor_intelligence()` — карта конкурентов
5. `analyze_positioning()` — УТП и позиционирование
6. `channel_recommendation()` — приоритетные каналы
7. `marketing_plan(period="3 months")` — план на квартал
8. Презентация стратегии, обсуждение, корректировка
9. Переход к реализации: SEO-аудит, контент-план

---

## 11. Система промптов

### Основной промпт (`strategist.md`)

Определяет общее поведение Claude-маркетолога:
- Опытный маркетолог для бизнеса в Рунете
- Всегда начинает с контекста проекта (вызывает `get_project_context()`)
- Предлагает план действий -> ждёт одобрения -> выполняет
- Приоритизирует: максимальный результат при минимальных затратах
- Говорит простым языком, без маркетингового жаргона
- Каждую рекомендацию подкрепляет данными из инструментов
- Адаптирует рекомендации под масштаб проекта

### Ролевые промпты

| Файл | Когда активируется | Суть |
|---|---|---|
| `seo_expert.md` | SEO-задачи | Приоритет — органический трафик, техническое здоровье, семантика |
| `content_writer.md` | Генерация контента | Tone of voice проекта, SEO-оптимизация, адаптация под площадку |
| `smm_manager.md` | Работа с соцсетями | Специфика площадок, тренды, вовлечённость, время публикации |
| `analyst.md` | Аналитика | Инсайты в данных, аномалии, перевод цифр в действия |

### Механизм загрузки

Промпты загружаются как MCP resources. Claude подгружает нужный ролевой промпт в зависимости от задачи:
- "Проведи SEO-аудит" -> `strategist.md` + `seo_expert.md`
- "Напиши пост для Telegram" -> `strategist.md` + `content_writer.md` + `smm_manager.md`
- "Как дела с трафиком?" -> `strategist.md` + `analyst.md`

---

## 12. Монетизация: Open-core

### Модель

Два PyPI-пакета:

```
marketolog        (открытый, бесплатный)
marketolog-pro    (приватный, платный)
```

### Разделение функционала

**`marketolog` (бесплатно):**
- Core: управление проектами (включая `delete_project`), контекст
- SEO: `seo_audit`, `ai_seo_check`, базовый `keyword_research`
- Analytics: `generate_utm` (базовая утилита, связывает каналы с аналитикой)
- PageSpeed аудит
- Все промпты

**`marketolog-pro` (платно):**
- Content: полный модуль (plan, generation, optimization, `repurpose_content`)
- SMM: публикация, статистика по всем площадкам, `best_time_to_post`
- Analytics: Метрика, Search Console, дайджест, `ai_referral_report`
- Strategy: полный модуль, `ai_visibility`
- SEO расширенный: `keyword_cluster`, `content_gap`, `check_positions`
- Exa-интеграция

### Техническая реализация

`marketolog-pro` — дополнительный пакет, который регистрирует свои tools в том же MCP-сервере:

```python
# marketolog-pro/src/marketolog_pro/__init__.py
from marketolog.server import mcp

# Регистрирует дополнительные tools
from .modules.content import planner, generator, optimizer
from .modules.smm import telegram, vk, max, dzen
from .modules.analytics import metrika, search_console, digest
from .modules.strategy import audience, positioning, planning
```

Если `marketolog-pro` установлен — tools доступны. Если нет — их нет в списке инструментов Claude. Никаких проверок лицензий, никаких сообщений "купи Pro".

### Каналы продажи

- GitHub Sponsors (tier с доступом к приватному репозиторию)
- Gumroad / собственный сайт -> invite в приватный репо или токен для приватного PyPI

---

## 13. Подключение к Claude

### Claude Desktop

```json
{
  "mcpServers": {
    "marketolog": {
      "command": "python",
      "args": ["-m", "marketolog"],
      "env": {
        "YANDEX_OAUTH_TOKEN": "...",
        "YANDEX_WORDSTAT_TOKEN": "...",
        "YANDEX_SEARCH_API_KEY": "...",
        "YANDEX_FOLDER_ID": "...",
        "VK_API_TOKEN": "...",
        "TELEGRAM_BOT_TOKEN": "...",
        "MAX_BOT_TOKEN": "...",
        "GOOGLE_SC_CREDENTIALS": "/path/to/service-account.json",
        "EXA_API_KEY": "...",
        "PAGESPEED_API_KEY": "..."
      }
    }
  }
}
```

### Claude Code

```bash
claude mcp add marketolog -- python -m marketolog
```

### Переменные окружения

| Переменная | Обязательная | Назначение |
|---|---|---|
| `YANDEX_OAUTH_TOKEN` | Нет | Яндекс.Метрика + Вебмастер (единый OAuth-токен) |
| `YANDEX_WORDSTAT_TOKEN` | Нет | Яндекс.Wordstat API (отдельный OAuth-токен, требует заявку) |
| `YANDEX_SEARCH_API_KEY` | Нет | API-ключ Yandex Cloud для Яндекс.Поиск API v2 |
| `YANDEX_FOLDER_ID` | Нет | Folder ID в Yandex Cloud (для Яндекс.Поиск API) |
| `YANDEX_METRIKA_COUNTER` | Нет | ID счётчика Метрики |
| `VK_API_TOKEN` | Нет | Токен сообщества VK |
| `TELEGRAM_BOT_TOKEN` | Нет | Токен Telegram-бота |
| `MAX_BOT_TOKEN` | Нет | Токен MAX-бота |
| `GOOGLE_SC_CREDENTIALS` | Нет | Путь к service account JSON для Google SC |
| `EXA_API_KEY` | Нет | Ключ Exa API (опционально) |
| `PAGESPEED_API_KEY` | Нет | Ключ PageSpeed (опционально, увеличивает квоту) |

Ни одна переменная не обязательна. Пользователь подключает сервисы постепенно.

### Встроенный OAuth-флоу

Для упрощения онбординга Marketolog поддерживает интерактивную авторизацию через CLI:

```bash
python -m marketolog auth yandex      # OAuth для Метрики + Вебмастера
python -m marketolog auth wordstat    # OAuth для Wordstat (отдельное приложение)
python -m marketolog auth vk          # Токен сообщества VK
python -m marketolog auth telegram    # Проверка токена Telegram-бота
python -m marketolog auth max         # Проверка токена MAX-бота
python -m marketolog auth status      # Статус всех подключений
```

Команда `auth yandex` открывает браузер → `oauth.yandex.ru/authorize?...` → пользователь подтверждает → токен сохраняется в `~/.marketolog/config.yaml`. Это опциональная альтернатива ручной настройке env-переменных.

---

## 14. Кэширование

Файловый TTL-кэш в `~/.marketolog/cache/`:

| Тип данных | TTL | Пример |
|---|---|---|
| Keyword research | 24 часа | Частотность запросов не меняется за день |
| SEO-аудит | 1 час | Технические проблемы могут быть исправлены |
| Позиции в выдаче | 6 часов | Позиции меняются не мгновенно |
| Аналитика (Метрика) | 1 час | Данные обновляются с задержкой |
| Статистика соцсетей | 30 минут | Охваты и вовлечённость меняются быстро |

Кэш предотвращает лишние запросы к API и ускоряет повторные вызовы.

### Структура локального хранилища

```
~/.marketolog/
├── config.yaml              # API-токены (альтернатива env-переменным, заполняется через `auth`)
├── projects/
│   ├── my-saas.yaml         # контекст проекта
│   └── blog.yaml
├── cache/
│   ├── wordstat/            # кэш Wordstat API
│   ├── positions/           # кэш позиций
│   └── metrika/             # кэш аналитики
└── scheduled/
    ├── 1712500800_telegram_mysaas.yaml   # отложенный пост
    └── 1712504400_max_mysaas.yaml
```

---

## 15. Полный список MCP Tools (сводка)

### Core (6 tools)
- `create_project`, `switch_project`, `list_projects`, `update_project`, `delete_project`, `get_project_context`

### SEO (8 tools)
- `seo_audit`, `ai_seo_check`, `keyword_research`, `keyword_cluster`, `check_positions`, `analyze_competitors`, `content_gap`, `webmaster_report`

### Content (7 tools)
- `content_plan`, `generate_article`, `generate_post`, `optimize_text`, `analyze_content`, `generate_meta`, `repurpose_content`

### SMM (10 tools)
- `telegram_post`, `telegram_stats`, `vk_post`, `vk_stats`, `max_post`, `max_stats`, `dzen_publish`, `trend_research`, `smm_calendar`, `best_time_to_post`

### Analytics (8 tools)
- `metrika_report`, `metrika_goals`, `search_console_report`, `traffic_sources`, `funnel_analysis`, `weekly_digest`, `ai_referral_report`, `generate_utm`

### Strategy (7 tools)
- `analyze_target_audience`, `analyze_positioning`, `competitor_intelligence`, `marketing_plan`, `channel_recommendation`, `brand_health`, `ai_visibility`

**Итого: 46 tools**

### ToolAnnotations (MCP 2025-03-26)

Каждый tool аннотируется для безопасного автоматического одобрения:

| Категория | Аннотация | Tools |
|---|---|---|
| **Только чтение** | `readOnlyHint=True` | `list_projects`, `get_project_context`, `seo_audit`, `ai_seo_check`, `keyword_research`, `keyword_cluster`, `check_positions`, `analyze_competitors`, `content_gap`, `webmaster_report`, `analyze_content`, `telegram_stats`, `vk_stats`, `max_stats`, `trend_research`, `smm_calendar`, `best_time_to_post`, `metrika_report`, `metrika_goals`, `search_console_report`, `traffic_sources`, `funnel_analysis`, `weekly_digest`, `ai_referral_report`, `analyze_target_audience`, `analyze_positioning`, `competitor_intelligence`, `channel_recommendation`, `brand_health`, `ai_visibility`, `generate_utm` |
| **Мутирующие** | `readOnlyHint=False` | `create_project`, `switch_project`, `update_project`, `content_plan`, `generate_article`, `generate_post`, `optimize_text`, `generate_meta`, `repurpose_content`, `marketing_plan` |
| **Деструктивные** | `destructiveHint=True` | `delete_project`, `telegram_post`, `vk_post`, `max_post`, `dzen_publish` (необратимые публикации/удаления — Claude запрашивает подтверждение) |

---

## 16. Порядок реализации (рекомендуемый)

### Фаза 1: Фундамент
- Core модуль (проекты, контекст, конфигурация, включая `delete_project`)
- MCP-сервер (FastMCP, регистрация tools, ToolAnnotations)
- Утилиты (`format_tabular()`, `fetch_with_retry()`, кэш, auth)
- Встроенный OAuth-флоу (`python -m marketolog auth ...`)
- Промпты (strategist.md)
- Подключение к Claude

### Фаза 2: SEO
- **Free:** `seo_audit` (PageSpeed + парсинг), `ai_seo_check` (проверка AI-краулеров, llms.txt), `keyword_research` (Wordstat API), `webmaster_report` (Яндекс.Вебмастер API)
- **Pro:** `keyword_cluster`, `check_positions` (Яндекс.Поиск API v2), `analyze_competitors` (парсинг + Exa), `content_gap`

### Фаза 3: Analytics
- `metrika_report` (Яндекс.Метрика API)
- `search_console_report` (Google SC API)
- `traffic_sources`, `funnel_analysis`
- `weekly_digest`
- `ai_referral_report` (трафик с AI-поисковиков)
- `generate_utm` (UTM-разметка ссылок)

### Фаза 4: Content
- `content_plan`
- `generate_article`, `generate_post`
- `optimize_text`, `analyze_content`, `generate_meta`
- `repurpose_content` (репёрпосинг)

### Фаза 5: SMM
- `telegram_post`, `telegram_stats`
- `vk_post`, `vk_stats`
- `max_post`, `max_stats`
- `dzen_publish`
- `trend_research`, `smm_calendar`, `best_time_to_post`

### Фаза 6: Strategy
- `analyze_target_audience`, `analyze_positioning`
- `competitor_intelligence`, `channel_recommendation`
- `marketing_plan`
- `brand_health`, `ai_visibility`

### Фаза 7: Pro-пакет и монетизация
- Разделение на `marketolog` / `marketolog-pro`
- Документация, README, сайт
- Публикация на PyPI и в MCP-каталогах
