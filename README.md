# Marketolog

AI-маркетолог для бизнеса в Рунете — MCP-сервер для Claude.

Подключается к Claude Desktop, Claude Code или claude.ai. Агент анализирует ваш проект, предлагает стратегию продвижения и выполняет задачи (SEO-аудит, контент-план, публикации в соцсети) после одобрения.

## Возможности

**Бесплатно (marketolog):**
- Управление проектами — создание, контекст, настройки
- SEO-аудит — Core Web Vitals, мета-теги, robots.txt, sitemap
- Проверка AI-готовности — GPTBot, ClaudeBot, llms.txt
- Подбор ключевых слов — Яндекс Wordstat API
- UTM-разметка ссылок
- Все промпты (маркетолог-стратег, SEO, аналитик, контент, SMM)

**Pro (marketolog-pro) — 36 инструментов:**
- SEO расширенный — кластеризация, позиции, конкуренты, content gap, Вебмастер
- Аналитика — Яндекс.Метрика, Google Search Console, воронки, AI-трафик, дайджест
- Контент — план, генерация статей и постов, оптимизация, мета-теги, репёрпосинг
- SMM — публикация в Telegram, VK, MAX, Дзен + статистика, тренды, календарь
- Стратегия — ЦА, позиционирование, конкурентная разведка, маркетинг-план, AI-видимость

Для получения Pro-версии напишите в Telegram: **[@E13ctr](https://t.me/E13ctr)**

## Быстрый старт

### Установка

```bash
pip install marketolog
```

### Подключение к Claude Desktop

Добавьте в `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "marketolog": {
      "command": "python",
      "args": ["-m", "marketolog"]
    }
  }
}
```

### Подключение к Claude Code

```bash
claude mcp add marketolog -- python -m marketolog
```

### Первый запуск

Скажите Claude:

> Создай проект my-saas с URL https://my-saas.ru в нише «управление проектами»

Claude создаст проект и предложит план действий.

## Настройка API-ключей

Ни один ключ не обязателен — подключайте сервисы по мере необходимости.

### Через CLI (рекомендуется)

```bash
python -m marketolog auth yandex      # OAuth для Метрики + Вебмастера
python -m marketolog auth wordstat    # OAuth для Wordstat
python -m marketolog auth vk          # Токен VK
python -m marketolog auth telegram    # Токен Telegram-бота
python -m marketolog auth max         # Токен MAX-бота
python -m marketolog auth status      # Статус подключений
```

### Через переменные окружения

| Переменная | Назначение |
|---|---|
| `YANDEX_OAUTH_TOKEN` | Яндекс.Метрика + Вебмастер |
| `YANDEX_WORDSTAT_TOKEN` | Яндекс Wordstat API |
| `YANDEX_SEARCH_API_KEY` | Яндекс Поиск API v2 |
| `YANDEX_FOLDER_ID` | Yandex Cloud Folder ID |
| `YANDEX_METRIKA_COUNTER` | ID счётчика Метрики |
| `VK_API_TOKEN` | Токен сообщества VK |
| `TELEGRAM_BOT_TOKEN` | Токен Telegram-бота |
| `MAX_BOT_TOKEN` | Токен MAX-бота |
| `GOOGLE_SC_CREDENTIALS` | Путь к service account JSON |
| `EXA_API_KEY` | Exa API (для трендов и AI-видимости) |
| `PAGESPEED_API_KEY` | PageSpeed (увеличивает квоту) |

## Инструменты

### Core (6)

| Инструмент | Описание |
|---|---|
| `create_project` | Создать проект |
| `switch_project` | Переключить активный проект |
| `list_projects` | Список проектов |
| `update_project` | Обновить поле проекта |
| `delete_project` | Удалить проект |
| `get_project_context` | Полный контекст проекта |

### SEO (8)

| Инструмент | Пакет | Описание |
|---|---|---|
| `seo_audit` | free | Технический SEO-аудит |
| `ai_seo_check` | free | Готовность к AI-поисковикам |
| `keyword_research` | free | Подбор ключевых слов |
| `keyword_cluster` | pro | Кластеризация по интенту |
| `check_positions` | pro | Позиции в Яндексе |
| `analyze_competitors` | pro | Анализ конкурентов |
| `content_gap` | pro | Контентные пробелы |
| `webmaster_report` | pro | Яндекс.Вебмастер |

### Analytics (8)

| Инструмент | Пакет | Описание |
|---|---|---|
| `generate_utm_link` | free | UTM-разметка |
| `metrika_report` | pro | Яндекс.Метрика |
| `metrika_goals` | pro | Цели Метрики |
| `search_console_report` | pro | Google Search Console |
| `traffic_sources` | pro | Источники трафика |
| `funnel_analysis` | pro | Воронка конверсии |
| `weekly_digest` | pro | Еженедельный дайджест |
| `ai_referral_report` | pro | AI-трафик |

### Content (7) — pro

| Инструмент | Описание |
|---|---|
| `content_plan` | Контент-план |
| `generate_article` | SEO-статья |
| `generate_post` | Пост для площадки |
| `optimize_text` | SEO-оптимизация текста |
| `analyze_content` | Анализ контента страницы |
| `generate_meta` | Title, description, H1 |
| `repurpose_content` | Адаптация под форматы |

### SMM (10) — pro

| Инструмент | Описание |
|---|---|
| `telegram_post` | Пост в Telegram |
| `telegram_stats` | Статистика Telegram |
| `vk_post` | Пост в VK |
| `vk_stats` | Статистика VK |
| `max_post` | Пост в MAX |
| `max_stats` | Статистика MAX |
| `dzen_publish` | Публикация в Дзен |
| `trend_research` | Тренды в нише |
| `smm_calendar` | Календарь публикаций |
| `best_time_to_post` | Лучшее время |

### Strategy (7) — pro

| Инструмент | Описание |
|---|---|
| `analyze_target_audience` | Портреты ЦА |
| `analyze_positioning` | УТП и позиционирование |
| `competitor_intelligence` | Конкурентная разведка |
| `marketing_plan` | Маркетинговый план |
| `channel_recommendation` | Рекомендация каналов |
| `brand_health` | Здоровье бренда |
| `ai_visibility` | AI-видимость |

## Хранилище данных

```
~/.marketolog/
├── config.yaml          # API-токены
├── projects/            # YAML-файлы проектов
├── cache/               # Кэш API-ответов
└── scheduled/           # Отложенные посты
```

## Pro-версия

Пакет `marketolog-pro` добавляет 36 инструментов поверх бесплатной базы: расширенный SEO-анализ, аналитику Яндекс.Метрики и Google Search Console, генерацию контента, публикацию в соцсети, стратегическое планирование и мониторинг AI-видимости.

**Как получить:**
1. Напишите в Telegram: [@E13ctr](https://t.me/E13ctr)
2. Получите доступ к приватному репозиторию
3. Установите:

```bash
pip install marketolog                    # базовый пакет (PyPI)
git clone https://github.com/E13ctr0N/marketolog-pro.git
pip install marketolog-pro/releases/v0.1.0/marketolog_pro-0.1.0-py3-none-any.whl
```

После установки Pro-инструменты автоматически появятся в Claude.

## Лицензия

MIT — бесплатный пакет `marketolog`

Proprietary — пакет `marketolog-pro`
