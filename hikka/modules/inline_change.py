import logging
import re
import string

from telethon.errors.rpcerrorlist import YouBlockedUserError
from telethon.tl.functions.contacts import UnblockRequest
from telethon.tl.types import Message

from .. import loader, utils
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)


@loader.tds
class InlineStuffMod(loader.Module):
    """Bot yaratish yoki botni oʻzgartirish"""

    strings = {
        "name": "BotYaratuvchi",
        "bot_username_invalid": "<b>◍ Belgilangan bot foydalanuvchi nomi yaroqsiz. Quyidagicha tugashi kerak </b><code>...bot</code>",
        "bot_username_occupied": "<b>◍ Bu foydalanuvchi nomi allaqachon band ಥ_ಥ</b>",
        "bot_updated": "<b>◍ Konfiguratsiya muvaffaqiyatli saqlandi. O'zgarishlarni qo'llash uchun userbotni qayta ishga tushiring.</b>",
    }

    async def client_ready(self, client, db):
        self._db = db
        self._client = client
        self._bot_id = (await self.inline.bot.get_me()).id

    async def inline__close(self, call: InlineCall):
        await call.delete()

    async def watcher(self, message: Message):
        if (
            getattr(message, "out", False)
            and getattr(message, "via_bot_id", False)
            and message.via_bot_id == self.inline.bot_id
            and "This message is gonna be deleted..."
            in getattr(message, "raw_text", "")
        ):
            await message.delete()
            return

        if (
            not getattr(message, "out", False)
            or not getattr(message, "via_bot_id", False)
            or message.via_bot_id != self._bot_id
            or "Loading gallery..." not in getattr(message, "raw_text", "")
        ):
            return

        id_ = re.search(r"#id: ([a-zA-Z0-9]+)", message.raw_text).group(1)

        await message.delete()

        m = await message.respond("<b>◍ Galereya ochilishi...</b>")

        await self.inline.gallery(
            message=m,
            next_handler=self.inline._custom_map[id_]["handler"],
            caption=self.inline._custom_map[id_].get("caption", ""),
            force_me=self.inline._custom_map[id_].get("force_me", False),
            disable_security=self.inline._custom_map[id_].get(
                "disable_security", False
            ),
        )

    async def _check_bot(self, username: str) -> bool:
        async with self._client.conversation("@BotFather", exclusive=False) as conv:
            try:
                m = await conv.send_message("/token")
            except YouBlockedUserError:
                await self._client(UnblockRequest(id="@BotFather"))
                m = await conv.send_message("/token")

            r = await conv.get_response()

            await m.delete()
            await r.delete()

            if not hasattr(r, "reply_markup") or not hasattr(r.reply_markup, "rows"):
                return False

            for row in r.reply_markup.rows:
                for button in row.buttons:
                    if username != button.text.strip("@"):
                        continue

                    m = await conv.send_message("/cancel")
                    r = await conv.get_response()

                    await m.delete()
                    await r.delete()

                    return True

    async def change_inlinecmd(self, message: Message):
        """<username> - Inline bot foydalanuvchi nomini o'zgartiring"""
        args = utils.get_args_raw(message).strip("@")
        if (
            not args
            or not args.lower().endswith("bot")
            or len(args) <= 4
            or any(
                litera not in (string.ascii_letters + string.digits + "_")
                for litera in args
            )
        ):
            await utils.answer(message, self.strings("bot_username_invalid"))
            return

        try:
            await self._client.get_entity(f"@{args}")
        except ValueError:
            pass
        else:
            if not await self._check_bot(args):
                await utils.answer(message, self.strings("bot_username_occupied"))
                return

        self._db.set("hikka.inline", "custom_bot", args)
        self._db.set("hikka.inline", "bot_token", None)
        await utils.answer(message, self.strings("bot_updated"))
