University: [ITMO University](https://itmo.ru)  
Faculty: [FICT](https://fict.itmo.ru)  
Course: Vibe Coding: AI-боты для бизнеса  
Year: 2025/2026  
Group: U4125  
Author: Popov Mark  
Lab: Lab1  
Date of create: 09.04.2026  
Date of finished: -
# Лабораторная работа №1

# 📌 Описание работы

В данной лабораторной работе был разработан Telegram-бот с использованием Python и библиотеки python-telegram-bot.

Бот реализует обработку команд пользователя и отправку ответов.


# ⚙️ Используемые технологии

- Python  
- python-telegram-bot  
- python-dotenv  
- Telegram Bot API  


# 🏗 Структура проекта

lab1/
├── bot.py
├── requirements.txt
├── .env
├── .env.example
└── lab1_report.md


# 🚀 Функционал бота

Реализованы команды:

- /start — приветствие  
- /help — помощь  
- /about — информация  
- /contacts — контакты  
- /team — команда  
- /events — события  


# 🔐 Работа с .env

Токен хранится в файле `.env`, что обеспечивает безопасность проекта.


# ▶️ Запуск

cd lab1
pip install -r requirements.txt
python bot.py


# ✅ Результат

Бот успешно запущен и корректно обрабатывает команды пользователя.


# 💡 Вывод

В ходе работы были изучены основы создания Telegram-ботов, работа с API и управление зависимостями проекта.
