#    Friendly Telegram (telegram userbot)
#  import asyncio
import atexit
import logging
import os
import subprocess
import sys
from typing import Union
import time

import git
from git import GitCommandError, Repo
from telethon.tl.functions.messages import (
    GetDialogFiltersRequest,
    UpdateDialogFilterRequest,
)
from telethon.tl.types import DialogFilter, Message

from .. import loader, utils, heroku
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)


@loader.tds
class UpdaterMod(loader.Module):
    """Soso yangilash boʻlimi"""

    strings = {
        "name": "Updater",
        "source": "◍ <b>Manba kodini o'qing:</b> <a href='{}'>bu yerda</a>",
        "restarting_caption": "◍ <b>Qayta ishga tushirilmoqda...</b>",
        "downloading": "◍ <b>Yangilanishlar yuklab olinmoqda...</b>",
        "installing": "◍ <b>Yangilanishlar o'rnatilmoqda...</b>",
        "success": "◍ <b>Qayta ishga tushirish muvaffaqiyatli bajarildi! {}\n◍ Ma'lumot:</b> modullar hali ham yuklanmoqda...\n<b>◍ Daraja:</b> qayta ishga tushirish {} soniya davom etadi.",
        "origin_cfg_doc": "Qayerdan yangilash uchun Git Origin URL kerak.",
        "btn_restart": "◍ restart",
        "btn_update": "◍ yangilash",
        "restart_confirm": "<b>◍ Haqiqatan ham qayta ishga tushirmoqchimisiz?</b>",
        "update_confirm": (
            "◍ <b>Haqiqatan ham yangilashni xohlaysizmi?\n\n"
            '<a href="https://github.com/Netuzb/sosi/commit/{}">{}</a> ⤑ '
            '<a href="https://github.com/Netuzb/sosi/commit/{}">{}</a></b>'
        ),
        "no_update": "◍ <b>Siz eng so'nggi versiyadasiz, baribir yangilanishlarni oʻrnatib olasizmi?</b>",
        "cancel": "◍ Bekor qilish",
        "lavhost_restart": "◍  <b>Your lavHost is restarting...\n&gt;///&lt;</b>",
        "lavhost_update": "◍  <b>Your lavHost is updating...\n&gt;///&lt;</b>",
        "full_success": "◍ <b>Muvaffaqiyatli yakunlandi! {}\n◍ Ma'lumot:</b> toʻliq qayta ishga tushirish {} soniya davom etdi.</code>",
    }

    strings_ru = {
        "source": "◍ <b>Прочтите исходный код:</b> <ahref='eccess'>здесь</a>",
        "restarting_caption": "◍ <b>Перезапуск...</b>",
        "downloading": "◍ <b>Обновления загружаются...</b>",
        "installing": "◍ <b>Устанавливаются обновления...</b>",
        "success": "◍ <b>Перезагрузка успешно завершена! {} \n◍ Информация: </b>модули все еще загружаются... \n<b> ◍ Уровень: </b>перезапуск занимает {} секунд.",
        "origin_cfg_doc": "Где вам нужно обновить URL-адрес Git Origin.",
        "btn_restart": "◍ Рестарт",
        "btn_update": "◍ Обновить",
        "restart_confirm": "<b>◍ Вы действительно хотите перезапустить?</b>",
        "update_confirm": (
            "◍ <b>Вы действительно хотите обновиться?\n\n"
            '<a href="https://github.com/Netuzb/sosi/commit/{}">{}</a> ⤑ '
            '<a href="https://github.com/Netuzb/sosi/commit/{}">{}</a></b>'
        ),
        "no_update": "◍ <b>Вы используете последнюю версию, можете ли вы установить обновления?</b>",
        "cancel": "◍ Отмена",
        "lavhost_restart": "◍  <b>Your lavHost is restarting...\n&gt;///&lt;</b>",
        "lavhost_update": "◍  <b>Your lavHost is updating...\n&gt;///&lt;</b>",
        "full_success": "◍ <b>Успешно завершено! {} \n◍ Информация: </b>полный перезапуск заняла {} секунды </code>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "GIT_ORIGIN_URL",
                "https://github.com/Netuzb/sosi",
                lambda: self.strings("origin_cfg_doc"),
                validator=loader.validators.Link(),
            )
        )

    @loader.owner
    async def restartcmd(self, message: Message):
        """Userbotni qayta ishga tushiradi"""
        try:
            if (
                "--force" in (utils.get_args_raw(message) or "")
                or not self.inline.init_complete
                or not await self.inline.form(
                    message=message,
                    text=self.strings("restart_confirm"),
                    reply_markup=[
                        {
                            "text": self.strings("btn_restart"),
                            "callback": self.inline_restart,
                        },
                        {"text": self.strings("cancel"), "callback": self.inline_close},
                    ],
                )
            ):
                raise
        except Exception:
            await self.restart_common(message)

    async def inline_restart(self, call: InlineCall):
        await self.restart_common(call)

    async def inline_close(self, call: InlineCall):
        await call.delete()

    async def process_restart_message(self, msg_obj: Union[InlineCall, Message]):
        self.set(
            "selfupdatemsg",
            msg_obj.inline_message_id
            if hasattr(msg_obj, "inline_message_id")
            else f"{utils.get_chat_id(msg_obj)}:{msg_obj.id}",
        )

    async def restart_common(self, msg_obj: Union[InlineCall, Message]):
        if (
            hasattr(msg_obj, "form")
            and isinstance(msg_obj.form, dict)
            and "uid" in msg_obj.form
            and msg_obj.form["uid"] in self.inline._units
            and "message" in self.inline._units[msg_obj.form["uid"]]
        ):
            message = self.inline._units[msg_obj.form["uid"]]["message"]
        else:
            message = msg_obj

        msg_obj = await utils.answer(
            msg_obj,
            self.strings(
                "restarting_caption"
                if "LAVHOST" not in os.environ
                else "lavhost_restart"
            ),
        )

        await self.process_restart_message(msg_obj)

        self.set("restart_ts", time.time())

        if "LAVHOST" in os.environ:
            os.system("lavhost restart")
            return

        if "DYNO" in os.environ:
            app = heroku.get_app(os.environ["heroku_api_token"])[0]
            app.restart()
            return

        atexit.register(restart, *sys.argv[1:])
        handler = logging.getLogger().handlers[0]
        handler.setLevel(logging.CRITICAL)
        for client in self.allclients:
            # Terminate main loop of all running clients
            # Won't work if not all clients are ready
            if client is not message.client:
                await client.disconnect()

        await message.client.disconnect()

    async def download_common(self):
        try:
            repo = Repo(os.path.dirname(utils.get_base_dir()))
            origin = repo.remote("origin")
            r = origin.pull()
            new_commit = repo.head.commit
            for info in r:
                if info.old_commit:
                    for d in new_commit.diff(info.old_commit):
                        if d.b_path == "requirements.txt":
                            return True
            return False
        except git.exc.InvalidGitRepositoryError:
            repo = Repo.init(os.path.dirname(utils.get_base_dir()))
            origin = repo.create_remote("origin", self.config["GIT_ORIGIN_URL"])
            origin.fetch()
            repo.create_head("master", origin.refs.master)
            repo.heads.master.set_tracking_branch(origin.refs.master)
            repo.heads.master.checkout(True)
            return False

    @staticmethod
    def req_common():
        # Now we have downloaded new code, install requirements
        logger.debug("Installing new requirements...")
        try:
            subprocess.run(  # skipcq: PYL-W1510
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    os.path.join(
                        os.path.dirname(utils.get_base_dir()),
                        "requirements.txt",
                    ),
                    "--user",
                ]
            )

        except subprocess.CalledProcessError:
            logger.exception("Req install failed")

    @loader.owner
    async def updatecmd(self, message: Message):
        """Downloads userbot updates"""
        try:
            current = utils.get_git_hash()
            upcoming = next(
                git.Repo().iter_commits("origin/master", max_count=1)
            ).hexsha
            if (
                "--force" in (utils.get_args_raw(message) or "")
                or not self.inline.init_complete
                or not await self.inline.form(
                    message=message,
                    text=self.strings("update_confirm").format(
                        current,
                        current[:8],
                        upcoming,
                        upcoming[:8],
                    )
                    if upcoming != current
                    else self.strings("no_update"),
                    reply_markup=[
                        {
                            "text": self.strings("btn_update"),
                            "callback": self.inline_update,
                        },
                        {"text": self.strings("cancel"), "callback": self.inline_close},
                    ],
                )
            ):
                raise
        except Exception:
            await self.inline_update(message)

    async def inline_update(
        self,
        msg_obj: Union[InlineCall, Message],
        hard: bool = False,
    ):
        # We don't really care about asyncio at this point, as we are shutting down
        if hard:
            os.system(f"cd {utils.get_base_dir()} && cd .. && git reset --hard HEAD")  # fmt: skip

        try:
            if "LAVHOST" in os.environ:
                msg_obj = await utils.answer(msg_obj, self.strings("lavhost_update"))
                await self.process_restart_message(msg_obj)
                os.system("lavhost update")
                return

            try:
                msg_obj = await utils.answer(msg_obj, self.strings("downloading"))
            except Exception:
                pass

            req_update = await self.download_common()

            try:
                msg_obj = await utils.answer(msg_obj, self.strings("installing"))
            except Exception:
                pass

            if req_update:
                self.req_common()

            await self.restart_common(msg_obj)
        except GitCommandError:
            if not hard:
                await self.inline_update(msg_obj, True)
                return

            logger.critical("Got update loop. Update manually via .terminal")
            return

    @loader.unrestricted
    async def sourcecmd(self, message: Message):
        """Links the source code of this project"""
        await utils.answer(
            message,
            self.strings("source").format(self.config["GIT_ORIGIN_URL"]),
        )

    async def client_ready(self, client, db):
        self._db = db
        self._client = client

        if self.get("selfupdatemsg") is not None:
            try:
                await self.update_complete(client)
            except Exception:
                logger.exception("Failed to complete update!")

        if self.get("do_not_create", False):
            return

        folders = await self._client(GetDialogFiltersRequest())

        if any(folder.title == "bt." for folder in folders):
            return

        try:
            folder_id = (
                max(
                    folders,
                    key=lambda x: x.id,
                ).id
                + 1
            )
        except ValueError:
            folder_id = 2

        try:
            await self._client(
                UpdateDialogFilterRequest(
                    folder_id,
                    DialogFilter(
                        folder_id,
                        title="bt.",
                        pinned_peers=(
                            [
                                await self._client.get_input_entity(
                                    self._client.loader.inline.bot_id
                                )
                            ]
                            if self._client.loader.inline.init_complete
                            else []
                        ),
                        include_peers=[
                            await self._client.get_input_entity(dialog.entity)
                            async for dialog in self._client.iter_dialogs(
                                None,
                                ignore_migrated=True,
                            )
                            if dialog.name
                            in {
                                "hikka-logs",
                                "hikka-onload",
                                "hikka-assets",
                                "hikka-backups",
                                "hikka-acc-switcher",
                                "silent-tags",
                            }
                            and dialog.is_channel
                            and (
                                dialog.entity.participants_count == 1
                                or dialog.entity.participants_count == 2
                                and dialog.name in {"hikka-logs", "silent-tags"}
                            )
                            or (
                                self._client.loader.inline.init_complete
                                and dialog.entity.id
                                == self._client.loader.inline.bot_id
                            )
                            or dialog.entity.id
                            in [
                                1554874075,
                                1697279580,
                                1679998924,
                            ]  # official hikka chats
                        ],
                        emoticon="😺",
                        exclude_peers=[],
                        contacts=False,
                        non_contacts=False,
                        groups=False,
                        broadcasts=False,
                        bots=False,
                        exclude_muted=False,
                        exclude_read=False,
                        exclude_archived=False,
                    ),
                )
            )
        except Exception:
            logger.critical(
                "Can't create Hikka folder. Possible reasons are:\n"
                "- User reached the limit of folders in Telegram\n"
                "- User got floodwait\n"
                "Ignoring error and adding folder addition to ignore list"
            )

        self.set("do_not_create", True)

    async def update_complete(self, client: "TelegramClient"):  # type: ignore
        logger.debug("Self update successful! Edit message")
        start = self.get("restart_ts")
        try:
            took = round(time.time() - start)
        except Exception:
            took = "n/a"

        msg = self.strings("success").format(utils.ascii_face(), took)
        ms = self.get("selfupdatemsg")

        if ":" in str(ms):
            chat_id, message_id = ms.split(":")
            chat_id, message_id = int(chat_id), int(message_id)
            await self._client.edit_message(chat_id, message_id, msg)
            return

        await self.inline.bot.edit_message_text(
            inline_message_id=ms,
            text=msg,
        )

    async def full_restart_complete(self):

        start = self.get("restart_ts")
        try:
            took = round(time.time() - start)
        except Exception:
            took = "n/a"

        self.set("restart_ts", None)
        ms = self.get("selfupdatemsg")

        msg = self.strings("full_success").format(utils.ascii_face(), took)

        if ms is None:
            return

        self.set("selfupdatemsg", None)

        if ":" in str(ms):
            chat_id, message_id = ms.split(":")
            chat_id, message_id = int(chat_id), int(message_id)
            await self._client.edit_message(chat_id, message_id, msg)
            await asyncio.sleep(60)
            await self._client.delete_messages(chat_id, message_id)
            return

        await self.inline.bot.edit_message_text(
            inline_message_id=ms,
            text=msg,
        )


def restart(*argv):
    os.execl(
        sys.executable,
        sys.executable,
        "-m",
        os.path.relpath(utils.get_base_dir()),
        *argv,
    )
