import asyncio
import functools
import logging
import time
from types import FunctionType
from typing import List, Optional, Union

from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultGif,
    InlineQueryResultPhoto,
    InputMediaAnimation,
    InputMediaPhoto,
)
from aiogram.utils.exceptions import BadRequest, InvalidHTTPUrlContent, RetryAfter
from telethon.tl.types import Message
from urllib.parse import urlparse
import os

from .. import utils
from .types import InlineUnit

logger = logging.getLogger(__name__)


class ListGalleryHelper:
    def __init__(self, lst: List[str]):
        self.lst = lst

    def __call__(self):
        elem = self.lst[0]
        del self.lst[0]
        return elem


class Gallery(InlineUnit):
    async def gallery(
        self,
        message: Union[Message, int],
        next_handler: Union[FunctionType, List[str]],
        caption: Union[str, FunctionType] = "",
        *,
        force_me: Optional[bool] = False,
        always_allow: Optional[list] = None,
        manual_security: Optional[bool] = False,
        disable_security: Optional[bool] = False,
        ttl: Optional[Union[int, bool]] = False,
        on_unload: Optional[FunctionType] = None,
        preload: Optional[Union[bool, int]] = False,
        gif: Optional[bool] = False,
        silent: Optional[bool] = False,
        _reattempt: bool = False,
    ) -> Union[bool, str]:
        """
        Processes inline gallery
        Args:
            caption
                Caption for photo, or callable, returning caption
            message
                Where to send inline. Can be either `Message` or `int`
            next_handler
                Callback function, which must return url for next photo or list with photo urls
            force_me
                Either this gallery buttons must be pressed only by owner scope or no
            always_allow
                Users, that are allowed to press buttons in addition to previous rules
            ttl
                Time, when the gallery is going to be unloaded. Unload means, that the gallery
                will become unusable. Pay attention, that ttl can't
                be bigger, than default one (1 day) and must be either `int` or `False`
            on_unload
                Callback, called when gallery is unloaded and/or closed. You can clean up trash
                or perform another needed action
            preload
                Either to preload gallery photos beforehand or no. If yes - specify threshold to
                be loaded. Toggle this attribute, if your callback is too slow to load photos
                in real time
            gif
                Whether the gallery will be filled with gifs. If you omit this argument and specify
                gifs in `next_handler`, Hikka will try to determine the filetype of these images
            manual_security
                By default, Hikka will try to inherit inline buttons security from the caller (command)
                If you want to avoid this, pass `manual_security=True`
            disable_security
                By default, Hikka will try to inherit inline buttons security from the caller (command)
                If you want to disable all security checks on this gallery in particular, pass `disable_security=True`
            silent
                Whether the gallery must be sent silently (w/o "Loading inline gallery..." message)
        """

        if not isinstance(caption, str) and not callable(caption):
            logger.error("Invalid type for `caption`")
            return False

        if not isinstance(manual_security, bool):
            logger.error("Invalid type for `manual_security`")
            return False

        if not isinstance(silent, bool):
            logger.error("Invalid type for `silent`")
            return False

        if not isinstance(disable_security, bool):
            logger.error("Invalid type for `disable_security`")
            return False

        if not isinstance(message, (Message, int)):
            logger.error("Invalid type for `message`")
            return False

        if not isinstance(force_me, bool):
            logger.error("Invalid type for `force_me`")
            return False

        if not isinstance(gif, bool):
            logger.error("Invalid type for `gif`")
            return False

        if (
            not isinstance(preload, (bool, int))
            or isinstance(preload, bool)
            and preload
        ):
            logger.error("Invalid type for `preload`")
            return False

        if always_allow and not isinstance(always_allow, list):
            logger.error("Invalid type for `always_allow`")
            return False

        if not always_allow:
            always_allow = []

        if not isinstance(ttl, int) and ttl:
            logger.error("Invalid type for `ttl`")
            return False

        if isinstance(ttl, int) and (ttl > self._markup_ttl or ttl < 10):
            ttl = self._markup_ttl
            logger.debug("Defaulted ttl, because it breaks out of limits")

        if isinstance(next_handler, list):
            if all(isinstance(i, str) for i in next_handler):
                next_handler = ListGalleryHelper(next_handler)
            else:
                logger.error("Invalid type for `next_handler`")
                return False

        unit_id = utils.rand(16)
        btn_call_data = {
            key: utils.rand(10) for key in {"back", "next", "close", "show"}
        }

        try:
            photo_url = await self._call_photo(next_handler)
            if not photo_url:
                return False
        except Exception:
            logger.exception("Error while parsing first photo in gallery")
            return False

        perms_map = self._find_caller_sec_map() if not manual_security else None

        self._units[unit_id] = {
            "type": "gallery",
            "caption": caption,
            "chat": None,
            "message_id": None,
            "uid": unit_id,
            "photo_url": (photo_url if isinstance(photo_url, str) else photo_url[0]),
            "next_handler": next_handler,
            "btn_call_data": btn_call_data,
            "photos": [photo_url] if isinstance(photo_url, str) else photo_url,
            "current_index": 0,
            **({"ttl": round(time.time()) + ttl} if ttl else {}),
            **({"force_me": force_me} if force_me else {}),
            **({"disable_security": disable_security} if disable_security else {}),
            **({"on_unload": on_unload} if callable(on_unload) else {}),
            **({"preload": preload} if preload else {}),
            **({"gif": gif} if gif else {}),
            **({"always_allow": always_allow} if always_allow else {}),
            **({"perms_map": perms_map} if perms_map else {}),
            **({"message": message} if isinstance(message, Message) else {}),
        }

        default_map = {
            **(
                {"ttl": self._units[unit_id]["ttl"]}
                if "ttl" in self._units[unit_id]
                else {}
            ),
            **({"always_allow": always_allow} if always_allow else {}),
            **({"force_me": force_me} if force_me else {}),
            **({"disable_security": disable_security} if disable_security else {}),
            **({"perms_map": perms_map} if perms_map else {}),
            **({"message": message} if isinstance(message, Message) else {}),
        }

        self._custom_map[btn_call_data["back"]] = {
            "handler": asyncio.coroutine(
                functools.partial(
                    self._gallery_back,
                    btn_call_data=btn_call_data,
                    unit_id=unit_id,
                )
            ),
            **default_map,
        }

        self._custom_map[btn_call_data["close"]] = {
            "handler": asyncio.coroutine(
                functools.partial(
                    self._delete_unit_message,
                    unit_uid=unit_id,
                )
            ),
            **default_map,
        }

        self._custom_map[btn_call_data["next"]] = {
            "handler": asyncio.coroutine(
                functools.partial(
                    self._gallery_next,
                    func=next_handler,
                    btn_call_data=btn_call_data,
                    unit_id=unit_id,
                )
            ),
            **default_map,
        }

        self._custom_map[btn_call_data["show"]] = {
            "handler": asyncio.coroutine(
                functools.partial(
                    self._gallery_slideshow,
                    btn_call_data=btn_call_data,
                    unit_id=unit_id,
                )
            ),
            **default_map,
        }

        if isinstance(message, Message) and not silent:
            try:
                status_message = await (
                    message.edit if message.out else message.respond
                )("🌉 <b>Loading gallery...</b>")
            except Exception:
                status_message = None
        else:
            status_message = None

        try:
            q = await self._client.inline_query(self.bot_username, unit_id)
            m = await q[0].click(
                utils.get_chat_id(message) if isinstance(message, Message) else message,
                reply_to=message.reply_to_msg_id
                if isinstance(message, Message)
                else None,
            )
        except Exception:
            logger.exception("Error sending inline gallery")

            del self._units[unit_id]

            if _reattempt:
                msg = (
                    "🚫 <b>A problem occurred with inline bot "
                    "while processing query. Check logs for "
                    "further info.</b>"
                )

                if isinstance(message, Message):
                    await (message.edit if message.out else message.respond)(msg)
                else:
                    await self._client.send_message(message, msg)

                return False

            return await self.gallery(
                message=message,
                next_handler=next_handler,
                caption=caption,
                force_me=force_me,
                always_allow=always_allow,
                manual_security=manual_security,
                disable_security=disable_security,
                ttl=ttl,
                on_unload=on_unload,
                preload=preload,
                gif=gif,
                silent=silent,
                _reattempt=True,
            )

        self._units[unit_id]["chat"] = utils.get_chat_id(m)
        self._units[unit_id]["message_id"] = m.id

        if isinstance(message, Message) and message.out:
            await message.delete()

        if status_message and not message.out:
            await status_message.delete()

        asyncio.ensure_future(self._load_gallery_photos(unit_id))

        return unit_id

    async def _call_photo(self, callback: FunctionType) -> Union[str, bool]:
        """Parses photo url from `callback`. Returns url on success, otherwise `False`"""
        if asyncio.iscoroutinefunction(callback):
            photo_url = await callback()
        elif getattr(callback, "__call__", False):
            photo_url = callback()
        elif isinstance(callback, str):
            photo_url = callback
        elif isinstance(callback, list):
            photo_url = callback[0]
        else:
            logger.error("Invalid type for `next_handler`")
            return False

        if not isinstance(photo_url, (str, list)):
            logger.error("Got invalid result from `next_handler`")
            return False

        return photo_url

    async def _load_gallery_photos(self, unit_id: str):
        """Preloads photo. Should be called via ensure_future"""
        photo_url = await self._call_photo(self._units[unit_id]["next_handler"])

        self._units[unit_id]["photos"] += (
            [photo_url] if isinstance(photo_url, str) else photo_url
        )

        # If only one preload was insufficient to load needed amount of photos
        if self._units[unit_id].get("preload", False) and len(
            self._units[unit_id]["photos"]
        ) - self._units[unit_id]["current_index"] < self._units[unit_id].get(
            "preload", False
        ):
            # Start load again
            asyncio.ensure_future(self._load_gallery_photos(unit_id))

    async def _gallery_slideshow_loop(
        self,
        call: CallbackQuery,
        btn_call_data: List[str] = None,
        unit_id: str = None,
    ):
        while True:
            await asyncio.sleep(7)

            if unit_id not in self._units or not self._units[unit_id].get(
                "slideshow", False
            ):
                return

            await self._custom_map[btn_call_data["next"]]["handler"](
                call,
                *self._custom_map[btn_call_data["next"]].get("args", []),
                **self._custom_map[btn_call_data["next"]].get("kwargs", {}),
            )

    async def _gallery_slideshow(
        self,
        call: CallbackQuery,
        btn_call_data: List[str] = None,
        unit_id: str = None,
    ):
        if not self._units[unit_id].get("slideshow", False):
            self._units[unit_id]["slideshow"] = True
            await self.bot.edit_message_reply_markup(
                inline_message_id=call.inline_message_id,
                reply_markup=self._gallery_markup(unit_id),
            )
            await call.answer("✅ Slideshow on")
        else:
            del self._units[unit_id]["slideshow"]
            await self.bot.edit_message_reply_markup(
                inline_message_id=call.inline_message_id,
                reply_markup=self._gallery_markup(unit_id),
            )
            await call.answer("🚫 Slideshow off")
            return

        asyncio.ensure_future(
            self._gallery_slideshow_loop(
                call,
                btn_call_data,
                unit_id,
            )
        )

    async def _gallery_back(
        self,
        call: CallbackQuery,
        btn_call_data: List[str] = None,
        unit_id: str = None,
    ):
        queue = self._units[unit_id]["photos"]

        if not queue:
            await call.answer("No way back", show_alert=True)
            return

        self._units[unit_id]["current_index"] -= 1

        if self._units[unit_id]["current_index"] < 0:
            self._units[unit_id]["current_index"] = 0
            await call.answer("No way back")
            return

        try:
            await self.bot.edit_message_media(
                inline_message_id=call.inline_message_id,
                media=self._get_current_media(unit_id),
                reply_markup=self._gallery_markup(unit_id),
            )
        except RetryAfter as e:
            await call.answer(
                f"Got FloodWait. Wait for {e.timeout} seconds",
                show_alert=True,
            )
        except Exception:
            logger.exception("Exception while trying to edit media")
            await call.answer("Error occurred", show_alert=True)
            return

    def _get_current_media(
        self,
        unit_id: str,
    ) -> Union[InputMediaPhoto, InputMediaAnimation]:
        """Return current media, which should be updated in gallery"""
        media = self._get_next_photo(unit_id)
        try:
            path = urlparse(media).path
            ext = os.path.splitext(path)[1]
        except Exception:
            ext = None

        if self._units[unit_id].get("gif", False) or ext in {".gif", ".mp4"}:
            return InputMediaAnimation(
                media=media,
                caption=self._get_caption(unit_id),
                parse_mode="HTML",
            )

        return InputMediaPhoto(
            media=media,
            caption=self._get_caption(unit_id),
            parse_mode="HTML",
        )

    async def _gallery_next(
        self,
        call: CallbackQuery,
        btn_call_data: List[str] = None,
        func: FunctionType = None,
        unit_id: str = None,
    ):
        self._units[unit_id]["current_index"] += 1
        # If we exceeded photos limit in gallery and need to preload more
        if self._units[unit_id]["current_index"] >= len(self._units[unit_id]["photos"]):
            await self._load_gallery_photos(unit_id)

        # If we still didn't get needed photo index
        if self._units[unit_id]["current_index"] >= len(self._units[unit_id]["photos"]):
            await call.answer("Can't load next photo")
            return

        if self._units[unit_id].get("preload", False) and len(
            self._units[unit_id]["photos"]
        ) - self._units[unit_id]["current_index"] < self._units[unit_id].get(
            "preload", False
        ):
            logger.debug(f"Started preload for gallery {unit_id}")
            asyncio.ensure_future(self._load_gallery_photos(unit_id))

        try:
            await self.bot.edit_message_media(
                inline_message_id=call.inline_message_id,
                media=self._get_current_media(unit_id),
                reply_markup=self._gallery_markup(unit_id),
            )
        except (InvalidHTTPUrlContent, BadRequest):
            logger.debug("Error fetching photo content, attempting load next one")
            del self._units[unit_id]["photos"][self._units[unit_id]["current_index"]]
            self._units[unit_id]["current_index"] -= 1
            return await self._gallery_next(call, btn_call_data, func, unit_id)
        except RetryAfter as e:
            await call.answer(
                f"Got FloodWait. Wait for {e.timeout} seconds",
                show_alert=True,
            )
            return
        except Exception:
            logger.exception("Exception while trying to edit media")
            await call.answer("Error occurred", show_alert=True)
            return

    def _get_next_photo(self, unit_id: str) -> str:
        """Returns next photo"""
        try:
            return self._units[unit_id]["photos"][self._units[unit_id]["current_index"]]
        except IndexError:
            logger.error(
                "Got IndexError in `_get_next_photo`. "
                f"{self._units[unit_id]['current_index']=} / "
                f"{len(self._units[unit_id]['photos'])=}"
            )
            return self._units[unit_id]["photos"][0]

    def _get_caption(self, unit_id: str) -> str:
        """Calls and returnes caption for gallery"""
        return (
            self._units[unit_id]["caption"]
            if isinstance(self._units[unit_id]["caption"], str)
            or not callable(self._units[unit_id]["caption"])
            else self._units[unit_id]["caption"]()
        )

    def _gallery_markup(self, unit_id: str) -> InlineKeyboardMarkup:
        """Converts `btn_call_data` into a aiogram markup"""
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(
                "back",
                callback_data=self._units[unit_id]["btn_call_data"]["back"],
            ),
            InlineKeyboardButton(
                "slideshow" if not self._units[unit_id].get("slideshow", False) else "⏸",
                callback_data=self._units[unit_id]["btn_call_data"]["show"],
            ),
            InlineKeyboardButton(
                "next",
                callback_data=self._units[unit_id]["btn_call_data"]["next"],
            ),
        )

        markup.add(
            InlineKeyboardButton(
                "🌉 That's a finish time",
                callback_data=self._units[unit_id]["btn_call_data"]["close"],
            ),
        )

        return markup

    async def _gallery_inline_handler(self, inline_query: InlineQuery):
        for unit in self._units.copy().values():
            if (
                inline_query.from_user.id == self._me
                and inline_query.query == unit["uid"]
                and unit["type"] == "gallery"
            ):
                try:
                    path = urlparse(unit["photo_url"]).path
                    ext = os.path.splitext(path)[1]
                except Exception:
                    ext = None

                args = {
                    "thumb_url": "https://img.icons8.com/fluency/344/loading.png",
                    "caption": self._get_caption(unit["uid"]),
                    "parse_mode": "HTML",
                    "reply_markup": self._gallery_markup(unit["uid"]),
                    "id": utils.rand(20),
                    "title": "Processing inline gallery",
                }

                if unit.get("gif", False) or ext in {".gif", ".mp4"}:
                    await inline_query.answer(
                        [InlineQueryResultGif(gif_url=unit["photo_url"], **args)]
                    )
                    return

                await inline_query.answer(
                    [InlineQueryResultPhoto(photo_url=unit["photo_url"], **args)],
                    cache_time=0,
                )
