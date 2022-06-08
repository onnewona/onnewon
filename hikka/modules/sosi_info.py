# ▀█▀ █▀▀ █▀▄▀█ █░█ █▀█
# ░█░ ██▄ █░▀░█ █▄█ █▀▄
# ═══════════════════════
# █▀▀ █▀█ █▄▀ █ █▄░█ █▀█ █░█
# ██▄ █▀▄ █░█ █ █░▀█ █▄█ ▀▄▀
# ═════════════════════════════
# meta developer: @netuzb
# meta channel: @umodules

import logging

import git
from telethon.tl.types import Message
from telethon.utils import get_display_name

from .. import loader, main, utils
from ..inline.types import InlineQuery

logger = logging.getLogger(__name__)


@loader.tds
class InfomodMod(loader.Module):
    """Userbot ma'lumotlarini ko'rsatish"""

    strings = {
        "name": "Info",
        "owner": "Boshqaruvchi",
        "version": "Sosi-versiyasi",
        "_cfg_cst_msg": "Custom message for info. May contain {me}, {version}, {build}, {prefix}, {platform} keywords",
        "_cfg_cst_btn": "Custom button for info. Leave empty to remove button",
        "_cfg_banner": "Set `True` in order to disable an image banner",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "custom_message",
                doc=lambda: self.strings("_cfg_cst_msg"),
            ),
            loader.ConfigValue(
                "custom_button6",
                ["Sosi-xususiy-chat (◕ᴗ◕✿)", "https://t.me/+5o1a-UjPfCZhNmE5"],
                lambda: self.strings("_cfg_cst_btn"),
                validator=loader.validators.Series(fixed_len=2),
            ),         
            loader.ConfigValue(
                "disable_banner",
                False,
                lambda: self.strings("_cfg_banner"),
                validator=loader.validators.Boolean(),
            ),
        )

    async def client_ready(self, client, db):
        self._db = db
        self._client = client
        self._me = await client.get_me()

    def _render_info(self) -> str:
        ver = utils.get_git_hash() or "Unknown"

        try:
            repo = git.Repo()
            diff = repo.git.log(["HEAD..origin/master", "--oneline"])
            upd = (
                self.strings("update_required") if diff else self.strings("up-to-date")
            )
        except Exception:
            upd = ""

        me = f'<code><a href="tg://user?id={self._me.id}">{utils.escape_html(get_display_name(self._me))}</a></code>'
        version = f'<i>{".".join(list(map(str, list(main.__version__))))}</i>'
        build = f'<a href="https://github.com/Netuzb/sosi/commit/{ver}">#{ver[:8]}</a>'  # fmt: skip
        prefix = f"•<code>{utils.escape_html(self.get_prefix())}</code>•"
        platform = utils.get_named_platform()

        return (
            "<b>Sosi</b>\n"
            + self.config["custom_message"].format(
                me=me,
                version=version,
                build=build,
                prefix=prefix,
                platform=platform,
            )
            if self.config["custom_message"] and self.config["custom_message"] != "no"
            else (
                "<b>◍ Sosi-Userbot (◕ᴗ◕✿) sosi</b>\n"
                f'<b>◍ {self.strings("owner")}:</b> <a href="tg://user?id={self._me.id}">bu yerda</a>\n'
                f"<b>◍ {self.strings('version')}:</b> <code>{version}</code> <a href='{build}'></a>\n"
                f"\n◍ ╔═══╦═══╦═══╦══╗"
                f"\n◍ ║╔═╗║╔═╗║╔═╗╠╣╠╝"
                f"\n◍ ║╚══╣║─║║╚══╗║║   ╔╗──╔╗"
                f"\n◍ ╚══╗║║─║╠══╗║║║   ║╚╦═╣╚╗"
                f"\n◍ ║╚═╝║╚═╝║╚═╝╠╣╠╗║╬║╬║╔╣"
                f"\n◍ ╚═══╩═══╩═══╩══╝╚═╩═╩═╝"
                f"\n\n<b>◍ <u>Eynshteyn</u> teoriyasi (ʘᴗʘ✿):</b> Statistik ma’lumotlarga  koʻra, eng xavfli odamlar lichkadagi yozishmalarni skrinshot qilib oladiganlari ekan."
            )
        )

    def _get_mark(self):
        return (
            None
            if not self.config["custom_button6"]
            else [
            {"text": self.config["custom_button6"][0],
             "url": self.config["custom_button6"][1],
            },            
          ]
        )

    @loader.inline_everyone
    async def info_inline_handler(self, query: InlineQuery) -> dict:
        """Send userbot info"""

        return {
            "title": self.strings("send_info"),
            "description": self.strings("description"),
            "message": self._render_info(),
            "thumb": "https://i.imgur.com/sYULuO1.jpeg",
            "reply_markup": self._get_mark(),
        }

    @loader.unrestricted
    async def infocmd(self, message: Message):
        """Send userbot info"""
        await self.inline.form(
            message=message,
            text=self._render_info(),
            reply_markup=self._get_mark(),
            **(
                {"photo": "https://i.imgur.com/sYULuO1.jpeg"}
                if not self.config["disable_banner"]
                else {}
            ),
        ) 

#949493939393949494994
