import logging
import os
from pathlib import Path
import csv
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters


# Базовая настройка логов для диагностики ошибок.
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Пути к файлам рядом со скриптом.
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
EMPLOYEES_CSV_PATH = BASE_DIR / "employees.csv"


def load_employees():
    """
    Читает список сотрудников из CSV.
    Проверяет наличие обязательных колонок.
    """
    employees = []

    try:
        with open(EMPLOYEES_CSV_PATH, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []

            required_columns = {"name", "department", "role", "email"}
            actual_columns = set(fieldnames)
            missing_columns = required_columns - actual_columns

            if missing_columns:
                missing_list = ", ".join(sorted(missing_columns))
                raise ValueError(
                    f"В employees.csv отсутствуют обязательные колонки: {missing_list}"
                )

            for row in reader:
                employees.append(row)

    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Файл не найден: {EMPLOYEES_CSV_PATH}"
        ) from exc
    except Exception as exc:
        raise RuntimeError(
            "Не удалось прочитать employees.csv"
        ) from exc

    return employees


def format_employees(employees):
    """Форматирует список сотрудников в читаемый текст."""
    lines = []

    for row in employees:
        lines.append(
            f"👤 {row['name']}\n"
            f"🏢 {row['department']}\n"
            f"💼 {row['role']}\n"
            f"✉️ {row['email']}"
        )

    return "\n\n".join(lines)


def split_text(text: str, max_length: int = 4000) -> list[str]:
    """Делит длинный текст на части, чтобы не превышать лимит Telegram."""
    if len(text) <= max_length:
        return [text]

    parts = []
    current_part = []
    current_length = 0

    for line in text.split("\n"):
        line_length = len(line) + 1
        if current_length + line_length > max_length and current_part:
            parts.append("\n".join(current_part))
            current_part = [line]
            current_length = line_length
        else:
            current_part.append(line)
            current_length += line_length

    if current_part:
        parts.append("\n".join(current_part))

    return parts


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Возвращает главное кнопочное меню."""
    keyboard = [
        ["Все сотрудники", "Отделы"],
        ["Контакты", "Помощь"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start: приветствие и краткое описание."""
    await update.message.reply_text(
        "Привет! Я бот-помощник по сотрудникам команды 👋\n"
        "Вот что я умею:\n"
        "• показать всех сотрудников\n"
        "• показать список отделов\n"
        "• найти сотрудника по имени\n\n"
        "Используйте команды или кнопки ниже ⬇️",
        reply_markup=get_main_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /help: список всех доступных команд."""
    await update.message.reply_text(
        "Вот доступные команды:\n\n"
        "ℹ️ Основное:\n"
        "/start - приветствие и кнопки\n"
        "/help - список команд\n\n"
        "👥 Команда:\n"
        "/about - информация о команде\n"
        "/contacts - контакты команды\n"
        "/team - состав команды\n"
        "/events - расписание событий\n\n"
        "📁 Сотрудники:\n"
        "/employees - показать всех сотрудников\n"
        "/departments - список отделов\n"
        "/department <название_отдела> - сотрудники отдела\n"
        "/find <имя> - поиск сотрудника по имени"
    )


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /about: описание команды."""
    await update.message.reply_text("Мы учебная команда, занимаемся разработкой проектов")


async def contacts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /contacts: контакты команды."""
    await update.message.reply_text(
        "Руководитель: Иван Иванов - @ivanov\n"
        "Менеджер: Анна Смирнова - @annasmirnova\n"
        "Почта: team@example.com"
    )


async def team_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /team: список участников команды."""
    await update.message.reply_text(
        "Иван Иванов - руководитель\n"
        "Анна Смирнова - менеджер\n"
        "Петр Петров - разработчик\n"
        "Мария Соколова - дизайнер"
    )


async def events_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /events: основные события."""
    await update.message.reply_text(
        "Планерка - понедельник 10:00\n"
        "Дедлайн - пятница 18:00\n"
        "Демонстрация проекта - среда 15:00"
    )


async def employees_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /employees: выводит всех сотрудников."""
    try:
        employees = load_employees()
        if not employees:
            await update.message.reply_text(
                "Пока список сотрудников пуст.\n"
                "Проверьте, что в employees.csv есть данные."
            )
            return

        text = "Сотрудники:\n\n" + format_employees(employees)
        for part in split_text(text):
            await update.message.reply_text(part)
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Ошибка в /employees", exc_info=exc)
        await update.message.reply_text("Не удалось получить список сотрудников.")


async def departments_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /departments: выводит отсортированный список отделов."""
    try:
        employees = load_employees()
        departments = sorted(
            {
                row.get("department", "").strip()
                for row in employees
                if row.get("department", "").strip()
            }
        )

        if not departments:
            await update.message.reply_text("Список отделов пуст.")
            return

        text = "Отделы:\n" + "\n".join(departments)
        for part in split_text(text):
            await update.message.reply_text(part)
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Ошибка в /departments", exc_info=exc)
        await update.message.reply_text("Не удалось получить список отделов.")


async def department_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /department <название_отдела>: фильтр по отделу."""
    if not context.args:
        await update.message.reply_text("Использование: /department <название_отдела>")
        return

    department_name = " ".join(context.args).strip()

    try:
        employees = load_employees()
        filtered_employees = [
            row
            for row in employees
            if row.get("department", "").strip().lower() == department_name.lower()
        ]

        if not filtered_employees:
            await update.message.reply_text(
                f"Не удалось найти сотрудников в отделе '{department_name}'.\n"
                "Подсказка: используйте /departments или кнопку \"Отделы\"."
            )
            return

        text = (
            f"Сотрудники отдела '{department_name}':\n"
            f"{format_employees(filtered_employees)}"
        )
        for part in split_text(text):
            await update.message.reply_text(part)
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Ошибка в /department", exc_info=exc)
        await update.message.reply_text("Не удалось выполнить поиск по отделу.")


async def find_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /find <имя>: поиск сотрудника по части имени."""
    if not context.args:
        await update.message.reply_text("Использование: /find <имя>")
        return

    search_name = " ".join(context.args).strip()

    try:
        employees = load_employees()
        search_name_lower = search_name.lower()
        filtered_employees = [
            row
            for row in employees
            if search_name_lower in row.get("name", "").strip().lower()
        ]

        if not filtered_employees:
            await update.message.reply_text(
                f"По запросу '{search_name}' никого не нашли.\n"
                "Подсказка: попробуйте, например, /find Иван"
            )
            return

        text = (
            f"Результаты поиска по '{search_name}':\n"
            f"{format_employees(filtered_employees)}"
        )
        for part in split_text(text):
            await update.message.reply_text(part)
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Ошибка в /find", exc_info=exc)
        await update.message.reply_text("Не удалось выполнить поиск сотрудника.")


async def text_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает нажатия на кнопки главного меню."""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    if text == "Все сотрудники":
        await employees_command(update, context)
    elif text == "Отделы":
        await departments_command(update, context)
    elif text == "Контакты":
        await contacts_command(update, context)
    elif text == "Помощь":
        await help_command(update, context)


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает неизвестные команды."""
    await update.message.reply_text(
        "Я не знаю такую команду 😅\n"
        "Используйте /help или кнопки ниже."
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Глобальный обработчик ошибок для непойманных исключений."""
    logger.exception("Необработанная ошибка в боте", exc_info=context.error)

    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("Произошла ошибка. Попробуйте позже.")


def main() -> None:
    """Точка входа: загрузка токена, регистрация команд и запуск бота."""
    load_dotenv(dotenv_path=ENV_PATH)

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("Не найден TELEGRAM_BOT_TOKEN в файле .env")

    application = Application.builder().token(token).build()

    # Старые команды.
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("contacts", contacts_command))
    application.add_handler(CommandHandler("team", team_command))
    application.add_handler(CommandHandler("events", events_command))

    # Новые команды для работы с CSV.
    application.add_handler(CommandHandler("employees", employees_command))
    application.add_handler(CommandHandler("departments", departments_command))
    application.add_handler(CommandHandler("department", department_command))
    application.add_handler(CommandHandler("find", find_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, text_menu_handler)
    )
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    # Глобальная обработка ошибок.
    application.add_error_handler(error_handler)

    logger.info("Бот запущен и ожидает команды...")
    application.run_polling()


if __name__ == "__main__":
    main()
