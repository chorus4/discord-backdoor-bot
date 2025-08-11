import discord
from sqlmodel import select
from sqlmodel import Session as SQLSession
import asyncio

import db
from db.models.dsBots import DsBot
from ds.botStorage import botStorage
from discord.ext.tasks import Loop

async def get_all_guilds(bot_id):
  session = SQLSession(db.engine)
  bot = session.exec(select(DsBot).where(DsBot.id == bot_id)).first()
  client = botStorage.get_bot(bot.id)

  return client.guilds

async def get_guild(bot_id, guild_id):
  session = SQLSession(db.engine)
  bot = session.exec(select(DsBot).where(DsBot.id == bot_id)).first()
  client = botStorage.get_bot(bot.id)

  return client.get_guild(guild_id)

async def edit_role(role, *args, **kwargs):
  # loop = asyncio.get_event_loop()
  # await loop.run_until_complete(await edt_rl(role, *args, **kwargs))
  task = asyncio.create_task(role.edit(*args, **kwargs))
  task = Loop.start(task)
  await task

async def edt_rl(role, *args, **kwargs):
 await role.edit(*args, **kwargs)