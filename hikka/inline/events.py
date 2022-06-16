import functools
import inspect
import logging
import re
from asyncio import Event
from typing import List

from aiogram.types import CallbackQuery, ChosenInlineResult
from aiogram.types import InlineQuery as AiogramInlineQuery
from aiogram.types import (
    InlineQueryResultArticle,
    InlineQueryResultDocument,
    InlineQueryResultGif,
    InlineQueryResultPhoto,
    InlineQueryResultVideo,
    InputTextMessageContent,
)
from aiogram.types import Message as AiogramMessage

from .. import utils
from .types import InlineCall, InlineQuery, InlineUnit

logger = logging.getLogger(__name__)


class Events(InlineUnit):
    async def _message_handler(self, message: AiogramMessage):
        """Processes incoming messages"""
        if message.chat.type != "private":
            return

        for mod in self._allmodules.modules:
            if not hasattr(mod, "aiogram_watcher"):
                continue

            setattr(
                message,
                "answer",
                functools.partial(
                    self._bot_message_answer,
                    message=message,
                ),
            )

            try:
                await mod.aiogram_watcher(message)
            except BaseException:
                logger.exception("Error on running aiogram watcher!")

    async def _inline_handler(self, inline_query: AiogramInlineQuery):
        """Inline query handler (forms' calls)"""
        # Retrieve query from passed object
        query = inline_query.query

        # If we didn't get any query, return help
        if not query:
            await self._query_help(inline_query)
            return

        # First, dispatch all registered inline handlers
        cmd = inline_query.query.split()[0].lower()
        if (
            cmd in self._allmodules.inline_handlers
            and await self.check_inline_security(
                func=self._allmodules.inline_handlers[cmd],
                user=inline_query.from_user.id,
            )
        ):
            instance = InlineQuery(inline_query)

            try:
                result = await self._allmodules.inline_handlers[cmd](instance)
            except BaseException:
                logger.exception("Error on running inline watcher!")
                return

            if not result:
                return

            if isinstance(result, dict):
                result = [result]

            if not isinstance(result, list) or not all(
                (
                    "message" in res
                    or "photo" in res
                    or "gif" in res
                    or "video" in res
                    or "file" in res
                    and "mime_type" in res
                )
                and "title" in res
                for res in result
            ):
                logger.error("Got invalid type from inline handler. Refer to docs for more info")  # fmt: skip
                await instance.e500()
                return

            inline_result = []

            for res in result:
                if "message" in res:
                    inline_result += [
                        InlineQueryResultArticle(
                            id=utils.rand(20),
                            title=res["title"],
                            description=res.get("description"),
                            input_message_content=InputTextMessageContent(
                                res["message"],
                                "HTML",
                                disable_web_page_preview=True,
                            ),
                            thumb_url=res.get("thumb"),
                            thumb_width=128,
                            thumb_height=128,
                            reply_markup=self.generate_markup(
                                res.get("reply_markup")
                            ),
                        )
                    ]
                elif "photo" in res:
                    inline_result += [
                        InlineQueryResultPhoto(
                            id=utils.rand(20),
                            title=res.get("title"),
                            description=res.get("description"),
                            caption=res.get("caption"),
                            parse_mode="HTML",
                            thumb_url=res.get("thumb", res["photo"]),
                            photo_url=res["photo"],
                            reply_markup=self.generate_markup(
                                res.get("reply_markup")
                            ),
                        )
                    ]
                elif "gif" in res:
                    inline_result += [
                        InlineQueryResultGif(
                            id=utils.rand(20),
                            title=res.get("title"),
                            caption=res.get("caption"),
                            parse_mode="HTML",
                            thumb_url=res.get("thumb", res["gif"]),
                            gif_url=res["gif"],
                            reply_markup=self.generate_markup(
                                res.get("reply_markup")
                            ),
                        )
                    ]
                elif "video" in res:
                    inline_result += [
                        InlineQueryResultVideo(
                            id=utils.rand(20),
                            title=res.get("title"),
                            description=res.get("description"),
                            caption=res.get("caption"),
                            parse_mode="HTML",
                            thumb_url=res.get("thumb", res["video"]),
                            video_url=res["video"],
                            mime_type="video/mp4",
                            reply_markup=self.generate_markup(
                                res.get("reply_markup")
                            ),
                        )
                    ]
                elif "file" in res:
                    inline_result += [
                        InlineQueryResultDocument(
                            id=utils.rand(20),
                            title=res.get("title"),
                            description=res.get("description"),
                            caption=res.get("caption"),
                            parse_mode="HTML",
                            thumb_url=res.get("thumb", res["file"]),
                            document_url=res["file"],
                            mime_type=res["mime_type"],
                            reply_markup=self.generate_markup(
                                res.get("reply_markup")
                            ),
                        )
                    ]

            try:
                await inline_query.answer(inline_result, cache_time=0)
            except Exception:
                logger.exception(f"Exception when answering inline query with result from {cmd}")  # fmt: skip
                return

        await self._form_inline_handler(inline_query)
        await self._gallery_inline_handler(inline_query)
        await self._list_inline_handler(inline_query)

    async def _callback_query_handler(
        self,
        query: CallbackQuery,
        reply_markup: List[List[dict]] = None,
    ):
        """Callback query handler (buttons' presses)"""
        if reply_markup is None:
            reply_markup = []

        if re.search(r"authorize_web_(.{8})", query.data):
            self._web_auth_tokens += [
                re.search(r"authorize_web_(.{8})", query.data).group(1)
            ]
            return

        # First, dispatch all registered callback handlers
        for func in self._allmodules.callback_handlers.values():
            if await self.check_inline_security(func=func, user=query.from_user.id):
                try:
                    await func(InlineCall(query, self, None))
                except Exception:
                    logger.exception("Error on running callback watcher!")
                    await query.answer(
                        "Error occured while processing request. More info in logs",
                        show_alert=True,
                    )
                    continue

        for unit_id, unit in self._units.copy().items():
            for button in utils.array_sum(unit.get("buttons", [])):
                if button.get("_callback_data") == query.data:
                    if (
                        button.get("disable_security", False)
                        or unit.get("disable_security", False)
                        or (
                            unit.get("force_me", False)
                            and query.from_user.id == self._me
                        )
                        or not unit.get("force_me", False)
                        and (
                            await self.check_inline_security(
                                func=unit.get(
                                    "perms_map",
                                    lambda: self._client.dispatcher.security._default,
                                )(),  # we call it so we can get reloaded rights in runtime
                                user=query.from_user.id,
                            )
                            if "message" in unit
                            else False
                        )
                    ):
                        pass
                    elif (
                        query.from_user.id
                        not in self._client.dispatcher.security._owner
                        + unit.get("always_allow", [])
                        + button.get("always_allow", [])
                    ):
                        await query.answer("You are not allowed to press this button!")
                        return

                    try:
                        return await button["callback"](
                            InlineCall(query, self, unit_id),
                            *button.get("args", []),
                            **button.get("kwargs", {}),
                        )
                    except Exception:
                        logger.exception("Error on running callback watcher!")
                        await query.answer(
                            "Error occurred while "
                            "processing request. "
                            "More info in logs",
                            show_alert=True,
                        )
                        return

                    del self._units[unit_id]

        if query.data in self._custom_map:
            if (
                self._custom_map[query.data].get("disable_security", False)
                or (
                    self._custom_map[query.data].get("force_me", False)
                    and query.from_user.id == self._me
                )
                or not self._custom_map[query.data].get("force_me", False)
                and (
                    await self.check_inline_security(
                        func=self._custom_map[query.data].get(
                            "perms_map",
                            lambda: self._client.dispatcher.security._default,
                        )(),
                        user=query.from_user.id,
                    )
                    if "message" in self._custom_map[query.data]
                    else False
                )
            ):
                pass
            elif (
                query.from_user.id not in self._client.dispatcher.security._owner
                and query.from_user.id
                not in self._custom_map[query.data].get("always_allow", [])
            ):
                await query.answer("You are not allowed to press this button!")
                return

            await self._custom_map[query.data]["handler"](
                InlineCall(query, self, None),
                *self._custom_map[query.data].get("args", []),
                **self._custom_map[query.data].get("kwargs", {}),
            )
            return

    async def _chosen_inline_handler(
        self,
        chosen_inline_query: ChosenInlineResult,
    ):
        query = chosen_inline_query.query

        for unit_id, unit in self._units.items():
            if (
                unit_id == query
                and "future" in unit
                and isinstance(unit["future"], Event)
            ):
                unit["inline_message_id"] = chosen_inline_query.inline_message_id
                unit["future"].set()
                return

        for unit_id, unit in self._units.copy().items():
            for button in utils.array_sum(unit.get("buttons", [])):
                if (
                    "_switch_query" in button
                    and "input" in button
                    and button["_switch_query"] == query.split()[0]
                    and chosen_inline_query.from_user.id
                    in [self._me]
                    + self._client.dispatcher.security._owner
                    + unit.get("always_allow", [])
                ):

                    query = query.split(maxsplit=1)[1] if len(query.split()) > 1 else ""

                    try:
                        return await button["handler"](
                            InlineCall(chosen_inline_query, self, unit_id),
                            query,
                            *button.get("args", []),
                            **button.get("kwargs", {}),
                        )
                    except Exception:
                        logger.exception("Exception while running chosen query watcher!")  # fmt: skip
                        return

    async def _query_help(self, inline_query: InlineQuery):
        _help = ""
        for name, fun in self._allmodules.inline_handlers.items():
            # If user doesn't have enough permissions
            # to run this inline command, do not show it
            # in help
            if not await self.check_inline_security(
                func=fun,
                user=inline_query.from_user.id,
            ):
                continue

            # Retrieve docs from func
            try:
                doc = utils.escape_html(inspect.getdoc(fun))
            except Exception:
                doc = "◍ Hujjat yo'q"

            _help += f"◍ <code>@{self.bot_username} {name}</code> - {doc}"

        if not _help:
            await inline_query.answer(
                [
                    InlineQueryResultArticle(
                        id=utils.rand(20),
                        title="◍ Barcha inlayn buyruqlar.",
                        description="Sizda inlayn buyruqlar mavjud emas",
                        input_message_content=InputTextMessageContent(
                            "<b>◍ Barcha inlayn buyruqlar yo'q yoki siz ularga kirish imkoniga ega emassiz</b>",
                            "HTML",
                            disable_web_page_preview=True,
                        ),
                        thumb_url="https://i.imgur.com/mMIbOnm.jpeg",
                        thumb_width=128,
                        thumb_height=128,
                    )
                ],
                cache_time=0,
            )
            return

        await inline_query.answer(
            [
                InlineQueryResultArticle(
                    id=utils.rand(20),
                    title="◍ Barcha inlayn buyruqlar.",
                    description=f"◍ Sizda {len(_help.splitlines())} ta buyruq(lar) mavjud.",
                    input_message_content=InputTextMessageContent(
                        f"<b>◍ Barcha inlayn buyruqlar:</b>\n\n{_help}",
                        "HTML",
                        disable_web_page_preview=True,
                    ),
                    thumb_url="https://i.imgur.com/mMIbOnm.jpeg",
                    thumb_width=128,
                    thumb_height=128,
                )
            ],
            cache_time=0,
        )
