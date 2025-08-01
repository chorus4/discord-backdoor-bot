from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from sqlmodel import Session as SQLSession
from sqlmodel import select
from aiogram.types import CallbackQuery


welcome_router = Router()

def get_welcome_message():
  msg = [
    "Dicord backdoor exploit",
    "",
    "Выбери действие ниже ⬇️"
  ]
  msg = '\n'.join(msg)
  return msg

@welcome_router.message(CommandStart())
async def welcome_handler(message: Message):
  await message.answer(get_welcome_message())