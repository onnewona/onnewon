import inspect
import logging
import os
import time
from io import BytesIO
from typing import Union
from telethon.tl.functions.channels import EditAdminRequest, InviteToChannelRequest
from telethon.tl.types import ChatAdminRights, Message
from .. import loader, main, utils
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)
DEBUG_MODS_DIR = os.path.join(utils.get_base_dir(), "debug_modules")

if not os.path.isdir(DEBUG_MODS_DIR):
    os.mkdir(DEBUG_MODS_DIR, mode=0o755)

for mod in os.scandir(DEBUG_MODS_DIR):
    os.remove(mod.path)


@loader.tds
class TestMod(loader.Module):
    """Perform operations based on userbot self-testing"""

    _memory = {}

    strings = {
        "name": "Tester",
        "set_loglevel": "🚫 <b>Please specify verbosity as an integer or string</b>",
        "no_logs": "<b>◍ Sizda batafsil ma'lumot bo'yicha hech qanday jurnal yo'q {}.</b>",
        "logs_filename": "sosi-logs.html",
        "logs_caption": "<b>◍ Sosi batafsil xatoliklar </b><code>{}</code>\n◍ <b>Sosi versiya: {}.{}.{}</b>\n<a href='{}'></a>",
        "suspend_invalid_time": "🚫 <b>Invalid time to suspend</b>",
        "suspended": "<b>◍ Bot suspended for</b> <code>{}</code> <b>seconds</b>",
        "results_ping": "(◕ᴗ◕✿) <b>Response speed:</b> <code>{} ms</code>\n(◍•ᴗ•◍) <b>Updated time:</b> <code>{}</code>",
        "confidential": "⚠️ <b>Log level </b><code>{}</code><b> may reveal your confidential info, be careful</b>",
        "confidential_text": (
            "⚠️ <b>Log level </b><code>{0}</code><b> may reveal your confidential info, "
            "be careful</b>\n<b>Type </b><code>.logs {0} force_insecure</code><b> "
            "to ignore this warning</b>"
        ),
        "choose_loglevel": "◍ <b>Jurnal darajasi</b>ni tanlang",
        "database_unlocked": "◍ JB bahosi ochildi",
        "database_locked": "◍ JB baholash bloklangan",
        "bad_module": "<b>◍ Modul topilmadi</b>",
        "debugging_enabled": "<b>◍ Modul uchun nosozliklarni tuzatish rejimi yoqilgan </b><code>{0}</code>\n<i>Go to directory named `debug_modules`, edit file named `{0}.py` and see changes in real time</i>",
        "debugging_disabled": "<b>◍ Nosozliklarni tuzatish o'chirilgan</b>",
    }

    @staticmethod
    async def dumpcmd(message: Message):
        """Use in reply to get a dump of a message"""
        if not message.is_reply:
            return

        await utils.answer(
            message,
            "<code>"
            + utils.escape_html((await message.get_reply_message()).stringify())
            + "</code>",
        )

    @staticmethod
    async def cancel(call: InlineCall):
        await call.delete()

    @loader.loop(interval=1, autostart=True)
    async def watchdog(self):
        try:
            for module in os.scandir(DEBUG_MODS_DIR):
                last_modified = os.stat(module.path).st_mtime
                cls_ = module.path.split("/")[-1].split(".py")[0]

                if cls_ not in self._memory:
                    self._memory[cls_] = last_modified
                    continue

                if self._memory[cls_] == last_modified:
                    continue

                self._memory[cls_] = last_modified
                logger.debug(f"Reloading debug module {cls_}")
                with open(module.path, "r") as f:
                    try:
                        await next(
                            module
                            for module in self.allmodules.modules
                            if module.__class__.__name__ == "LoaderMod"
                        ).load_module(
                            f.read(),
                            None,
                            save_fs=False,
                        )
                    except Exception:
                        logger.exception("Failed to reload module in watchdog")
        except Exception:
            logger.exception("Failed debugging watchdog")
            return

    async def debugmodcmd(self, message: Message):
        """[module] - For developers: Open module for debugging
        You will be able to track changes in real-time"""
        args = utils.get_args_raw(message)
        instance = None
        for module in self.allmodules.modules:
            if (
                module.__class__.__name__.lower() == args.lower()
                or module.strings["name"].lower() == args.lower()
            ):
                if os.path.isfile(
                    os.path.join(
                        DEBUG_MODS_DIR,
                        f"{module.__class__.__name__}.py",
                    )
                ):
                    os.remove(
                        os.path.join(
                            DEBUG_MODS_DIR,
                            f"{module.__class__.__name__}.py",
                        )
                    )

                    try:
                        delattr(module, "hikka_debug")
                    except AttributeError:
                        pass

                    await utils.answer(message, self.strings("debugging_disabled"))
                    return

                module.hikka_debug = True
                instance = module
                break

        if not instance:
            await utils.answer(message, self.strings("bad_module"))
            return

        with open(
            os.path.join(
                DEBUG_MODS_DIR,
                f"{instance.__class__.__name__}.py",
            ),
            "wb",
        ) as f:
            f.write(inspect.getmodule(instance).__loader__.data)

        await utils.answer(
            message,
            self.strings("debugging_enabled").format(instance.__class__.__name__),
        )

    async def logscmd(
        self,
        message: Union[Message, InlineCall],
        force: bool = False,
        lvl: Union[int, None] = None,
    ):
        """<level> - Dumps logs. Loglevels below WARNING may contain personal info."""
        if not isinstance(lvl, int):
            args = utils.get_args_raw(message)
            try:
                try:
                    lvl = int(args.split()[0])
                except ValueError:
                    lvl = getattr(logging, args.split()[0].upper(), None)
            except IndexError:
                lvl = None

        if not isinstance(lvl, int):
            try:
                if not self.inline.init_complete or not await self.inline.form(
                    text=self.strings("choose_loglevel"),
                    reply_markup=[
                        [
                            {
                                "text": "◍ Tanqidiy",
                                "callback": self.logscmd,
                                "args": (False, 50),
                            },
                            {
                                "text": "◍ Xato",
                                "callback": self.logscmd,
                                "args": (False, 40),
                            },
                        ],
                        [
                            {
                                "text": "◍ Ogohlantirish",
                                "callback": self.logscmd,
                                "args": (False, 30),
                            },
                            {
                                "text": "◍ Ma'lumot",
                                "callback": self.logscmd,
                                "args": (False, 20),
                            },
                        ],
                        [
                            {
                                "text": "◍ Nosozliklarni tuzatish",
                                "callback": self.logscmd,
                                "args": (False, 10),
                            },
                            {
                                "text": "◍ Hammasi",
                                "callback": self.logscmd,
                                "args": (False, 0),
                            },
                        ],
                        [{"text": "× Bekor qilish", "callback": self.cancel}],
                    ],
                    message=message,
                ):
                    raise
            except Exception:
                await utils.answer(message, self.strings("set_loglevel"))

            return

        logs = "\n\n".join(
            [
                ("\n".join(handler.dumps(lvl)))
                for handler in logging.getLogger().handlers
            ]
        )

        named_lvl = (
            lvl
            if lvl not in logging._levelToName
            else logging._levelToName[lvl]  # skipcq: PYL-W0212
        )

        if (
            lvl < logging.WARNING
            and not force
            and (
                not isinstance(message, Message)
                or "force_insecure" not in message.raw_text.lower()
            )
        ):
            try:
                if not self.inline.init_complete:
                    raise

                cfg = {
                    "text": self.strings("confidential").format(named_lvl),
                    "reply_markup": [
                        {
                            "text": "◍ Baribir yuboring",
                            "callback": self.logscmd,
                            "args": [True, lvl],
                        },
                        {"text": "× Bekor qilish", "callback": self.cancel},
                    ],
                }
                if isinstance(message, Message):
                    if not await self.inline.form(**cfg, message=message):
                        raise
                else:
                    await message.edit(**cfg)
            except Exception:
                await utils.answer(
                    message,
                    self.strings("confidential_text").format(named_lvl),
                )

            return

        if len(logs) <= 2:
            if isinstance(message, Message):
                await utils.answer(message, self.strings("no_logs").format(named_lvl))
            else:
                await message.edit(self.strings("no_logs").format(named_lvl))
                await message.unload()

            return

        if btoken := self._db.get("hikka.inline", "bot_token", False):
            logs = logs.replace(
                btoken,
                f'{btoken.split(":")[0]}:***************************',
            )

        if hikka_token := self._db.get("HikkaDL", "token", False):
            logs = logs.replace(
                hikka_token,
                f'{hikka_token.split("_")[0]}_********************************',
            )

        if hikka_token := self._db.get("Kirito", "token", False):
            logs = logs.replace(
                hikka_token,
                f'{hikka_token.split("_")[0]}_********************************',
            )

        logs = BytesIO(logs.encode("utf-16"))
        logs.name = self.strings("logs_filename")

        ghash = utils.get_git_hash()

        other = (
            *main.__version__,
            f' <i><a href="https://github.com/hikariatama/Hikka/commit/{ghash}">({ghash[:8]})</a></i>'
            if ghash
            else "",
            utils.formatted_uptime(),
            utils.get_named_platform(),
            self.strings(
                f"database_{'un' if self._db.get(main.__name__, 'enable_db_eval', False) else ''}locked"
            ),
            "✅" if self._db.get(main.__name__, "no_nickname", False) else "🚫",
            "✅" if self._db.get(main.__name__, "grep", False) else "🚫",
            "✅" if self._db.get(main.__name__, "inlinelogs", False) else "🚫",
        )


        if getattr(message, "out", True):
            await message.delete()

        if isinstance(message, Message):
            await utils.answer(
                message,
                logs,
                caption=self.strings("logs_caption").format(named_lvl, *other),
            )
        else:
            await self._client.send_file(
                message.form["chat"],
                logs,
                caption=self.strings("logs_caption").format(named_lvl, *other),
            )

    @loader.owner
    async def suspendcmd(self, message: Message):
        """<time> - Suspends the bot for N seconds"""
        try:
            time_sleep = float(utils.get_args_raw(message))
            await utils.answer(
                message,
                self.strings("suspended").format(time_sleep),
            )
            time.sleep(time_sleep)
        except ValueError:
            await utils.answer(message, self.strings("suspend_invalid_time"))

    async def pingcmd(self, message: Message):
        """Test your userbot ping"""
        start = time.perf_counter_ns()
        message = await utils.answer(message, "<code>(◕ᴗ◕✿) wait...</code>")
        await utils.answer(
            message,
            self.strings("results_ping").format(
                round((time.perf_counter_ns() - start) / 10**6, 3),
                utils.formatted_uptime(),
            ),
        )

    async def client_ready(self, client, db):
        self._client = client
        self._db = db

        chat, is_new = await utils.asset_channel(
            self._client,
            "🌇 SOSI-LOGS",
            "🌇 SOSI-LOGS - All logs is here",
            silent=True,
            avatar="https://i.imgur.com/JmwwMM0.jpeg",
        )

        self._logchat = int(f"-100{chat.id}")

        if not is_new and any(
            participant.id == self.inline.bot_id
            for participant in (await self._client.get_participants(chat, limit=3))
        ):
            logging.getLogger().handlers[0].install_tg_log(self)
            logger.debug(f"Bot logging installed for {self._logchat}")
            return

        logger.debug("New logging chat created, init setup...")

        try:
            await self._client(InviteToChannelRequest(chat, [self.inline.bot_username]))
        except Exception:
            logger.warning("Unable to invite logger to chat")

        try:
            await self._client(
                EditAdminRequest(
                    channel=chat,
                    user_id=self.inline.bot_username,
                    admin_rights=ChatAdminRights(ban_users=True),
                    rank="Logger",
                )
            )
        except Exception:
            pass

        logging.getLogger().handlers[0].install_tg_log(self)
        logger.debug(f"Bot logging installed for {self._logchat}")
