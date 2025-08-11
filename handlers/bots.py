from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, MessageReactionUpdated
from sqlmodel import Session as SQLSession
from sqlmodel import select
from aiogram.types import CallbackQuery
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
import os
import sys

import re

import ds
from ds.guilds import get_all_guilds
import db
from db.models.dsBots import DsBot

bots_router = Router()

def restart_script():
    os.execv(sys.executable, [sys.executable] + sys.argv)

class ManageBotCallback(CallbackData, prefix="manageBot"):
  bot_id: int

class NewBotFSM(StatesGroup):
  name = State()
  token = State()
  lastMsg = State()

def get_main_menu_keyboard():
  builder = InlineKeyboardBuilder()
  builder.row(InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu"))
  return builder.as_markup()

@bots_router.callback_query(F.data == "manage_bots")
async def manage_bots_callback(callback_query: CallbackQuery, state: FSMContext):
  await state.clear()

  text = [
    "Выбери действие ниже ⬇️"
  ]
  text =  '\n'.join(text)
  await callback_query.message.edit_text(text)

  builder = InlineKeyboardBuilder()
  builder.row(InlineKeyboardButton(text="➕ Добавить бота", callback_data="add_bot"))

  with SQLSession(db.engine) as session:
    dsBots = session.exec(select(DsBot))

    for bot in dsBots:
      builder.row(InlineKeyboardButton(text=f"🤖 {bot.name}", callback_data=ManageBotCallback(bot_id=bot.id).pack()))
  
  builder.row(InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu"))
  
  await callback_query.message.edit_text(text, reply_markup=builder.as_markup())

@bots_router.callback_query(F.data == "add_bot")
async def add_bot_callback(callback_query: CallbackQuery, state: FSMContext):
  msgId = await callback_query.message.edit_text("Введите название бота ⬇️", reply_markup=get_main_menu_keyboard())
  await state.update_data(lastMsg=msgId.message_id)

  await state.set_state(NewBotFSM.name)

@bots_router.message(NewBotFSM.name)
async def name_message_handler(message: Message, state: FSMContext):
  state_data = await state.get_data()

  # await message.bot.delete_message(message.chat.id, int(state_data["lastMsg"]))
  await message.bot.delete_message(message.chat.id, message.message_id)

  msgId = await message.bot.edit_message_text(chat_id=message.chat.id, message_id=int(state_data["lastMsg"]), text="Введите токен бота ⬇️", reply_markup=get_main_menu_keyboard())
  await state.update_data(name=message.text, lastMsg=msgId.message_id)
  await state.set_state(NewBotFSM.token)

@bots_router.message(NewBotFSM.token)
async def name_message_handler(message: Message, state: FSMContext):
  # if not (re.fullmatch(r'^[\w-]{24}\.[\w-]{6}\.[\w-]{38}$', message.text) or re.fullmatch(r'^mfa\.[\w-]{84}$', message.text)): # TODO: ADD TOKEN VALIDATION
  #   await message.answer("Пожалуйста укажите правильный токен")
  #   return
  
  state_data = await state.get_data()

  await message.bot.delete_message(message.chat.id, message.message_id)

  await state.clear()

  with SQLSession(db.engine) as session:
    dsBot = DsBot(name=state_data["name"], token=message.text)

    session.add(dsBot)
    session.commit()
    await message.bot.edit_message_text(chat_id=message.chat.id, message_id=int(state_data["lastMsg"]), text="Бот успешно добавлен, перезагрузка скрипта ♻️", reply_markup=get_main_menu_keyboard())
    # ds.start_bot(dsBot.id)
    restart_script()
    exit()

# Managing bots

class DeleteBotCallback(CallbackData, prefix="deleteBot"):
  bot_id: int

class GetBotServersCallback(CallbackData, prefix="getBotServers"):
  bot_id: int

class GetServerCallback(CallbackData, prefix="getServer"):
  bot_id: int
  server_id: int

class DeleteBotFSM(StatesGroup):
  delete = State()
  # botId = State()

def get_manage_bot_keyboard(botId):
  builder = InlineKeyboardBuilder()
  builder.row(InlineKeyboardButton(text="🖥 Сервера на которых есть бот", callback_data=GetBotServersCallback(bot_id=botId).pack()))
  builder.row(InlineKeyboardButton(text="❌ Удалить бота", callback_data=DeleteBotCallback(bot_id=botId).pack()))
  builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="manage_bots"))
  return builder.as_markup()

def get_manage_bot_text(botName):
  text = [
    f"Управление ботом \"{botName}\"",
    "",
    "Выберите действие ниже ⬇️"
  ]
  text = '\n'.join(text)
  return text

@bots_router.callback_query(ManageBotCallback.filter())
async def manage_bot_callback(callback_query: CallbackQuery, callback_data: ManageBotCallback, state: FSMContext):
  session = SQLSession(db.engine)
  bot = session.exec(select(DsBot).where(DsBot.id == callback_data.bot_id)).first()

  await state.clear()
  await callback_query.message.edit_text(get_manage_bot_text(bot.name), reply_markup=get_manage_bot_keyboard(bot.id))

@bots_router.callback_query(DeleteBotCallback.filter())
async def delete_bot_callback(callback_query: CallbackQuery, callback_data: DeleteBotCallback, state: FSMContext):
  text = [
    "Вы уверенны?",
    "",
    "Поставьте любую реакцию на это сообщение для подтверждения 🚀"
  ]
  text = '\n'.join(text)

  builder = InlineKeyboardBuilder()
  builder.row(InlineKeyboardButton(text="🔙 Отменить", callback_data=ManageBotCallback(bot_id=callback_data.bot_id).pack()))

  await state.set_state(DeleteBotFSM.delete)
  await state.update_data(botId = callback_data.bot_id)
  await callback_query.message.edit_text(text, reply_markup=builder.as_markup())

@bots_router.message_reaction(DeleteBotFSM.delete)
async def message_reaction_handler(message_reaction: MessageReactionUpdated, state: FSMContext):
  session = SQLSession(db.engine)
  state_data = await state.get_data()

  bot = session.exec(select(DsBot).where(DsBot.id == state_data["botId"])).first()
  await ds.stop_bot(bot.id)
  session.delete(bot)
  session.commit()

  message_id = message_reaction.message_id
  chat_id = message_reaction.chat.id

  await message_reaction.bot.delete_message(message_id=message_id, chat_id=chat_id)
  await message_reaction.bot.send_message(chat_id, "Успешно ✅", reply_markup=get_main_menu_keyboard())

@bots_router.callback_query(GetBotServersCallback.filter())
async def get_bot_servers_callback(callback_query: CallbackQuery, callback_data: DeleteBotCallback, state: FSMContext):
  botId = callback_data.bot_id

  guilds = await get_all_guilds(botId)
  builder = InlineKeyboardBuilder()

  for guild in guilds:
    builder.row(InlineKeyboardButton(text=guild.name, callback_data=GetServerCallback(bot_id=botId, server_id=guild.id).pack()))
  
  builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=ManageBotCallback(bot_id=botId).pack()))

  await callback_query.message.edit_text("Сервера на которых есть бот ⬇️", reply_markup=builder.as_markup())