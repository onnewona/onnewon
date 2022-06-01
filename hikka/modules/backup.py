import asyncio
import datetime
import io
import json
import logging
import time

from telethon.tl.types import Message

from .. import loader, utils
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)


@loader.tds
class BackupmodMod(loader.Module):
    """Automatic database backup"""

    strings = {
        "name": "Backup",
        "period": "⌚️ <b>Hewwo! I'm Sosi</b> - your personal backup manager. Please, select the periodicity of automatic database backups",
        "saved": "✅ Backup period saved. You can re-configure it later with .set_backup_period",
        "never": "✅ I will not make automatic backups. You can re-configure it later with .set_backup_period",
        "invalid_args": "🚫 <b>Specify correct backup period in hours, or `0` to disable</b>",
    }

    strings_ru = {
        "period": "⌚️ <b>Приветики! Я Асуна</b> - твой менеджер резервного копирования. Пожалуйста, выбери периодичность резервных копий базы данных Hikka",
        "saved": "✅ Периодичность сохранена! Ее можно изменить с помощью .set_backup_period",
        "never": "✅ Я не буду делать автоматические резервные копии. Можно отменить используя .set_backup_period",
        "invalid_args": "🚫 <b>Укажи правильную периодичность в часах, или `0` для отключения</b>",
    }

    async def client_ready(self, client, db):
        self._db = db
        self._client = client
        if not self.get("period"):
            await self.inline.bot.send_photo(
                self._tg_id,
                photo="https://i.imgur.com/KK0KJqG.jpeg",
                caption=self.strings("period"),
                reply_markup=self.inline.generate_markup(
                    utils.chunks(
                        [
                            {"text": f"🕰 {i} h", "data": f"backup_period/{i}"}
                            for i in {1, 2, 4, 6, 8, 12, 24, 48, 168}
                        ],
                        3,
                    )
                    + [[{"text": "🚫 Never", "data": "backup_period/never"}]]
                ),
            )

        self._backup_channel, is_new = await utils.asset_channel(
            self._client,
            "🌇 SOSI-BACKUPS",
            "🌇 SOSI-BACKUPS - all backups is here",
            silent=True,
            archive=True,
            avatar="https://i.imgur.com/uNXNY7I.jpeg",
            _folder="hikka",
        )

        self.handler.start()

        if not is_new and self.get("nomigrate", False):
            return

        await utils.set_avatar(
            client,
            self._backup_channel,
            "https://i.imgur.com/uNXNY7I.jpeg",
        )

        self.set("nomigrate", True)

    async def backup_period_callback_handler(self, call: InlineCall):
        if not call.data.startswith("backup_period"):
            return

        if call.data == "backup_period/never":
            self.set("period", "disabled")
            await call.answer(self.strings("never"), show_alert=True)

            await self.inline.bot.delete_message(
                call.message.chat.id,
                call.message.message_id,
            )
            return

        period = int(call.data.split("/")[1]) * 60 * 60

        self.set("period", period)
        self.set("last_backup", round(time.time()))

        await call.answer(self.strings("saved"), show_alert=True)

        await self.inline.bot.delete_message(
            call.message.chat.id,
            call.message.message_id,
        )

    async def set_backupcmd(self, message: Message):
        """<time in hours> - Change backup frequency"""
        args = utils.get_args_raw(message)
        if not args or not args.isdigit() or int(args) not in range(200):
            await utils.answer(message, self.strings("invalid_args"))
            return

        if not int(args):
            self.set("period", "disabled")
            await utils.answer(message, f"<b>{self.strings('never')}</b>")
            return

        period = int(args) * 60 * 60
        self.set("period", period)
        self.set("last_backup", round(time.time()))
        await utils.answer(message, f"<b>{self.strings('saved')}</b>")

    @loader.loop(interval=1)
    async def handler(self):
        try:
            if not self.get("period"):
                await asyncio.sleep(3)
                return

            if not self.get("last_backup"):
                self.set("last_backup", round(time.time()))
                await asyncio.sleep(self.get("period"))
                return

            if self.get("period") == "disabled":
                raise loader.StopLoop

            await asyncio.sleep(
                self.get("last_backup") + self.get("period") - time.time()
            )

            backup = io.BytesIO(json.dumps(self._db).encode("utf-8"))
            backup.name = f"hikka-db-backup-{getattr(datetime, 'datetime', datetime).now().strftime('%d-%m-%Y-%H-%M')}.json"

            await self._client.send_file(
                self._backup_channel,
                backup,
            )
            self.set("last_backup", round(time.time()))
        except loader.StopLoop:
            raise
        except Exception:
            logger.exception("HikkaBackup failed")
            await asyncio.sleep(60)
