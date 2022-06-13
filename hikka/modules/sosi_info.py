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
        "version": "Soso-versiyasi",
        "_cfg_cst_msg": "Ma'lumot uchun maxsus xabar. O'z ichiga olishi mumkin {me}, {version}, {build}, {prefix}, {platform}",
        "_cfg_cst_btn": "Ma'lumot uchun maxsus tugma. O'chirish uchun tugmani bo'sh qoldiring",
        "_cfg_banner": "Rasm bannerini oʻchirish uchun “True” ni oʻrnating",
    }

    strings_cn = {
        "owner": "經理",
        "version": "Soso-版本",
        "_cfg_cst_msg": "信息的特殊消息。可能包括 {me}, {version}, {build}, {prefix}, {platform}",
        "_cfg_cst_btn": "信息的特殊按鈕。將按鈕留空以將其關閉",
        "_cfg_banner": "設置 True 以刪除圖像橫幅",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "custom_message",
                doc=lambda: self.strings("_cfg_cst_msg"),
            ),
            loader.ConfigValue(
                "custom_button10",
                ["◍ Soso-xususiy-chat", "https://t.me/+5o1a-UjPfCZhNmE5"],
                lambda: self.strings("_cfg_cst_btn"),
                validator=loader.validators.Series(fixed_len=2),
            ),         
            loader.ConfigValue(
                "custom_button11",
                ["◍ Soso-yangilash", "http://t.me/share/url?url=.update --force"],
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
            ""
            + self.config["custom_message"].format(
                me=me,
                version=version,
                build=build,
                prefix=prefix,
                platform=platform,
            )
            if self.config["custom_message"] and self.config["custom_message"] != "no"
            else (
                "<b>◍ Soso-Userbot (◕ᴗ◕✿) soso</b>\n"
                f'<b>◍ {self.strings("owner")}:</b> <a href="tg://user?id={self._me.id}">{me}</a>\n'
                f"<b>◍ {self.strings('version')}:</b> <code>{version}</code> <a href='{build}'></a>\n"
                f"<b>◍ Soso-platforma:</b> <code>{platform}</code>"
                f"\n\n<b>◍ <u>Eynshteyn</u> teoriyasi (ʘᴗʘ✿):</b> temurni soso'si top"
            )
        )

    def _get_mark(self):
        return (
            None
            if not self.config["custom_button10"]
            else [
            {"text": self.config["custom_button10"][0],
             "url": self.config["custom_button10"][1],
            },   
            {"text": self.config["custom_button11"][0],
             "url": self.config["custom_button11"][1],
            },         
          ]
        )

    @loader.inline_everyone
    async def info_inline_handler(self, query: InlineQuery) -> dict:
        """Userbot ma'lumotlarini yuboring"""

        return {
            "title": self.strings("send_info"),
            "description": self.strings("description"),
            "message": self._render_info(),
            "thumb": "https://i.imgur.com/sYULuO1.jpeg",
            "reply_markup": self._get_mark(),
        }

    @loader.unrestricted
    async def infocmd(self, message: Message):
        """Userbot ma'lumotlarini yuboring"""
        await self.inline.form(
            message=message,
            text=self._render_info(),
            reply_markup=self._get_mark(),
            **(
                {"photo": "https://i.imgur.com/t0Qjyhc.jpeg"}
                if not self.config["disable_banner"]
                else {}
            ),
        ) 
