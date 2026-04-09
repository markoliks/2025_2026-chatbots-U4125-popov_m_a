import logging
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


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


def load_employees() -> pd.DataFrame:
    """
    Читает таблицу сотрудников из CSV.
    Проверяет наличие обязательных колонок и возвращает DataFrame.
    """
    try:
        employees_df = pd.read_csv(EMPLOYEES_CSV_PATH)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Файл не найден: {EMPLOYEES_CSV_PATH}") from exc
    except Exception as exc:  # pylint: disable=broad-except
        raise RuntimeError("Не удалось прочитать employees.csv") from exc

    required_columns = {"name", "department", "role", "email"}
    actual_columns = set(employees_df.columns)
    missing_columns = required_columns - actual_columns

    if missing_columns:
        missing_list = ", ".join(sorted(missing_columns))
        raise ValueError(f"В employees.csv нет обязательных колонок: {missing_list}")

    return employees_df


def format_employees(employees_df: pd.DataFrame) -> str:
    """Форматирует список сотрудников в читаемый текст."""
    lines = []
    for _, row in employees_df.iterrows():
        lines.append(
            f"{row['name']} | Отдел: {row['department']} | "
            f"Должность: {row['role']} | Email: {row['email']}"
        )

    return "\n".join(lines)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start: приветствие и краткое описание."""
    await update.message.reply_text(
        "Привет! Я учебный Telegram-бот команды.\n"
        "Я могу показать информацию о команде, контактах, событиях и сотрудниках.\n"
        "Напиши /help, чтобы увидеть список команд."
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
        employees_df = load_employees()
        if employees_df.empty:
            await update.message.reply_text("Список сотрудников пуст.")
            return

        await update.message.reply_text("Сотрудники:\n" + format_employees(employees_df))
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Ошибка в /employees", exc_info=exc)
        await update.message.reply_text("Не удалось получить список сотрудников.")


async def department_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /department <название_отдела>: фильтр по отделу."""
    if not context.args:
        await update.message.reply_text("Использование: /department <название_отдела>")
        return

    department_name = " ".join(context.args).strip()

    try:
        employees_df = load_employees()
        filtered_df = employees_df[
            employees_df["department"].astype(str).str.lower() == department_name.lower()
        ]

        if filtered_df.empty:
            await update.message.reply_text(
                f"Сотрудники отдела '{department_name}' не найдены."
            )
            return

        await update.message.reply_text(
            f"Сотрудники отдела '{department_name}':\n{format_employees(filtered_df)}"
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
        employees_df = load_employees()
        filtered_df = employees_df[
            employees_df["name"].astype(str).str.contains(search_name, case=False, na=False)
        ]

        if filtered_df.empty:
            await update.message.reply_text(
                f"Сотрудники по запросу '{search_name}' не найдены."
            )
            return

        await update.message.reply_text(
            f"Результаты поиска по '{search_name}':\n{format_employees(filtered_df)}"
        )
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Ошибка в /find", exc_info=exc)
        await update.message.reply_text("Не удалось выполнить поиск сотрудника.")


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
    application.add_handler(CommandHandler("department", department_command))
    application.add_handler(CommandHandler("find", find_command))

    # Глобальная обработка ошибок.
    application.add_error_handler(error_handler)

    logger.info("Бот запущен и ожидает команды...")
    application.run_polling()


if __name__ == "__main__":
    main()
