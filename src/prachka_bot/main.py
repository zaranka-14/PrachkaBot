import asyncio
import logging
from aiogram import Bot, Dispatcher

from prachka_bot import config
from prachka_bot.handlers import common, client, admin

logging.basicConfig(level=logging.INFO)


async def run_bot():
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(common.router)
    dp.include_router(client.router)
    dp.include_router(admin.router)

    await dp.start_polling(bot)


def main():
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
