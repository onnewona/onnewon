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
class HikkaInfoMod(loader.Module):
    """Show userbot info"""

    strings = {
        "name": "HikkaInfo",
        "owner": "Moderator",
        "version": "Sosi version",
        "build": "Build",
        "prefix": "Prefix",
        "send_info": "Send userbot info",
        "description": "ℹ This will not compromise any sensitive info",
        "up-to-date": "😌 Up-to-date",
        "update_required": "😕 Update required </b><code>.update</code><b>",
        "_cfg_cst_msg": "Custom message for info. May contain {me}, {version}, {build}, {prefix}, {platform} keywords",
        "_cfg_cst_btn": "Custom button for info. Leave empty to remove button",
        "_cfg_banner": "Set `True` in order to disable an image banner",
    }

    strings_ru = {
        "owner": "Владелец",
        "version": "Версия",
        "build": "Сборка",
        "prefix": "Префикс",
        "send_info": "Отправить информацию о юзерботе",
        "description": "ℹ Это не раскроет никакой личной информации",
        "_ihandle_doc_info": "Отправить информацию о юзерботе",
        "up-to-date": "😌 Актуальная версия",
        "update_required": "😕 Требуется обновление </b><code>.update</code><b>",
        "_cfg_cst_msg": "Кастомный текст сообщения в info. Может содержать ключевые слова {me}, {version}, {build}, {prefix}, {platform}",
        "_cfg_cst_btn": "Кастомная кнопка в сообщении в info. Оставь пустым, чтобы убрать кнопку",
        "_cfg_banner": "Поставь `True`, чтобы отключить баннер-картинку",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "custom_message",
                doc=lambda: self.strings("_cfg_cst_msg"),
            ),
            loader.ConfigValue(
                "custom_button",
                ["🏙️ Sosi ! Administration", "https://t.me/netuzb"],
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
            "<b>🌇 Sosi</b>\n"
            + self.config["custom_message"].format(
                me=me,
                version=version,
                build=build,
                prefix=prefix,
                platform=platform,
            )
            if self.config["custom_message"] and self.config["custom_message"] != "no"
            else (
                "<b>🌇 Sosi-Userbot</b>\n"
                f'<b>🌉 {self.strings("owner")}: </b>{me}\n'
                f"<b>🌉 {self.strings('version')}: </b><code>{version}</code> <a href='{build}'></a>\n"
                f"<a href='{upd}'></a>\n"
                f"🏙️ <b>Einstein's theory:</b> <code>If you are reading this, then understand that you are already sucking me.</code> <a href='{self.strings('prefix')} {prefix}'></a>\n"
                f"<a href='{platform}'></a>\n"
            )
        )

    def _get_mark(self):
        return (
            None
            if not self.config["custom_button"]
            else {
                "text": self.config["custom_button"][0],
                "url": self.config["custom_button"][1],
            }
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
