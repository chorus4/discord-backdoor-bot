from ds.utils.logs_loop import logs_task, logs_stop_event
from ds.guilds import get_guild
import asyncio
from aiogram import Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from utils.progressbar import progressbar
from handlers.guilds import GetServerCallback

clock_emojis = [
  '🕐',
  '🕑',
  '🕒',
  '🕓',
  '🕔',
  '🕕',
  '🕖',
  '🕗',
  '🕘',
  '🕙',
  '🕚',
  '🕛',
]

def get_keyboard():
  builder = InlineKeyboardBuilder()
  builder.row(InlineKeyboardButton(text='Отмена ❌', callback_data='stop-logs'))
  return builder.as_markup()

def get_back_keyboard(bot_id, guild_id):
  builder = InlineKeyboardBuilder()
  builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data=GetServerCallback(bot_id=bot_id, server_id=guild_id).pack()))
  return builder.as_markup()

async def clear_logs(bot: Bot, message_id, chat_id, bot_id, guild_id, iterations):
  guild = await get_guild(bot_id, guild_id)
  clock_it = 0

  # while not logs_stop_event.is_set():
  #   pass
  for i in range(0, iterations):
    if logs_stop_event.is_set():
      await bot.edit_message_text('Очистка логов отменена ❌', chat_id=chat_id, message_id=message_id, reply_markup=get_back_keyboard(bot_id, guild_id))
      return
      # break

    if clock_it > len(clock_emojis) - 1:
      clock_it = 0
    # await bot.send_message(chat_id=chat_id, text=iterations/i*100)

    msg = [
      f"<b>Очистка логов</b> {clock_emojis[clock_it]}",
      '',
      progressbar(i/iterations*100)
    ]
    msg = '\n'.join(msg)
    clock_it += 1

    vc = guild.voice_channels[0]

    invite = await vc.create_invite()
    await asyncio.sleep(0.5)
    await invite.delete()


    await bot.edit_message_text(msg, chat_id=chat_id, message_id=message_id, reply_markup=get_keyboard())
    await asyncio.sleep(1.5)

  await bot.edit_message_text('Очистка логов завершена ✅', chat_id=chat_id, message_id=message_id, reply_markup=get_back_keyboard(bot_id, guild_id))
