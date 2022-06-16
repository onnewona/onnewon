import itertools
import logging
from traceback import format_exc
from types import ModuleType
import telethon
from meval import meval
from telethon.errors.rpcerrorlist import MessageIdInvalidError
from telethon.tl.types import Message
from .. import loader, main, utils
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)


class FakeDbException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class FakeDb:
    def __getattr__(self, *args, **kwargs):
        raise FakeDbException("Database read-write permission required")


@loader.tds
class PythonMod(loader.Module):
    """Evaluates python code"""

    strings = {
        "name": "Python",
        "eval": "<b>◍ python:</b>\n\n<code>{}</code>\n<b>◍ natija:</b>\n\n<code>{}</code>",
        "err": "<b>◍ python:</b>\n\n<code>{}</code>\n\n<b>◍ noma`lum:</b>\n\n<code>{}</code>",
        "db_permission": "◍ db.set unknown",
    }

    async def client_ready(self, client, db):
        self._client = client
        self._db = db
        self._phone = (await client.get_me()).phone

    @loader.owner
    async def evalcmd(self, message: Message):
        """Alias for .e command"""
        await self.ecmd(message)

    async def inline__close(self, call: InlineCall):
        await call.answer("Operation cancelled")
        await call.delete()

    async def inline__allow(self, call: InlineCall):
        await call.answer("Now you can access db through .e command", show_alert=True)
        self._db.set(main.__name__, "enable_db_eval", True)
        await call.delete()

    @loader.owner
    async def ecmd(self, message: Message):
        """Evaluates python code"""
        ret = self.strings("eval")
        try:
            it = await meval(
                utils.get_args_raw(message),
                globals(),
                **await self.getattrs(message),
            )
        except FakeDbException:
            await self.inline.form(
                self.strings("db_permission"),
                message=message,
                reply_markup=[
                    [
                        {
                            "text": "✅ Allow",
                            "callback": self.inline__allow,
                        },
                        {"text": "🚫 Cancel", "callback": self.inline__close},
                    ]
                ],
            )
            return
        except Exception:
            exc = format_exc().replace(self._phone, "📵")
            await utils.answer(
                message,
                self.strings("err").format(
                    utils.escape_html(utils.get_args_raw(message)),
                    utils.escape_html(exc),
                ),
            )

            return
        ret = ret.format(
            utils.escape_html(utils.get_args_raw(message)),
            utils.escape_html(it),
        )
        ret = ret.replace(str(self._phone), "📵")
        try:
            await utils.answer(message, ret)
        except MessageIdInvalidError:
            pass

    async def getattrs(self, message):
        reply = await message.get_reply_message()
        return {
            **{
                "message": message,
                "client": self._client,
                "reply": reply,
                "r": reply,
                **self.get_sub(telethon.tl.types),
                **self.get_sub(telethon.tl.functions),
                "event": message,
                "chat": message.to_id,
                "telethon": telethon,
                "utils": utils,
                "main": main,
                "loader": loader,
                "f": telethon.tl.functions,
                "c": self._client,
                "m": message,
                "lookup": self.lookup,
                "self": self,
            },
            **(
                {
                    "db": self._db,
                }
                if self._db.get(main.__name__, "enable_db_eval", False)
                else {
                    "db": FakeDb(),
                }
            ),
        }

    def get_sub(self, it, _depth: int = 1) -> dict:
        """Get all callable capitalised objects in an object recursively, ignoring _*"""
        return {
            **dict(
                filter(
                    lambda x: x[0][0] != "_"
                    and x[0][0].upper() == x[0][0]
                    and callable(x[1]),
                    it.__dict__.items(),
                )
            ),
            **dict(
                itertools.chain.from_iterable(
                    [
                        self.get_sub(y[1], _depth + 1).items()
                        for y in filter(
                            lambda x: x[0][0] != "_"
                            and isinstance(x[1], ModuleType)
                            and x[1] != it
                            and x[1].__package__.rsplit(".", _depth)[0]
                            == "telethon.tl",
                            it.__dict__.items(),
                        )
                    ]
                )
            ),
        }
