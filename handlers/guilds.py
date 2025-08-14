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


import ds
from ds.guilds import get_guild
import db
from db.models.dsBots import DsBot
from handlers.bots import GetServerCallback, GetBotServersCallback

guilds_router = Router()

class GetMembersCallback(CallbackData, prefix="getMembers"):
  bot_id: int
  server_id: int
  offset: int

class GetChannelsCallback(CallbackData, prefix="getChannels"):
  bot_id: int
  server_id: int
  offset: int
  filter: int

class GetRolesCallback(CallbackData, prefix="getRoles"):
  bot_id: int
  server_id: int
  role_id: int
  action: int

class GetAuditCallback(CallbackData, prefix="getAudit"):
  bot_id: int
  server_id: int

class CreateInviteCallback(CallbackData, prefix="createInvite"):
  bot_id: int
  server_id: int

@guilds_router.callback_query(GetServerCallback.filter())
async def get_guild_callback(callback_query: CallbackQuery, callback_data: GetServerCallback, state: FSMContext):
  state_data = await state.get_data()
  guild_id = callback_data.server_id
  bot_id = callback_data.bot_id
  if not "max_age" in state_data:
    await state.update_data(max_age=0, max_uses=0, temporary=False)
  await state.update_data(bot_id=bot_id, guild_id=guild_id, confirmation_step=0)

  guild = await get_guild(bot_id, guild_id)

  builder = InlineKeyboardBuilder()

  builder.add(InlineKeyboardButton(text="Участники 👥", callback_data=GetMembersCallback(bot_id=bot_id, server_id=guild_id, offset=0).pack()))
  builder.add(InlineKeyboardButton(text="Каналы 📺", callback_data=GetChannelsCallback(bot_id=bot_id, server_id=guild_id, offset=0, filter=0).pack()))
  builder.add(InlineKeyboardButton(text="Роли 👀", callback_data=GetRolesCallback(bot_id=bot_id, server_id=guild_id, role_id=0, action=0).pack()))
  builder.add(InlineKeyboardButton(text="Журнал аудита 🤖", callback_data=GetAuditCallback(bot_id=bot_id, server_id=guild_id).pack()))
  
  builder.adjust(2, 2)

  builder.row(InlineKeyboardButton(text="Ссылки-приглашения 🔗", callback_data='get_invites'))
  builder.row(InlineKeyboardButton(text="Зачистка логов 🧹", callback_data="q"))
  builder.add(InlineKeyboardButton(text="Снос сервера 🪓", callback_data="q"))

  builder.row(InlineKeyboardButton(text="Покинуть сервер ❌", callback_data=GetAuditCallback(bot_id=bot_id, server_id=guild_id).pack()))
  builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=GetBotServersCallback(bot_id=bot_id).pack()))

  text = [
    f"<b>Подробности сервера \"{guild.name}\"</b>",
    "",
    f"<b>Количество участников:</b> {guild.member_count}",
    f"<b>Количество текстовых каналов:</b> {len(guild.text_channels)}",
    f"<b>Количество голосовых каналов:</b> {len(guild.voice_channels)}",
    "",
    f"<b>Канал с правилами:</b> {guild.rules_channel.name if guild.rules_channel else "Нет"}",
    f"<b>Уровень верификации:</b> {guild.verification_level}",
    f"<b>Стандартная ссылка на сервер:</b> {guild.vanity_url}"
  ]
  text = '\n'.join(text)
  await callback_query.message.edit_text(text, reply_markup=builder.as_markup())

class GetMemberCallback(CallbackData, prefix="getMember"):
  bot_id: int
  server_id: int
  member_id: int

class GetChannelCallback(CallbackData, prefix="getChannel"):
  bot_id: int
  server_id: int
  channel_id: int

class GetFSM(StatesGroup):
  user = State()
  role = State()
  channel = State()

emojiForChannelType = {
  ChannelType.text: "🗒",
  ChannelType.voice: "🗣",
  ChannelType.news: "🗞",
  ChannelType.stage_voice: "📢",
  ChannelType.forum: "💬",
  ChannelType.category: "📁",
  "all": "Все"
}

channelTypeFilter = [
  "all",
  ChannelType.text,
  ChannelType.voice,
  ChannelType.news,
  ChannelType.stage_voice,
  ChannelType.forum,
  ChannelType.category
]

@guilds_router.callback_query(GetMembersCallback.filter())
async def get_members_callback(callback_query: CallbackQuery, callback_data: GetMembersCallback, state: FSMContext):
  guild_id = callback_data.server_id
  bot_id = callback_data.bot_id
  offset = callback_data.offset
  limit = 5

  guild = await get_guild(bot_id, guild_id)
  members = guild.members[offset*limit:limit+offset*limit]

  builder = InlineKeyboardBuilder()

  for member in members:
    builder.row(InlineKeyboardButton(text=f"{"🤖" if member.bot else "👤"} {member.name} {f"| {member.nick}" if member.nick else ""}", callback_data=GetMemberCallback(bot_id=bot_id, server_id=guild_id, member_id=member.id).pack()))
  
  builder.row(InlineKeyboardButton(text="⬅️ Предыдущая страница", callback_data=GetMembersCallback(bot_id=bot_id, server_id=guild_id, offset=offset-1).pack() if offset > 0 else "none"))
  builder.add(InlineKeyboardButton(text="Следующая страница ➡️", callback_data=GetMembersCallback(bot_id=bot_id, server_id=guild_id, offset=offset+1).pack() if offset < (len(guild.members) / limit) - 1 else "none"))
  builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=GetServerCallback(bot_id=bot_id, server_id=guild_id).pack()))

  text = [
    f"<b>Пользователи сервера</b> {guild.name}",
    "",
    "<b>Выберите пользователя ниже либо отправьте его айди в чат</b>"
  ]
  text = "\n".join(text)

  await state.set_state(GetFSM.user)
  await state.update_data(guild_id=guild_id, bot_id=bot_id, last_message=callback_query.message.message_id)
  await callback_query.message.edit_text(text, reply_markup=builder.as_markup())

@guilds_router.callback_query(GetChannelsCallback.filter())
async def get_channels_callback(callback_query: CallbackQuery, callback_data: GetChannelsCallback, state: FSMContext):
  guild_id = callback_data.server_id
  bot_id = callback_data.bot_id
  offset = callback_data.offset
  filtr = callback_data.filter
  new_filter = filtr + 1
  limit = 5

  if new_filter > len(channelTypeFilter):
    new_filter = 0
    filtr = 0

  guild = await get_guild(bot_id, guild_id)
  channels_org = guild.channels
  if channelTypeFilter[filtr] != "all":
    channels_org = list(filter(lambda channel: channel.type == channelTypeFilter[filtr], guild.channels))
  channels = channels_org[offset*limit:limit+offset*limit]

  builder = InlineKeyboardBuilder()
  builder.row(InlineKeyboardButton(text=f"Фильтр: {emojiForChannelType[channelTypeFilter[filtr]]}", callback_data=GetChannelsCallback(bot_id=bot_id, server_id=guild_id, offset=0, filter=new_filter).pack()))

  for channel in channels:
    builder.row(InlineKeyboardButton(text=f"{emojiForChannelType[channel.type]} | {channel.name}", callback_data=GetChannelCallback(bot_id=bot_id, server_id=guild_id, channel_id=channel.id).pack()))

  builder.row(InlineKeyboardButton(text="⬅️ Предыдущая страница", callback_data=GetChannelsCallback(bot_id=bot_id, server_id=guild_id, offset=offset-1, filter=filtr).pack() if offset > 0 else "none"))
  builder.add(InlineKeyboardButton(text="Следующая страница ➡️", callback_data=GetChannelsCallback(bot_id=bot_id, server_id=guild_id, offset=offset+1, filter=filtr).pack() if offset < (len(channels_org) / limit) - 1 else "none"))
  builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=GetServerCallback(bot_id=bot_id, server_id=guild_id).pack()))

  text = [
    f"<b>Каналы сервера</b> {guild.name}",
    "",
    "<b>Выберите канал ниже</b>"
  ]
  text = "\n".join(text)

  await state.set_state(GetFSM.channel)
  await state.update_data(guild_id=guild_id, bot_id=bot_id, last_message=callback_query.message.message_id)
  await callback_query.message.edit_text(text, reply_markup=builder.as_markup())

class EditRoleCallback(CallbackData, prefix="eR"):
  bot_id: int
  server_id: int
  role_id: int
  action: int

@guilds_router.callback_query(GetRolesCallback.filter())
async def get_roles_callback(callback_query: CallbackQuery, callback_data: GetRolesCallback, state: FSMContext):
  guild_id = callback_data.server_id
  bot_id = callback_data.bot_id
  action = callback_data.action
  role_id = callback_data.role_id

  guild = await get_guild(bot_id, guild_id)
  role = guild.get_role(role_id)

  builder = InlineKeyboardBuilder()

  builder.row(InlineKeyboardButton(text="Создать роль ➕", callback_data="q"))

  if action == 1 or action == 2: # Перемещение ролей
    if not guild.me.guild_permissions.manage_roles:
      await callback_query.answer("У бота нет прав на редактирование ролей")
      return
    
    if guild.self_role.id == role.id:
      await callback_query.answer("Вы не можете переместить роль бота")
      return
    
    if action == 1:
      if guild.self_role.position == role.position+1:
        await callback_query.answer("Вы не можете перемесить эту роль выше роли бота")
        return
      await role.edit(position=role.position+1)
    elif action == 2:
      if role.position == 1:
        await callback_query.answer("Вы не можете перемесить эту роль ниже роли @everyone")
        return
      await role.edit(position=role.position-1)

  roles = guild.roles[::-1]

  for role in roles:

    if role.name != "@everyone":
      builder.row(InlineKeyboardButton(text=f"{role.name}", callback_data=GetRolesCallback(bot_id=bot_id, server_id=guild_id, role_id=role.id if role.id != callback_data.role_id else 0, action=0).pack()))
    else:
      builder.row(InlineKeyboardButton(text=f"{role.name}", callback_data=EditRoleCallback(server_id=guild_id, bot_id=bot_id, role_id=role.id, action=0).pack()))

    if role.id == callback_data.role_id and role.name != "@everyone":
      builder.row(InlineKeyboardButton(text="⬆️ Выше", callback_data=GetRolesCallback(bot_id=bot_id, server_id=guild_id, role_id=role.id, action=1).pack()))
      builder.add(InlineKeyboardButton(text="Подробнее", callback_data=EditRoleCallback(server_id=guild_id, bot_id=bot_id, role_id=role.id, action=0).pack()))
      builder.add(InlineKeyboardButton(text="Ниже ⬇️", callback_data=GetRolesCallback(bot_id=bot_id, server_id=guild_id, role_id=role.id, action=2).pack()))

  builder.row(InlineKeyboardButton(text=f"🔙 Назад", callback_data=GetServerCallback(bot_id=bot_id, server_id=guild_id).pack()))
  
  await callback_query.message.edit_text(f"<b>Роли сервера</b> {guild.name}", reply_markup=builder.as_markup())

@guilds_router.callback_query(GetAuditCallback.filter())
async def get_audit_callback(callback_query: CallbackQuery, callback_data: GetAuditCallback, state: FSMContext):
  bot_id = callback_data.bot_id
  guild_id = callback_data.server_id

  guild = await get_guild(bot_id, guild_id)

  if not guild.me.guild_permissions.view_audit_log:
    await callback_query.answer("У бота нет прав на просмотр журнала аудита")
    return

  audit_logs = guild.audit_logs(limit=20)

  text = [
    f"<b>Логи сервера</b> {guild.name}",
    ""
  ]

  async for log in audit_logs:
    text.append(f"{log.user.name} - {log.action}")

  text = '\n'.join(text)
  builder = InlineKeyboardBuilder()
  builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data=GetServerCallback(bot_id=bot_id, server_id=guild_id).pack()))

  await callback_query.message.edit_text(text, reply_markup=builder.as_markup())