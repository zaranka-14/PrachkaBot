import asyncio
import logging
from aiogram import Bot, Dispatcher

from prachka_bot import config
from prachka_bot.handlers import common, client, admin

import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
while current_dir != os.path.dirname(current_dir):
    if os.path.exists(os.path.join(current_dir, "pyproject.toml")):
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        break
    current_dir = os.path.dirname(current_dir)

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
