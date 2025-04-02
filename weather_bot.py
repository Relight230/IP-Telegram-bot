import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Вставьте ваш API-ключ OpenWeatherMap и токен Telegram-бота
WEATHER_API_KEY = 'c75f48b92d46fc0a91e2ce85a8a53915'
TELEGRAM_TOKEN = '7524922007:AAGhR2F8-FY4grVzxt7PiBIGN5M85QiWN5o'

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Привет! Напиши /weather <город>, чтобы получить прогноз погоды.')


async def get_weather(city: str) -> str:
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        weather_description = data['weather'][0]['description']
        temperature = data['main']['temp']
        return f"Погода в {city}: {weather_description}, температура: {temperature}°C."
    else:
        return "Не удалось получить данные о погоде. Проверьте название города."


async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:
        city = ' '.join(context.args)
        weather_info = await get_weather(city)
        await update.message.reply_text(weather_info)
    else:
        await update.message.reply_text('Пожалуйста, укажите город. Пример: /weather Москва')


async def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("weather", weather))

    await application.run_polling()


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())

