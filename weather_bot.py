import requests
import warnings
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackContext,
    CallbackQueryHandler, MessageHandler, filters, ConversationHandler)
from telegram.warnings import PTBUserWarning

warnings.filterwarnings("ignore", category=PTBUserWarning)

WEATHER_API_KEY = 'c75f48b92d46fc0a91e2ce85a8a53915'
TELEGRAM_TOKEN = '7524922007:AAGhR2F8-FY4grVzxt7PiBIGN5M85QiWN5o'

SELECTING_ACTION, GETTING_WEATHER_CITY, GETTING_CLOTHING_CITY = range(3)

WEATHER_EMOJIS = {
    "Clear": ("🌞", "Ясно"),
    "Clouds": ("☁️", "Облачно"),
    "Rain": ("🌧", "Дождь"),
    "Thunderstorm": ("⛈", "Гроза"),
    "Snow": ("❄️", "Снег"),
    "Drizzle": ("🌦", "Морось"),
    "Mist": ("🌫", "Туман")
}

async def start(update: Update, context: CallbackContext) -> int:
    keyboard = [
        [InlineKeyboardButton("Прогноз погоды 🌤", callback_data='weather')],
        [InlineKeyboardButton("Совет по одежде 👚👕", callback_data='clothing_advice')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text('Привет! 👋\nВыберите действие:', reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text('Привет! 👋\nВыберите действие:', reply_markup=reply_markup)
    return SELECTING_ACTION

async def weather_options(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("На сегодня 🌤", callback_data='weather_today')],
        [InlineKeyboardButton("На 3 дня 🌦", callback_data='weather_3_days')],
        [InlineKeyboardButton("На 5 дней 📆", callback_data='weather_5_days')],
        [InlineKeyboardButton("Назад ↩️", callback_data='back_to_main')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Выберите период прогноза ⏳:", reply_markup=reply_markup)
    return SELECTING_ACTION

async def ask_weather_city(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == 'weather_today':
        context.user_data['forecast_days'] = 1
    elif query.data == 'weather_3_days':
        context.user_data['forecast_days'] = 3
    elif query.data == 'weather_5_days':
        context.user_data['forecast_days'] = 5

    await query.edit_message_text("Введите название города для прогноза погоды 🌤:")
    return GETTING_WEATHER_CITY

async def handle_weather_city(update: Update, context: CallbackContext) -> int:
    city = update.message.text
    days = context.user_data.get('forecast_days', 1)

    forecast_info = await get_forecast(city, days)

    keyboard = [[InlineKeyboardButton("Назад ↩️", callback_data='back_to_main')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(forecast_info, reply_markup=reply_markup)
    return SELECTING_ACTION

async def get_forecast(city: str, days: int) -> str:
    if days == 1:
        return await get_current_weather(city)

    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    response = requests.get(url)

    if response.status_code != 200:
        return "❌ Город не найден."

    data = response.json()
    if 'list' not in data or not data['list']:
        return "❌ Нет доступных данных для прогноза."

    forecast_days = {}
    for item in data['list']:
        date_time = datetime.strptime(item['dt_txt'], "%Y-%m-%d %H:%M:%S")
        date = date_time.date()
        time = date_time.time()

        if date not in forecast_days:
            forecast_days[date] = {}

        if time.hour in [9, 10, 11]:
            forecast_days[date]['morning'] = item
        elif time.hour in [15, 16, 17]:
            forecast_days[date]['day'] = item
        elif time.hour in [21, 22, 23]:
            forecast_days[date]['evening'] = item

    result = [f"Прогноз погоды в {city} на {days} дней:\n"]

    for i, (date, times) in enumerate(sorted(forecast_days.items())):
        if i >= days:
            break

        date_str = date.strftime("%d.%m.%Y")
        day_name = get_day_name(date)
        result.append(f"\n📅 {day_name}, {date_str}")

        for time_name in ['morning', 'day', 'evening']:
            if time_name in times:
                item = times[time_name]
                temp = item['main']['temp']
                weather = item['weather'][0]['main']
                emoji, desc = WEATHER_EMOJIS.get(weather, ("", "Неизвестно"))

                time_label = {
                    'morning': '🌅 Утро (10:00)',
                    'day': '🌞 День (16:00)',
                    'evening': '🌙 Вечер (22:00)'
                }[time_name]

                result.append(f"{time_label}: {temp}°C, {desc} {emoji}")

    return "\n".join(result) if result else "❌ Нет данных для отображения"

def get_day_name(date):
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    return days[date.weekday()]

async def get_current_weather(city: str) -> str:
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    response = requests.get(url)

    if response.status_code != 200:
        return "❌ Город не найден."

    data = response.json()
    temp = data['main']['temp']
    feels_like = data['main']['feels_like']
    humidity = data['main']['humidity']
    wind_speed = data['wind']['speed']
    weather = data['weather'][0]['main']
    emoji, desc = WEATHER_EMOJIS.get(weather, ("", "Неизвестно"))

    return (f"Погода в {city} сегодня 🌤:\n"
            f"🌡 Температура: {temp}°C (ощущается как {feels_like}°C)\n"
            f"💧 Влажность: {humidity}%\n"
            f"🌬 Ветер: {wind_speed} м/с\n"
            f"🌦 Условия: {desc} {emoji}")

async def ask_clothing_city(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Введите название города для совета по одежде 👗:")
    return GETTING_CLOTHING_CITY

async def handle_clothing_advice(update: Update, context: CallbackContext) -> int:
    city = update.message.text
    weather_data = fetch_weather_data(city)

    if not weather_data:
        await update.message.reply_text("❌ Не удалось получить данные о погоде. Проверьте название города.")
        return SELECTING_ACTION

    try:
        advice = generate_clothing_advice(weather_data['temp'], weather_data['city'])
        keyboard = [[InlineKeyboardButton("Назад ↩️", callback_data='back_to_main')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(advice, reply_markup=reply_markup)
    except KeyError as e:
        await update.message.reply_text("❌ Произошла ошибка при обработке данных о погоде.")
        print(f"KeyError in handle_clothing_advice: {e}")

    return SELECTING_ACTION

def fetch_weather_data(city: str) -> dict:
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                'temp': data['main']['temp'],
                'city': city,
                'weather': data['weather'][0]['main'] if data.get('weather') else 'Unknown'
            }
        return None
    except (requests.RequestException, ValueError, KeyError):
        return None

def generate_clothing_advice(temp: float, city: str) -> str:
    if temp < 0:
        return (f"На сегодня температура в {city} {temp}°C ❄️. Очень холодно! "
                f"Наденьте теплую куртку 🧥, шапку 🧢, перчатки 🧤 и шарф 🧣.")
    elif 0 <= temp < 10:
        return (f"На сегодня температура в {city} {temp}°C 🌬. Прохладно. "
                f"Рекомендуется куртка 🧥 и свитер 🧶.")
    elif 10 <= temp < 20:
        return (f"На сегодня температура в {city} {temp}°C 🌤. Тепло, но не жарко. "
                f"Лучше всего подойдет легкая куртка 🧥 или толстовка 👚.")
    elif 20 <= temp < 30:
        return (f"На сегодня температура в {city} {temp}°C 🌞. Довольно тепло. "
                f"Можно надеть футболку 👕 и шорты 👖.")
    else:
        return (f"На сегодня температура в {city} {temp}°C 🔥. Жара! "
                f"Легкая одежда 👗 и головной убор 🧢 — отличный выбор.")

async def back_to_main(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    return await start(update, context)

def main() -> None:
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_ACTION: [
                CallbackQueryHandler(weather_options, pattern='^weather$'),
                CallbackQueryHandler(ask_clothing_city, pattern='^clothing_advice$'),
                CallbackQueryHandler(ask_weather_city, pattern='^weather_today$|^weather_3_days$|^weather_5_days$'),
                CallbackQueryHandler(back_to_main, pattern='^back_to_main$'),
            ],
            GETTING_WEATHER_CITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_weather_city),
            ],
            GETTING_CLOTHING_CITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_clothing_advice),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    print("Бот запущен! 🚀")
    app.run_polling()

if __name__ == '__main__':
    main()
