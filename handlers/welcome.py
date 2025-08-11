from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from sqlmodel import Session as SQLSession
from sqlmodel import select
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext


welcome_router = Router()

def get_welcome_message():
  msg = [
    "Dicord backdoor exploit",
    "",
    "Выбери действие ниже ⬇️"
  ]
  msg = '\n'.join(msg)
  return msg

def get_welcome_keyboard():
  builder = InlineKeyboardBuilder()
  builder.add(InlineKeyboardButton(text="Управление ботами", callback_data="manage_bots"))
  return builder.as_markup()

@welcome_router.message(CommandStart())
async def welcome_handler(message: Message):
  await message.answer(get_welcome_message(), reply_markup=get_welcome_keyboard())

@welcome_router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback_query: CallbackQuery, state: FSMContext):
  await state.clear()
  await callback_query.message.edit_text(get_welcome_message(), reply_markup=get_welcome_keyboard())