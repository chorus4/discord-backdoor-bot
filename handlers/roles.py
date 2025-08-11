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
from discord import Permissions
import asyncio

import ds
from ds.guilds import get_guild, edit_role
import db
from db.models.dsBots import DsBot
from handlers.guilds import EditRoleCallback, GetRolesCallback, get_roles_callback

roles_router = Router()

class EditRolePermissionsCallback(CallbackData, prefix="eRP"):
  bot_id: int
  perm: str

class DeleteRoleCallback(CallbackData, prefix="dR"):
  bot_id: int
  perm: str

@roles_router.callback_query(EditRoleCallback.filter())
async def edit_role_callback(callback_query: CallbackQuery, callback_data: EditRoleCallback, state: FSMContext):
  guild_id = callback_data.server_id
  bot_id = callback_data.bot_id
  role_id = callback_data.role_id
  action = callback_data.action

  await state.update_data(guild_id=guild_id, role_id=role_id)

  guild = await get_guild(bot_id, guild_id)
  role = guild.get_role(role_id)

  builder = InlineKeyboardBuilder()

  if action == 1:
    await role.edit(hoist=not role.hoist)

  builder.row(InlineKeyboardButton(text="Редактировать разрешения ✏️", callback_data=EditRolePermissionsCallback(bot_id=bot_id, perm="").pack()))
  # builder.row(InlineKeyboardButton(text="Изменить цвет ⚪️", callback_data="В"))
  builder.row(InlineKeyboardButton(text=f"Показывать людей с ролью отдельно: {"Да" if role.hoist else "Нет"}", callback_data=EditRoleCallback(server_id=guild_id, bot_id=bot_id, role_id=role.id, action=1).pack()))
  builder.row(InlineKeyboardButton(text="Удалить роль ❌", callback_data="В"))
  builder.row(InlineKeyboardButton(text=f"🔙 Назад", callback_data=GetRolesCallback(bot_id=bot_id, server_id=guild_id, role_id=role.id, action=0).pack()))

  text = [
    f"<b>Подробности роли</b> {role.name} <b>на сервере</b> {guild.name}"
  ]
  text = '\n'.join(text)

  await callback_query.message.edit_text(text, reply_markup=builder.as_markup())


@roles_router.callback_query(EditRolePermissionsCallback.filter())
async def edit_role_permissions_callback(callback_query: CallbackQuery, callback_data: EditRolePermissionsCallback, state: FSMContext):
  state_data = await state.get_data()
  guild_id = state_data["guild_id"]
  bot_id = callback_data.bot_id
  role_id = state_data["role_id"]
  permx = callback_data.perm

  guild = await get_guild(bot_id, guild_id)
  role = guild.get_role(role_id)
  old_perms = role.permissions

  builder = InlineKeyboardBuilder()

  perms_list = {
    "view_channel": "Просматривать каналы",
    "manage_channels": "Управлять каналами",
    "manage_roles": "Управлять ролями",
    "view_audit_log": "Просматривать журнал аудита",
    "manage_webhooks": "Управлять вебхуками",
    "manage_guild": "Управлять сервером",
    "create_instant_invite": "Создание приглашения",
    "change_nickname": "Изменить никнейм",
    "manage_nicknames": "Управлять никнеймами",
    "administrator": "Администратор",
  }

  if permx != "":
    kw = {permx: not getattr(old_perms, permx)}
    old_perms.update(**kw)
    await role.edit(permissions=old_perms)

  for perm in perms_list:
    builder.row(InlineKeyboardButton(text=f"{perms_list[perm]}:  {"✅" if getattr(old_perms, perm) else "❌"}", callback_data=EditRolePermissionsCallback(bot_id=bot_id, perm=perm).pack()))

  builder.row(InlineKeyboardButton(text=f"🔙 Назад", callback_data=EditRoleCallback(bot_id=bot_id, server_id=guild_id, role_id=role.id, action=0).pack()))

  await callback_query.message.edit_text(f"<b>Права роли</b> {role.name}", reply_markup=builder.as_markup())