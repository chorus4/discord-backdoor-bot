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
from discord import ChannelType
from discord import Status

import ds
from ds.guilds import get_guild
import db
from db.models.dsBots import DsBot
from handlers.guilds import GetChannelCallback, GetMemberCallback, GetMembersCallback, GetFSM

members_router = Router()

class BanMemberCallback(CallbackData, prefix="banMember"):
  bot_id: int
  server_id: int
  member_id: int

class KickMemberCallback(CallbackData, prefix="kickMember"):
  bot_id: int
  server_id: int
  member_id: int

class EditMemberRolesCallback(CallbackData, prefix="eMR"):
  bot_id: int
  server_id: int
  member_id: int

class EditMemberProfileCallback(CallbackData, prefix="editMemberProfile"):
  bot_id: int
  server_id: int
  member_id: int

class DeleteMemberRoleCallback(CallbackData, prefix="eMR"):
  # bot_id: int
  # server_id: int
  # member_id: int
  role_id: int

class DeleteRoleFSM(StatesGroup):
  delete = State()

def get_member_keyboard(bot_id, guild_id, member):
  builder = InlineKeyboardBuilder()

  # builder.row(InlineKeyboardButton(text="Редактировать профиль сервера 📝", callback_data=EditMemberProfileCallback(bot_id=bot_id, server_id=guild_id, member_id=member.id).pack()))
  builder.row(InlineKeyboardButton(text="Редактировать роли ✏️", callback_data=EditMemberRolesCallback(bot_id=bot_id, server_id=guild_id, member_id=member.id).pack()))

  builder.row(InlineKeyboardButton(text="Забанить 🚫", callback_data=BanMemberCallback(bot_id=bot_id, server_id=guild_id, member_id=member.id).pack()))
  builder.add(InlineKeyboardButton(text="Кикнуть 🚪", callback_data=KickMemberCallback(bot_id=bot_id, server_id=guild_id, member_id=member.id).pack()))

  builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=GetMembersCallback(bot_id=bot_id, server_id=guild_id, offset=0).pack()))
  return builder.as_markup()

statuses = {
  Status.online: "Онлайн",
  Status.offline: "Оффлайн",
  Status.idle: "Простаивает",
  Status.dnd: "Не беспокоить",
  Status.invisible: "Невидимый"
}

def get_member_text(member, guild):
  # created_at = datetime.datetime.strptime(member.created_at, '%Y-%m-%d %H:%M:%S.%f').strftime('%d/%m/%Y')
  created_at = member.created_at.strftime('%d/%m/%Y')


  text = [
    f"<b>Участник {member.name} на сервере {guild.name}</b>",
    "",
    f"<b>Айди:</b> <code>{member.id}</code>",
    f"<b>Тип профиля:</b> {"Бот 🤖" if member.bot else "Человек 👤"}",
    f"<b>Публичный ник:</b> {member.global_name}",
    f"<b>Ник на сервере:</b> {member.nick}",
    f"<b>Дата создания профиля:</b> {created_at}",
    f"<b>Дата захода на сервер:</b> {member.joined_at.strftime('%d/%m/%Y')}",
    f"<b>Статус:</b> {statuses[member.status]}",
    f"<b>Наивысшая роль:</b> {member.top_role.name}"
  ]
  text = '\n'.join(text)
  return text


@members_router.callback_query(GetMemberCallback.filter())
async def get_member_callback(callback_query: CallbackQuery, callback_data: GetMemberCallback, state: FSMContext):
  guild_id = callback_data.server_id
  bot_id = callback_data.bot_id
  member_id = callback_data.member_id
  guild = await get_guild(bot_id, guild_id)
  member = guild.get_member(member_id)

  await callback_query.message.edit_text(get_member_text(member, guild), reply_markup=get_member_keyboard(bot_id, guild_id, member))

@members_router.message(GetFSM.user)
async def get_member_handler(message: Message, state: FSMContext):
  state_data = await state.get_data()
  guild_id = state_data["guild_id"]
  bot_id = state_data["bot_id"]
  last_message = state_data["last_message"]

  try:
    member_id = int(message.text)
  except Exception:
    await message.delete()
    return

  guild = await get_guild(bot_id, guild_id)
  member = guild.get_member(member_id)

  if member == None:
    await message.delete()
    return

  await message.delete()
  await message.bot.edit_message_text(get_member_text(member, guild), chat_id=message.chat.id, message_id=last_message, reply_markup=get_member_keyboard(bot_id, guild_id, member))

@members_router.callback_query(EditMemberRolesCallback.filter())
async def edit_member_roles_callback(callback_query: CallbackQuery, callback_data: EditMemberRolesCallback, state: FSMContext):
  guild_id = callback_data.server_id
  bot_id = callback_data.bot_id
  member_id = callback_data.member_id
  guild = await get_guild(bot_id, guild_id)
  member = guild.get_member(member_id)
  roles = member.roles[::-1]

  await state.clear()
  await state.update_data(guild_id=guild_id, bot_id=bot_id, member_id=member_id)

  builder = InlineKeyboardBuilder()

  builder.row(InlineKeyboardButton(text="Добавить роль ➕", callback_data="add_role_to_member"))

  for role in roles:
    builder.row(InlineKeyboardButton(text=f"{role.name}", callback_data=DeleteMemberRoleCallback(role_id=role.id).pack()))

    # if role.id == callback_data.role_id and role.name != "@everyone":
      # builder.row(InlineKeyboardButton(text="⬆️ Выше", callback_data="1"))
      # builder.row(InlineKeyboardButton(text="Убрать роль ❌", callback_data="1"))
      # builder.add(InlineKeyboardButton(text="Ниже ⬇️", callback_data="1"))

  builder.row(InlineKeyboardButton(text=f"🔙 Назад", callback_data=GetMemberCallback(bot_id=bot_id, server_id=guild_id, member_id=member_id).pack()))
  
  await callback_query.message.edit_text(f"<b>Роли пользователя</b> {member.name}", reply_markup=builder.as_markup())

@members_router.callback_query(DeleteMemberRoleCallback.filter())
async def delete_member_role_callback(callback_query: CallbackQuery, callback_data: DeleteMemberRoleCallback, state: FSMContext):
  state_data = await state.get_data()
  guild_id = state_data["guild_id"]
  bot_id = state_data['bot_id']
  member_id = state_data['member_id']
  role_id = callback_data.role_id
  guild = await get_guild(bot_id, guild_id)
  # member = guild.get_member(member_id)
  role = guild.get_role(role_id)

  if not guild.me.guild_permissions.manage_roles:
    await callback_query.answer("У бота нет прав на редактирование ролей")
    return
  if role.position > guild.self_role.position:
    await callback_query.answer("Эта роль стоит выше чем роль бота")
    return
  if role.name == "@everyone":
    await callback_query.answer("Вы не можете убрать роль @everyone")
    return


  text = [
    "Вы точно хотите убрать роль?",
    "",
    "Поставьте любую реакцию на это сообщение для подтверждения 🚀"
  ]
  text = '\n'.join(text)

  builder = InlineKeyboardBuilder()
  builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=EditMemberRolesCallback(bot_id=bot_id, server_id=guild_id, member_id=member_id).pack()))

  await state.set_state(DeleteRoleFSM.delete)
  await state.update_data(role_id=role_id)
  await callback_query.message.edit_text(text, reply_markup=builder.as_markup())

@members_router.message_reaction(DeleteRoleFSM.delete)
async def delete_role_reaction_handler(message_reaction: MessageReactionUpdated, state: FSMContext):
  state_data = await state.get_data()
  guild_id = state_data["guild_id"]
  bot_id = state_data['bot_id']
  member_id = state_data['member_id']
  role_id = state_data['role_id']
  guild = await get_guild(bot_id, guild_id)

  role = guild.get_role(role_id)
  member = guild.get_member(member_id)

  await member.remove_roles(role)

  builder = InlineKeyboardBuilder()
  builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=EditMemberRolesCallback(bot_id=bot_id, server_id=guild_id, member_id=member_id).pack()))

  await state.clear()
  await message_reaction.bot.delete_message(message_id=message_reaction.message_id, chat_id=message_reaction.chat.id)
  await message_reaction.bot.send_message(chat_id=message_reaction.chat.id, text="Роль успешно убрана ✅", reply_markup=builder.as_markup())

class AddRoleToMemberCallback(CallbackData, prefix='adrm'):
  role_id: int

@members_router.callback_query(F.data == "add_role_to_member")
async def edit_member_roles_callback(callback_query: CallbackQuery, state: FSMContext):
  state_data = await state.get_data()
  guild_id = state_data["guild_id"]
  bot_id = state_data['bot_id']
  member_id = state_data['member_id']
  guild = await get_guild(bot_id, guild_id)
  member = guild.get_member(member_id)

  if not guild.me.guild_permissions.manage_roles:
    await callback_query.answer("У бота нет прав на редактирование ролей")
    return

  guild_roles = guild.roles[::-1]
  member_roles = member.roles

  builder = InlineKeyboardBuilder()

  for role in guild_roles:
    if role.position < guild.self_role.position and role.name != "@everyone" and not (role in member_roles):
      builder.row(InlineKeyboardButton(text=f"{role.name}", callback_data=AddRoleToMemberCallback(role_id=role.id).pack()))
  
  builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=EditMemberRolesCallback(bot_id=bot_id, server_id=guild_id, member_id=member_id).pack()))

  await callback_query.message.edit_text("<b>Выберите роль</b>", reply_markup=builder.as_markup())

@members_router.callback_query(AddRoleToMemberCallback.filter())
async def add_role_to_member(callback_query: CallbackQuery, callback_data: AddRoleToMemberCallback, state: FSMContext):
  state_data = await state.get_data()
  guild_id = state_data["guild_id"]
  bot_id = state_data['bot_id']
  member_id = state_data['member_id']
  role_id = callback_data.role_id

  guild = await get_guild(bot_id, guild_id)
  member = guild.get_member(member_id)
  role = guild.get_role(role_id)

  await member.add_roles(role)

  guild_roles = guild.roles[::-1]
  member_roles = member.roles

  builder = InlineKeyboardBuilder()

  for role in guild_roles:
    if role.position < guild.self_role.position and role.name != "@everyone" and not (role in member_roles):
      builder.row(InlineKeyboardButton(text=f"{role.name}", callback_data=AddRoleToMemberCallback(role_id=role.id).pack()))
  
  builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=EditMemberRolesCallback(bot_id=bot_id, server_id=guild_id, member_id=member_id).pack()))

  await callback_query.answer("Успешно")
  await callback_query.message.edit_reply_markup(reply_markup=builder.as_markup())