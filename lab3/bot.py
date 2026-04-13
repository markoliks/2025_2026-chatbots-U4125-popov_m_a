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
            f"Имя: {row['name']}\n"
            f"Отдел: {row['department']}\n"
            f"Должность: {row['role']}\n"
            f"Email: {row['email']}"
        )

    return "\n\n".join(lines)


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
        "Привет! Я учебный Telegram-бот команды.\n"
        "Я могу показать информацию о команде, контактах, событиях и сотрудниках.\n"
        "Напиши /help, чтобы увидеть список команд.",
        reply_markup=get_main_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /help: список всех доступных команд."""
    await update.message.reply_text(
        "Доступные команды:\n"
        "/start - приветствие и описание\n"
        "/help - список команд\n"
        "/about - информация о команде\n"
        "/contacts - контакты команды\n"
        "/team - состав команды\n"
        "/events - расписание событий\n"
        "/employees - показать всех сотрудников\n"
        "/departments - показать список отделов\n"
        "/department <название_отдела> - показать сотрудников отдела\n"
        "/find <имя> - найти сотрудника по имени"
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
            await update.message.reply_text("Список сотрудников пуст.")
            return

        await update.message.reply_text("Сотрудники:\n" + format_employees(employees))
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

        await update.message.reply_text("Отделы:\n" + "\n".join(departments))
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
                f"Сотрудники отдела '{department_name}' не найдены."
            )
            return

        await update.message.reply_text(
            f"Сотрудники отдела '{department_name}':\n"
            f"{format_employees(filtered_employees)}"
        )
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
                f"Сотрудники по запросу '{search_name}' не найдены."
            )
            return

        await update.message.reply_text(
            f"Результаты поиска по '{search_name}':\n"
            f"{format_employees(filtered_employees)}"
        )
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

    # Глобальная обработка ошибок.
    application.add_error_handler(error_handler)

    logger.info("Бот запущен и ожидает команды...")
    application.run_polling()


if __name__ == "__main__":
    main()
