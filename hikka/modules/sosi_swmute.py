# Simple lavHost manager
# Copyright © 2022 https://t.me/nalinor

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# meta developer: @nalinormods - mod by @netuzb

import logging
import re
import time
from typing import List, Tuple

from telethon import TelegramClient
from telethon.hints import Entity
from telethon.tl.custom import Message
from telethon.utils import get_peer_id

from .. import loader, utils
from ..database import Database

logger = logging.getLogger(__name__)


def s2time(string) -> Tuple[int, dict]:
    """Parse time from text `string`"""
    r = {}  # results

    for time_type in ["mon", "w", "d", "h", "m", "s"]:
        try:
            count = int(re.search(rf"(\d+)\s*{time_type}", string)[1])
        except TypeError as e:
            r[time_type] = 0
        else:
            r[time_type] = count

    r["d"] += r["mon"] * 30 + r["w"] * 7
    del r["mon"]
    del r["w"]

    return (r["d"] * 86400 + r["h"] * 3600 + r["m"] * 60 + r["s"]), r


def get_link(user: Entity) -> str:
    """Return permanent link to `user`"""
    return "<a href='tg://user?id={id}'>{name}</a>".format(
        id=user.id,
        name=utils.escape_html(
            user.first_name if hasattr(user, "first_name") else user.title
        ),
    )


def plural_number(n):
    return (
        "one"
        if n % 10 == 1 and n % 100 != 11
        else "few"
        if 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20)
        else "many"
    )


# noinspection PyCallingNonCallable
@loader.tds
class SwmuteMod(loader.Module):
    """Deletes messages from certain users"""

    strings = {
        "name": "Swmute",
        "not_group": "🚫 <b>This command is for groups only</b>",
        "muted": "🔇 <b>Swmuted {user} for {time}</b>",
        "muted_forever": "🔇 <b>Swmuted {user} indefinitely</b>",
        "unmuted": "🔉 <b>Removed swmute from {user}</b>",
        "not_muted": "🚫 <b>This user wasn't muted</b>",
        "invalid_user": "🚫 <b>Provided username/id {entity} is invalid</b>",
        "no_mute_target": "🧐 <b>Whom should I mute?</b>",
        "no_unmute_target": "🧐 <b>Whom should I unmute?</b>",
        "mutes_empty": "😔 <b>There's no mutes in this group</b>",
        "muted_users": "📃 <b>Swmuted users at the moment:</b>\n{names}",
        "cleared": "🧹 <b>Cleared mutes in this chat</b>",
        "cleared_all": "🧹 <b>Cleared all mutes</b>",
        "s_one": "seconds",
        "s_few": "seconds",
        "s_many": "seconds",
        "m_one": "minutes",
        "m_few": "minutes",
        "m_many": "minutes",
        "h_one": "hours",
        "h_few": "hours",
        "h_many": "hours",
        "d_one": "days",
        "d_few": "days",
        "d_many": "days",
    }

    strings_ru = {
        "_cls_doc": "Удаляет сообщения от выбранных пользователей",
        "_cmd_doc_swmute": "<реплай/юзернейм/айди> <время> — Добавить пользователя в список swmute",
        "_cmd_doc_swunmute": "<реплай/юзернейм/айди> — Удалить пользователя из списка swmute",
        "_cmd_doc_swmutelist": "Получить список пользователей в swmute",
        "_cmd_doc_swmuteclear": "<all> — Удалить всех пользователей из списка swmute в этом/всех чатах",
        "not_group": "🚫 <b>Эта команда предназначена только для групп</b>",
        "muted": "🔇 <b>{user} добавлен в список swmute на {time}</b>",
        "muted_forever": "🔇 <b>{user} добавлен в список swmute навсегда</b>",
        "unmuted": "🔉 <b>{user} удалён из списка swmute</b>",
        "not_muted": "🚫 <b>Этот пользователь не был в муте</b>",
        "invalid_user": "🚫 <b>Предоставленный юзернейм/айди {entity} некорректный</b>",
        "no_mute_target": "🧐 <b>Кого я должен замутить?</b>",
        "no_unmute_target": "🧐 <b>Кого я должен размутить?</b>",
        "mutes_empty": "😔 <b>В этой группе никто не в муте</b>",
        "muted_users": "📃 <b>Пользователи в списке swmute:</b>\n{names}",
        "cleared": "🧹 <b>Муты в этой группе очищены</b>",
        "cleared_all": "🧹 <b>Все муты очищены</b>",
        "s_one": "секунда",
        "s_few": "секунды",
        "s_many": "секунд",
        "m_one": "минута",
        "m_few": "минуты",
        "m_many": "минут",
        "h_one": "час",
        "h_few": "часа",
        "h_many": "часов",
        "d_one": "день",
        "d_few": "дня",
        "d_many": "дней",
    }

    async def client_ready(self, client: TelegramClient, db: Database):
        self._db = db

        self._cleanup()

    def format_time(self, time_dict: dict) -> str:
        """Format time from `s2time` to human-readable variant"""
        text = ""

        for time_type, count in time_dict.items():
            if count != 0:
                text += (
                    f"{count} {self.strings(time_type + '_' + plural_number(count))} "
                )

        return text.rstrip()

    def _mute(self, chat_id: int, user_id: int, until_time: int = 0):
        """Add user to mute list"""
        chat_id = str(chat_id)
        user_id = str(user_id)

        mutes = self._db.get("swmute", "mutes")
        mutes.setdefault(chat_id, {})
        mutes[chat_id][user_id] = until_time
        self._db.set("swmute", "mutes", mutes)

        logger.debug(f"Muted user {user_id} in chat {chat_id}")

    def _unmute(self, chat_id: int, user_id: int):
        """Remove user from mute list"""
        chat_id = str(chat_id)
        user_id = str(user_id)

        mutes = self._db.get("swmute", "mutes")
        if chat_id in mutes and user_id in mutes[chat_id]:
            mutes[chat_id].pop(user_id)
        self._db.set("swmute", "mutes", mutes)

        logger.debug(f"Unmuted user {user_id} in chat {chat_id}")

    def _get_mutes(self, chat_id: int) -> List[int]:
        """Get current mutes for specified chat"""
        return [
            int(user_id)
            for user_id, until_time in self._db.get("swmute", "mutes", {})
            .get(str(chat_id), {})
            .items()
            if until_time > time.time() or until_time == 0
        ]

    def _cleanup(self):
        """Clear all expired mutes"""
        mutes = {}

        for chat_id, chat_mutes in self._db.get("swmute", "mutes", {}).items():
            if new_chat_mutes := {
                user_id: until_time
                for user_id, until_time in chat_mutes.items()
                if until_time == 0 or until_time > time.time()
            }:
                mutes[chat_id] = new_chat_mutes

        self._db.set("swmute", "mutes", mutes)

    def _clear_mutes(self, chat_id: int = None):
        if chat_id:
            mutes = self._db.get("swmute", "mutes", {})
            del mutes[str(chat_id)]
            self._db.set("swmute", "mutes", mutes)
        else:
            self._db.set("swmute", "mutes", {})

    async def swmutecmd(self, message: Message):
        """<reply/username/id> <time> — Add user to swmute list"""
        if not message.is_group:
            return await utils.answer(message, self.strings("not_group"))

        args = utils.get_args(message)
        reply = await message.get_reply_message()

        if reply and reply.sender_id:
            user_id = reply.sender_id
            user = await message.client.get_entity(reply.sender_id)
            string_time = " ".join(args) if args else False
        elif args:
            try:
                user = await message.client.get_entity(
                    int(args[0]) if re.fullmatch(r"(-100)?\d+", args[0]) else args[0]
                )
                user_id = get_peer_id(user)
            except ValueError:
                return await utils.answer(message, self.strings("no_mute_target"))
            string_time = " ".join(args[1:]) if len(args) else False
        else:
            return await utils.answer(message, self.strings("no_mute_target"))

        if string_time:
            mute_time, arguments = s2time(" ".join(args))
            if mute_time:
                self._mute(message.chat_id, user_id, int(time.time() + mute_time))
                return await utils.answer(
                    message,
                    self.strings("muted").format(
                        time=self.format_time(arguments), user=get_link(user)
                    ),
                )

        self._mute(message.chat_id, user_id)
        await utils.answer(
            message, self.strings("muted_forever").format(user=get_link(user))
        )

    async def swunmutecmd(self, message: Message):
        """<reply/username/id> — Remove swmute from user"""
        if not message.is_group:
            return await utils.answer(message, self.strings("not_group"))

        args = utils.get_args(message)
        reply = await message.get_reply_message()

        if reply and reply.sender_id:
            user_id = reply.sender_id
            user = await message.client.get_entity(reply.sender_id)
        elif args:
            try:
                user = await message.client.get_entity(
                    int(args[0]) if re.fullmatch(r"(-100)?\d+", args[0]) else args[0]
                )
                user_id = get_peer_id(user)
            except ValueError:
                return await utils.answer(message, self.strings("no_unmute_target"))
        else:
            return await utils.answer(message, self.strings("no_unmute_target"))

        self._unmute(message.chat_id, user_id)
        await utils.answer(message, self.strings("unmuted").format(user=get_link(user)))

    async def swmutelistcmd(self, message: Message):
        """Get list of swmuted users"""
        if not message.is_group:
            return await utils.answer(message, self.strings("not_group"))

        mutes = self._get_mutes(message.chat_id)
        if not mutes:
            return await utils.answer(message, self.strings("mutes_empty"))

        muted_names = []
        for mute in mutes:
            try:
                user = get_link(await message.client.get_entity(mute))
            except ValueError:
                user = ""
            muted_names.append(f"• <i>{user}</i> (<code>{mute}</code>)")

        await utils.answer(
            message, self.strings("muted_users").format(names="\n".join(muted_names))
        )

    async def swmuteclearcmd(self, message: Message):
        """<all> — Clear all swmutes in this chat/in all chats"""
        if "all" in utils.get_args_raw(message):
            self._clear_mutes()
            await utils.answer(message, self.strings("cleared_all"))
        else:
            self._clear_mutes(message.chat_id)
            await utils.answer(message, self.strings("cleared"))

    async def watcher(self, message: Message):
        if (
            isinstance(message, Message)
            and not message.out
            and message.is_group
            and message.sender_id in self._get_mutes(message.chat_id)
        ):
            await message.delete()

            logger.debug(
                f"Deleted message from user {message.sender_id} in chat {message.chat_id}"
            )