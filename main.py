import os
from dotenv import load_dotenv
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from handlers.welcome import welcome_router
from handlers.bots import bots_router
from handlers.guilds import guilds_router
from handlers.members import members_router
from handlers.roles import roles_router
from handlers.invite import invite_router
from handlers.logs import logs_router

from ds import prepare_bots

import db

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

async def main():
  dp.include_routers(
    welcome_router,
    bots_router,
    guilds_router,
    members_router,
    roles_router,
    invite_router,
    logs_router
  )

  try:
    await asyncio.gather(
       dp.start_polling(bot),
        *prepare_bots()
    )
  except KeyboardInterrupt:
    exit()
    await stop_all_bots()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    db.init()
    asyncio.run(main())