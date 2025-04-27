import os
import requests
import telebot
from datetime import datetime
from threading import Thread
from time import sleep
from dotenv import load_dotenv  # Добавлен импорт

# Загрузка переменных окружения
load_dotenv()  # Добавлена эта строка

# Инициализация БД
from database import init_db, save_user, get_all_users, delete_user, get_user
init_db()

# Проверка токенов
TOKEN = os.getenv('TG_TOKEN')
WEATHER_KEY = os.getenv('WEATHER_KEY')

if not TOKEN or not WEATHER_KEY:
    raise ValueError("Не найдены токены в .env файле!")

bot = telebot.TeleBot(TOKEN)

# Состояния пользователей
user_states = {}


def get_weather(city):
    """Получение погоды с OpenWeatherMap"""
    url = 'http://api.openweathermap.org/data/2.5/weather'
    params = {
        'q': city,
        'appid': WEATHER_KEY,
        'units': 'metric',
        'lang': 'ru'
    }
    response = requests.get(url, params=params)
    return response.json()


def format_weather(weather_data):
    """Форматирование данных о погоде"""
    if 'main' not in weather_data:
        return "Не удалось получить данные о погоде"

    return (
        f"Погода в {weather_data['name']}:\n"
        f"🌡 Температура: {weather_data['main']['temp']}°C\n"
        f"💧 Влажность: {weather_data['main']['humidity']}%\n"
        f"🌬 Ветер: {weather_data['wind']['speed']} м/с\n"
        f"☁ {weather_data['weather'][0]['description'].capitalize()}"
    )


def send_daily_weather():
    """Функция для ежедневной отправки погоды"""
    while True:
        now = datetime.now().strftime('%H:%M')
        for chat_id, city, time in get_all_users():
            if now == time:
                weather = get_weather(city)
                if 'main' in weather:
                    bot.send_message(chat_id, format_weather(weather))
        sleep(60)


@bot.message_handler(commands=['start'])
def start(message):
    """Обработка команды /start"""
    if get_user(message.chat.id):
        bot.send_message(
            message.chat.id,
            'Вы уже подписаны на уведомления.\n'
            'Используйте:\n'
            '/change_city - изменить город\n'
            '/change_time - изменить время\n'
            '/stop - не присылать уведомления'
        )
        return

    msg = bot.send_message(message.chat.id, 'Введите город для получения погоды:')
    bot.register_next_step_handler(msg, process_city_step)


def process_city_step(message):
    """Обработка ввода города"""
    user_states[message.chat.id] = {'city': message.text}
    msg = bot.send_message(
        message.chat.id,
        'Введите время отправки уведомлений (ЧЧ:ММ):'
    )
    bot.register_next_step_handler(msg, process_time_step)


def process_time_step(message):
    """Обработка ввода времени"""
    try:
        time = datetime.strptime(message.text, '%H:%M').time()
        save_user(
            message.chat.id,
            user_states[message.chat.id]['city'],
            message.text
        )
        bot.send_message(
            message.chat.id,
            f"Отлично! Буду присылать погоду для {user_states[message.chat.id]['city']} "
            f"каждый день в {message.text}"
        )
        del user_states[message.chat.id]
    except ValueError:
        msg = bot.send_message(
            message.chat.id,
            'Неверный формат времени. Введите в формате ЧЧ:ММ'
        )
        bot.register_next_step_handler(msg, process_time_step)


@bot.message_handler(commands=['change_city'])
def change_city(message):
    """Обработка команды /change_city"""
    if not get_user(message.chat.id):
        bot.send_message(
            message.chat.id,
            'Сначала подпишитесь на уведомления через /start'
        )
        return

    msg = bot.send_message(message.chat.id, 'Введите новый город:')
    bot.register_next_step_handler(msg, process_city_change_step)


def process_city_change_step(message):
    """Обработка изменения города"""
    user_data = get_user(message.chat.id)
    save_user(
        message.chat.id,
        message.text,
        user_data[1]  # Сохраняем старое время
    )
    bot.send_message(
        message.chat.id,
        f'Город изменен на {message.text}'
    )

@bot.message_handler(commands=['help'])
def show_help(message):
    """Показывает список всех доступных команд"""
    help_text = """
📚 *Доступные команды:*

/start - Начать настройку уведомлений
/help - Показать это сообщение
/weather - Получить текущую погоду
/change_city - Изменить город для уведомлений
/change_time - Изменить время уведомлений
/stop - Отписаться от уведомлений

Пример использования:
1. Сначала введите /start
2. Укажите город (например, Москва)
3. Укажите время в формате ЧЧ:ММ (например, 09:00)
4. Получайте ежедневные уведомления!
"""
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['change_time'])
def change_time(message):
    """Обработка команды /change_time"""
    if not get_user(message.chat.id):
        bot.send_message(
            message.chat.id,
            'Сначала подпишитесь на уведомления через /start'
        )
        return

    msg = bot.send_message(message.chat.id, 'Введите новое время (ЧЧ:ММ):')
    bot.register_next_step_handler(msg, process_time_change_step)


def process_time_change_step(message):
    """Обработка изменения времени"""
    try:
        time = datetime.strptime(message.text, '%H:%M').time()
        user_data = get_user(message.chat.id)
        save_user(
            message.chat.id,
            user_data[0],  # Сохраняем старый город
            message.text
        )
        bot.send_message(
            message.chat.id,
            f'Время уведомлений изменено на {message.text}'
        )
    except ValueError:
        msg = bot.send_message(
            message.chat.id,
            'Неверный формат времени. Введите в формате ЧЧ:ММ'
        )
        bot.register_next_step_handler(msg, process_time_change_step)


@bot.message_handler(commands=['stop'])
def stop(message):
    """Обработка команды /stop"""
    if delete_user(message.chat.id):
        bot.send_message(message.chat.id, 'Вы отписались от уведомлений')
    else:
        bot.send_message(message.chat.id, 'Вы отписались от уведомлений')


@bot.message_handler(commands=['weather'])
def weather_now(message):
    """Получить текущую погоду"""
    user_data = get_user(message.chat.id)
    if user_data:
        weather = get_weather(user_data[0])
        if 'main' in weather:
            bot.send_message(message.chat.id, format_weather(weather))
        else:
            bot.send_message(message.chat.id, 'Не удалось получить погоду')
    else:
        bot.send_message(
            message.chat.id,
            'Сначала настройте уведомления через /start'
        )


if __name__ == '__main__':
    # Запуск потока для ежедневной отправки погоды
    Thread(target=send_daily_weather, daemon=True).start()
    bot.polling(none_stop=True)