from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, Message
from aiogram.fsm.state import State, StatesGroup
import asyncio


from ds.guilds import get_guild
from handlers.guilds import GetServerCallback
from ds.utils.logs_loop import logs_stop_event, logs_task
from ds.logs import clear_logs

logs_router = Router()

class LogsFSM(StatesGroup):
  change_iterations = State()

async def get_clear_logs_preparation_keyboard(state_data):
  builder = InlineKeyboardBuilder()
  builder.row(InlineKeyboardButton(text=f'Количество итераций: {state_data['iterations']}', callback_data='change-iterations'))
  builder.row(InlineKeyboardButton(text=f'Запуск 🧹', callback_data='start-clearing-logs'))
  builder.row(InlineKeyboardButton(text=f'🔙 Назад', callback_data=GetServerCallback(bot_id=state_data['bot_id'], server_id=state_data['guild_id']).pack()))

  return builder.as_markup()

async def get_clear_logs_preparation_text():
  msg = [
    "<b>Очистка логов 🧹</b>",
    "",
    "Эта функция создает огромное количество мусорных записей в журнале аудита тем самым администраторам может быть сложнее найти нужное действие в логах",
  ]
  msg = '\n'.join(msg)
  return msg

@logs_router.callback_query(F.data == 'clear-logs')
async def clear_logs_callback(callback_query: CallbackQuery, state: FSMContext):
  state_data = await state.get_data()
  bot_id = state_data['bot_id']
  guild_id = state_data['guild_id']

  guild = await get_guild(bot_id, guild_id)

  await state.set_state()
  await callback_query.message.edit_text(await get_clear_logs_preparation_text(), reply_markup=await get_clear_logs_preparation_keyboard(state_data))

@logs_router.callback_query(F.data == 'change-iterations')
async def change_iterations_callback(callback_query: CallbackQuery, state: FSMContext):
  builder = InlineKeyboardBuilder()
  builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data='clear-logs'))

  await callback_query.message.edit_text("Введите количество итераций (макс 50) ⬇️", reply_markup=builder.as_markup())
  await state.set_state(LogsFSM.change_iterations)
  await state.update_data(last_msg=callback_query.message.message_id)

@logs_router.message(LogsFSM.change_iterations)
async def iterations_handler(message: Message, state: FSMContext):
  state_data = await state.get_data()
  msg_id = state_data['last_msg']

  await message.delete()

  if not message.text.isnumeric():
    return 
  if int(message.text) > 50:
    return
  
  await state.update_data(iterations=int(message.text))
  await state.set_state()
  state_data = await state.get_data()

  await message.bot.edit_message_text(await get_clear_logs_preparation_text(), reply_markup=await get_clear_logs_preparation_keyboard(state_data), chat_id=message.chat.id, message_id=msg_id)

@logs_router.callback_query(F.data == 'start-clearing-logs')
async def start_cleaning_logs_callback(callback_query: CallbackQuery, state: FSMContext):
  state_data = await state.get_data()
  bot_id = state_data['bot_id']
  guild_id = state_data['guild_id']
  iterations = state_data['iterations']

  await callback_query.message.edit_text("Запуск процесса очистки логов 🕐")

  global logs_task
  global logs_stop_event

  if logs_task and not logs_task.done():
    await callback_query.answer("Уже запущено!", show_alert=True)
    return

  logs_stop_event.clear()
  logs_task = asyncio.create_task(clear_logs(callback_query.bot, callback_query.message.message_id, callback_query.message.chat.id, bot_id, guild_id, iterations))

@logs_router.callback_query(F.data == 'stop-logs')
async def stop_cleaning_logs_callback(callback_query: CallbackQuery, state: FSMContext):
  logs_stop_event.set()


"""
LOGIC OF CLEARING LOGS

1. Change rate limit/bitrate in vc
2. Create invite
3. Delete that invite
4. Change rate limit/bitrate in vc (revert to default state)

"""