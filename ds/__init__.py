import discord
import asyncio
from sqlmodel import Session as SQLSession
from sqlmodel import select
import threading


from ds.botStorage import botStorage

import db
from db.models.dsBots import DsBot

def start_bot(bot_id):
  session = SQLSession(db.engine)
  bot = session.exec(select(DsBot).where(DsBot.id == bot_id)).first()

  intents = discord.Intents.all()
  intents.message_content = True

  client = discord.Client(intents=intents)

  botStorage.add_bot(bot_id, client)

  @client.event
  async def on_ready():
      print(f'We have logged in as {client.user}')

  return client

async def stop_bot(bot_id):
  session = SQLSession(db.engine)
  bot = session.exec(select(DsBot).where(DsBot.id == bot_id)).first()

  client = botStorage.get_bot(bot.id)

  await client.close()

def prepare_bots():
  session = SQLSession(db.engine)
  bots = session.exec(select(DsBot)).fetchall()
  bts = []

  for bot in bots:
    bts.append(start_bot(bot.id).start(bot.token))

  return bts
