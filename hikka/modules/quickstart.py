import logging
import os
from random import choice
from .. import loader, translations
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)
imgs = ["https://i.imgur.com/t0Qjyhc.jpeg"]

TEXT = """<b>Soso</b> top iz vsex topov"""


TEXT_RU = """..."""

if "OKTETO" in os.environ:
    TEXT += "☁️ <b>Your userbot is installed on Okteto</b>. Don't worry, you will get some notifications from @WebpageBot. Do not block him."
    TEXT_RU += "☁️ <b>Твой юзербот установлен на Okteto</b>. Не пугайся, когда будешь получать уведомления от @WebpageBot и не блокируй его."


@loader.tds
class QuickstartMod(loader.Module):
    """Notifies user about userbot installation"""

    strings = {"name": "Quickstart"}

    async def client_ready(self, client, db):
        self._db = db

        mark = self.inline.generate_markup(
            [
                [{"text": "◍ Moderator", "url": "https://t.me/netuzb"}],               
            ],
        )

        await self.inline.bot.send_animation(
            self._tg_id,
            animation=choice(imgs),
            caption=TEXT,
            reply_markup=mark,
        )

        db.set("hikka", "disable_quickstart", True)

    async def quickstart_callback_handler(self, call: InlineCall):
        if not call.data.startswith("hikka_qs_sw_lng_"):
            return

        lang = call.data.split("_")[-1]
        if lang == "ru":
            mark = self.inline.generate_markup(
                [
                    [{"text": "🥷 Чат помощи", "url": "https://t.me/hikka_talks"}],
                    [{"text": "🇬🇧 English", "data": "hikka_qs_sw_lng_en"}],
                ]
            )

            self._db.set(translations.__name__, "lang", "ru")
            self._db.set(translations.__name__, "pack", "ru")
            await self.translator.init()
            await call.answer("🇷🇺 Язык сохранен!")

            await self.inline.bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=TEXT_RU,
                reply_markup=mark,
            )
        elif lang == "en":
            mark = self.inline.generate_markup(
                [
                    [{"text": "🥷 Support chat", "url": "https://t.me/hikka_talks"}],
                    [{"text": "🇷🇺 Русский", "data": "hikka_qs_sw_lng_ru"}],
                ]
            )

            self._db.set(translations.__name__, "lang", "en")
            self._db.set(translations.__name__, "pack", None)
            await self.translator.init()
            await call.answer("🇬🇧 Language saved!")

            await self.inline.bot.edit_message_caption(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                caption=TEXT,
                reply_markup=mark,
            )
