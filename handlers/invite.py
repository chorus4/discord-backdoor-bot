from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
import aiogram.utils.formatting as format

from handlers.guilds import CreateInviteCallback, GetServerCallback
from ds.guilds import get_guild

invite_router = Router()



# =============Get Invites=======================

@invite_router.callback_query(F.data == "get_invites")
async def get_invites(callback_query: CallbackQuery, state: FSMContext):
  state_data = await state.get_data()
  bot_id = state_data["bot_id"]
  guild_id = state_data["guild_id"]
  guild = await get_guild(bot_id, guild_id)

  builder = InlineKeyboardBuilder()
  builder.row(InlineKeyboardButton(text="Создать ссылку-приглашение 🔗", callback_data=CreateInviteCallback(bot_id=bot_id, server_id=guild_id).pack()))
  builder.row(InlineKeyboardButton(text=f'🔙 Назад', callback_data=GetServerCallback(bot_id=state_data["bot_id"], server_id=state_data["guild_id"]).pack()))

  invites = await guild.invites()

  text = [
    f"<b>Ссылки-приглашения сервера</b> {guild.name}",
    ""
  ]

  for invite in invites:
    text.append(f"{invite.inviter.name} - <a href='{invite.url}'>#{invite.channel.name}</a> - {invite.created_at.strftime('%H:%M:%S %d/%m/%Y')}")

  text = '\n'.join(text)

  await callback_query.message.edit_text(text, reply_markup=builder.as_markup())

# ==============Create Invite====================
class CreateInviteFSM(StatesGroup):
  max_age = State()
  max_uses = State()

def get_invite_keyboard(state):
  builder = InlineKeyboardBuilder()

  builder.row(InlineKeyboardButton(text=f'Срок жизни: {"Бесконечно" if state["max_age"] == 0 else f"{state["max_age"]} минут"}', callback_data='change-max_age'))
  builder.row(InlineKeyboardButton(text=f'Максимальное количество пользователей: {"Бесконечно" if state["max_uses"] == 0 else state["max_uses"]}', callback_data='change-max_users'))
  builder.row(InlineKeyboardButton(text=f'Временное: {"Да" if state["temporary"] else "Нет"}', callback_data='change-temporary-invite'))
  builder.row(InlineKeyboardButton(text=f'Создать ➕', callback_data='create_invite'))
  builder.row(InlineKeyboardButton(text=f'🔙 Назад', callback_data=GetServerCallback(bot_id=state["bot_id"], server_id=state["guild_id"]).pack()))

  return builder.as_markup()

@invite_router.callback_query(CreateInviteCallback.filter())
async def create_invite_callback(callback_query: CallbackQuery, callback_data: CreateInviteCallback, state: FSMContext):
  bot_id = callback_data.bot_id
  guild_id = callback_data.server_id
  guild = await get_guild(bot_id, guild_id)

  await state.update_data(bot_id=bot_id, guild_id=guild_id)
  state_data = await state.get_data()

  if not "max_age" in state_data:
    await state.update_data(max_age=0, max_uses=0, temporary=False)

  await callback_query.message.edit_text(f"<b>Создание приглашения на сервере</b> {guild.name}", reply_markup=get_invite_keyboard(state_data))

@invite_router.callback_query(F.data == "change-temporary-invite")
async def chabge_temporary_invite(callback_query: CallbackQuery, state: FSMContext):
  state_data = await state.get_data()
  bot_id = state_data["bot_id"]
  guild_id = state_data["guild_id"]
  guild = await get_guild(bot_id, guild_id)

  await state.update_data(temporary=not state_data['temporary'])
  state_data = await state.get_data()
  await callback_query.message.edit_text(f"<b>Создание приглашения на сервере</b> {guild.name}", reply_markup=get_invite_keyboard(state_data))

@invite_router.callback_query(F.data == "change-max_age")
async def change_max_age_invite(callback_query: CallbackQuery, state: FSMContext):
  state_data = await state.get_data()
  bot_id = state_data["bot_id"]
  guild_id = state_data["guild_id"]
  guild = await get_guild(bot_id, guild_id)

  builder = InlineKeyboardBuilder()
  builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data=CreateInviteCallback(bot_id=bot_id, server_id=guild_id).pack()))

  await callback_query.message.edit_text("Введите срок жизни приглашения (в минутах)", reply_markup=builder.as_markup())
  await state.set_state(CreateInviteFSM.max_age)
  await state.update_data(msg_id=callback_query.message.message_id)

@invite_router.callback_query(F.data == "change-max_users")
async def change_max_uses_invite(callback_query: CallbackQuery, state: FSMContext):
  state_data = await state.get_data()
  bot_id = state_data["bot_id"]
  guild_id = state_data["guild_id"]
  guild = await get_guild(bot_id, guild_id)

  builder = InlineKeyboardBuilder()
  builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data=CreateInviteCallback(bot_id=bot_id, server_id=guild_id).pack()))

  await callback_query.message.edit_text("Введите максимальное количество пользователей для приглашения", reply_markup=builder.as_markup())
  await state.set_state(CreateInviteFSM.max_uses)
  await state.update_data(msg_id=callback_query.message.message_id)

@invite_router.message(CreateInviteFSM.max_age)
async def max_age_handler(message: Message, state: FSMContext):
  state_data = await state.get_data()
  bot_id = state_data["bot_id"]
  guild_id = state_data["guild_id"]
  msg_id = state_data["msg_id"]
  guild = await get_guild(bot_id, guild_id)

  await message.delete()
  
  if not message.text.isnumeric():
    return 
  
  await state.update_data(max_age=int(message.text))
  state_data = await state.get_data()
  await state.set_state()
  await message.bot.edit_message_text(f"<b>Создание приглашения на сервере</b> {guild.name}", chat_id=message.chat.id, message_id=msg_id, reply_markup=get_invite_keyboard(state_data))

@invite_router.message(CreateInviteFSM.max_uses)
async def max_age_handler(message: Message, state: FSMContext):
  state_data = await state.get_data()
  bot_id = state_data["bot_id"]
  guild_id = state_data["guild_id"]
  msg_id = state_data["msg_id"]
  guild = await get_guild(bot_id, guild_id)

  await message.delete()
  
  if not message.text.isnumeric():
    return 
  
  await state.update_data(max_uses=int(message.text))
  state_data = await state.get_data()
  await state.set_state()
  await message.bot.edit_message_text(f"<b>Создание приглашения на сервере</b> {guild.name}", chat_id=message.chat.id, message_id=msg_id, reply_markup=get_invite_keyboard(state_data))

@invite_router.callback_query(F.data == "create_invite")
async def create_invite(callback_query: CallbackQuery, state: FSMContext):
  state_data = await state.get_data()
  bot_id = state_data["bot_id"]
  guild_id = state_data["guild_id"]
  guild = await get_guild(bot_id, guild_id)
  channel = guild.text_channels[0]

  invite = await channel.create_invite(max_age=state_data['max_age'], max_uses=state_data['max_uses'], temporary=state_data['temporary'])

  builder = InlineKeyboardBuilder()
  builder.row(InlineKeyboardButton(text='🔙 Назад', callback_data=GetServerCallback(bot_id=state_data["bot_id"], server_id=state_data["guild_id"]).pack()))

  await callback_query.message.edit_text(invite.url, reply_markup=builder.as_markup())