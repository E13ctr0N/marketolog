"""CLI entry point: python -m marketolog

Usage:
    python -m marketolog              — start MCP server
    python -m marketolog auth status  — show credentials status
    python -m marketolog auth yandex  — start OAuth flow for Yandex
"""

import sys


def run_auth(args: list[str]) -> None:
    """Handle `python -m marketolog auth <subcommand>`."""
    from marketolog.utils.auth import get_auth_status, get_oauth_url, save_token

    if not args:
        print("Использование: python -m marketolog auth <status|yandex|wordstat|vk|telegram|max>")
        sys.exit(1)

    subcommand = args[0]

    if subcommand == "status":
        status = get_auth_status()
        print("Статус подключений:\n")
        labels = {
            "yandex_oauth_token": "Яндекс (Метрика + Вебмастер)",
            "yandex_wordstat_token": "Яндекс Wordstat API",
            "yandex_search_api_key": "Яндекс Поиск API",
            "yandex_folder_id": "Yandex Cloud Folder ID",
            "yandex_metrika_counter": "Яндекс Метрика (счётчик)",
            "vk_api_token": "VK API",
            "telegram_bot_token": "Telegram Bot",
            "max_bot_token": "MAX Bot",
            "google_sc_credentials": "Google Search Console",
            "exa_api_key": "Exa API",
            "pagespeed_api_key": "PageSpeed API",
        }
        for field, label in labels.items():
            state = status.get(field, "не настроен")
            icon = "+" if state != "не настроен" else "-"
            print(f"  [{icon}] {label}: {state}")

    elif subcommand in ("yandex", "wordstat"):
        client_id = input("Введите Client ID приложения Яндекс OAuth: ").strip()
        if not client_id:
            print("Client ID не может быть пустым.")
            sys.exit(1)
        url = get_oauth_url(subcommand, client_id=client_id)
        print(f"\nОткройте в браузере:\n{url}\n")
        token = input("Вставьте полученный токен: ").strip()
        if not token:
            print("Токен не может быть пустым.")
            sys.exit(1)
        field = "yandex_oauth_token" if subcommand == "yandex" else "yandex_wordstat_token"
        save_token(field, token)
        print(f"Токен сохранён в ~/.marketolog/config.yaml ({field})")

    elif subcommand in ("vk", "telegram", "max"):
        field_map = {
            "vk": "vk_api_token",
            "telegram": "telegram_bot_token",
            "max": "max_bot_token",
        }
        token = input(f"Введите токен для {subcommand.upper()}: ").strip()
        if not token:
            print("Токен не может быть пустым.")
            sys.exit(1)
        save_token(field_map[subcommand], token)
        print(f"Токен сохранён в ~/.marketolog/config.yaml")

    else:
        print(f"Неизвестная команда: {subcommand}")
        print("Доступные: status, yandex, wordstat, vk, telegram, max")
        sys.exit(1)


def main() -> None:
    args = sys.argv[1:]

    if args and args[0] == "auth":
        run_auth(args[1:])
        return

    # Default: start MCP server
    from marketolog.server import create_server
    server = create_server()
    server.run()


if __name__ == "__main__":
    main()
