import ast
import logging
from typing import Union, Any

from telethon.tl.types import Message

from .. import loader, utils, translations
from ..inline.types import InlineCall

logger = logging.getLogger(__name__)


@loader.tds
class ConfigmodMod(loader.Module):
    """Interactive configurator for Hikka Userbot"""

    strings = {
        "name": "Config",
        "configure": "<b>◍ Bu yerda siz modullarning konfiguratsiyasini sozlashingiz mumkin.</b>",
        "configuring_mod": "(◍•ᴗ•◍) <b>Mod uchun konfiguratsiya opsiyasini tanlang</b> <code>{}</code>",
        "configuring_option": "<b>◍ </b><code>{}</code><b> mod </b><code>{}</code> parametri sozlanmoqda\n<i>◍ {}</i>\n\n<b>Standart: </b><code>{}</code>\n\n<b>Hozirgi: </b><code>{}</code>\n\n{}",
        "option_saved": "<b>◍ Modning </b><code>{}</code><b> varianti </b><code>{}</code><b> saqlandi!</b>\n<b>Hozirgi: </b><code>{}</code>",
        "option_reset": "<b>◍ Modning </b><code>{}</code><b> varianti </b><code>{}</code><b> standart holatga qaytarildi</b>\n<b>Hozirgi: </b><code>{}</code>",
        "args": "<b>× Siz noto'g'ri belgi ko'rsatdingiz</b>",
        "no_mod": "<b>× Modul mavjud emas</b>",
        "no_option": "<b>× Konfiguratsiya opsiyasi mavjud emas</b>",
        "validation_error": "<b>× Siz noto'g'ri konfiguratsiya qiymatini kiritdingiz. \nXato: {}</b>",
        "try_again": "◍ Qayta takrorlash",
        "typehint": "<b>◍ {} boʻlishi kerak/b>",
        "set": "kiritish",
        "set_default_btn": "◍ Eski holatini tiklash",
        "enter_value_btn": "◍ Qiymatni kiritish",
        "enter_value_desc": "◍ Ushbu parametr uchun yangi konfiguratsiya qiymatini kiriting",
        "add_item_desc": "◍ Qo'shish uchun elementni kiriting",
        "remove_item_desc": "◍ O'chirish uchun elementni kiriting",
        "back_btn": "◍ Orqaga",
        "close_btn": "◍ Yopish",
        "add_item_btn": "+ Element qoʻshish",
        "remove_item_btn": "- Element oʻchirish",
    }

    async def client_ready(self, client, db):
        self._db = db
        self._client = client

    @staticmethod
    async def inline__close(call: InlineCall):
        await call.delete()

    @staticmethod
    def prep_value(value: Any) -> Any:
        if isinstance(value, str):
            return utils.escape_html(value.strip())

        if isinstance(value, list) and value:
            return utils.escape_html(", ".join(list(map(str, value))))

        return utils.escape_html(value)

    async def inline__set_config(
        self,
        call: InlineCall,
        query: str,
        mod: str,
        option: str,
        inline_message_id: str,
    ):
        try:
            self.lookup(mod).config[option] = query
        except loader.validators.ValidationError as e:
            await call.edit(
                self.strings("validation_error").format(e.args[0]),
                reply_markup={
                    "text": self.strings("try_again"),
                    "callback": self.inline__configure_option,
                    "args": (mod, option),
                },
            )
            return

        await call.edit(
            self.strings("option_saved").format(
                utils.escape_html(mod),
                utils.escape_html(option),
                self.prep_value(self.lookup(mod).config[option]),
            ),
            reply_markup=[
                [
                    {
                        "text": self.strings("back_btn"),
                        "callback": self.inline__configure,
                        "args": (mod,),
                    },
                    {"text": self.strings("close_btn"), "callback": self.inline__close},
                ]
            ],
            inline_message_id=inline_message_id,
        )

    async def inline__reset_default(self, call: InlineCall, mod: str, option: str):
        mod_instance = self.lookup(mod)
        mod_instance.config[option] = mod_instance.config.getdef(option)

        await call.edit(
            self.strings("option_reset").format(
                utils.escape_html(mod),
                utils.escape_html(option),
                self.prep_value(self.lookup(mod).config[option]),
            ),
            reply_markup=[
                [
                    {
                        "text": self.strings("back_btn"),
                        "callback": self.inline__configure,
                        "args": (mod,),
                    },
                    {"text": self.strings("close_btn"), "callback": self.inline__close},
                ]
            ],
        )

    async def inline__set_bool(
        self,
        call: InlineCall,
        mod: str,
        option: str,
        value: bool,
    ):
        try:
            self.lookup(mod).config[option] = value
        except loader.validators.ValidationError as e:
            await call.edit(
                self.strings("validation_error").format(e.args[0]),
                reply_markup={
                    "text": self.strings("try_again"),
                    "callback": self.inline__configure_option,
                    "args": (mod, option),
                },
            )
            return

        validator = self.lookup(mod).config._config[option].validator
        doc = utils.escape_html(
            validator.doc.get(
                self._db.get(translations.__name__, "lang", "en"), validator.doc["en"]
            )
        )

        await call.edit(
            self.strings("configuring_option").format(
                utils.escape_html(option),
                utils.escape_html(mod),
                utils.escape_html(self.lookup(mod).config.getdoc(option)),
                self.prep_value(self.lookup(mod).config.getdef(option)),
                self.prep_value(self.lookup(mod).config[option]),
                self.strings("typehint").format(doc) if doc else "",
            ),
            reply_markup=self._generate_bool_markup(mod, option),
        )

        await call.answer("√")

    def _generate_bool_markup(self, mod: str, option: str) -> list:
        return [
            [
                *(
                    [
                        {
                            "text": f"√ {self.strings('set')} `True`",
                            "callback": self.inline__set_bool,
                            "args": (mod, option, True),
                        }
                    ]
                    if not self.lookup(mod).config[option]
                    else [
                        {
                            "text": f"× {self.strings('set')} `False`",
                            "callback": self.inline__set_bool,
                            "args": (mod, option, False),
                        }
                    ]
                ),
            ],
            [
                *(
                    [
                        {
                            "text": self.strings("set_default_btn"),
                            "callback": self.inline__reset_default,
                            "args": (mod, option),
                        }
                    ]
                    if self.lookup(mod).config[option]
                    != self.lookup(mod).config.getdef(option)
                    else []
                )
            ],
            [
                {
                    "text": self.strings("back_btn"),
                    "callback": self.inline__configure,
                    "args": (mod,),
                },
                {"text": self.strings("close_btn"), "callback": self.inline__close},
            ],
        ]

    async def inline__add_item(
        self,
        call: InlineCall,
        query: str,
        mod: str,
        option: str,
        inline_message_id: str,
    ):
        try:
            try:
                query = ast.literal_eval(query)
            except Exception:
                pass

            if isinstance(query, (set, tuple)):
                query = list(query)

            if not isinstance(query, list):
                query = [query]

            self.lookup(mod).config[option] = self.lookup(mod).config[option] + query
        except loader.validators.ValidationError as e:
            await call.edit(
                self.strings("validation_error").format(e.args[0]),
                reply_markup={
                    "text": self.strings("try_again"),
                    "callback": self.inline__configure_option,
                    "args": (mod, option),
                },
            )
            return

        await call.edit(
            self.strings("option_saved").format(
                utils.escape_html(mod),
                utils.escape_html(option),
                self.prep_value(self.lookup(mod).config[option]),
            ),
            reply_markup=[
                [
                    {
                        "text": self.strings("back_btn"),
                        "callback": self.inline__configure,
                        "args": (mod,),
                    },
                    {"text": self.strings("close_btn"), "callback": self.inline__close},
                ]
            ],
            inline_message_id=inline_message_id,
        )

    async def inline__remove_item(
        self,
        call: InlineCall,
        query: str,
        mod: str,
        option: str,
        inline_message_id: str,
    ):
        try:
            try:
                query = ast.literal_eval(query)
            except Exception:
                pass

            if isinstance(query, (set, tuple)):
                query = list(query)

            if not isinstance(query, list):
                query = [query]

            query = list(map(str, query))
            found = False

            while True:
                for i, item in enumerate(self.lookup(mod).config[option]):
                    if str(item) in query:
                        del self.lookup(mod).config[option][i]
                        found = True
                        break
                else:
                    break

            if not found:
                raise loader.validators.ValidationError(
                    f"Nothing from passed value ({self.prep_value(query)}) is not in target list"
                )
        except loader.validators.ValidationError as e:
            await call.edit(
                self.strings("validation_error").format(e.args[0]),
                reply_markup={
                    "text": self.strings("try_again"),
                    "callback": self.inline__configure_option,
                    "args": (mod, option),
                },
            )
            return

        await call.edit(
            self.strings("option_saved").format(
                utils.escape_html(mod),
                utils.escape_html(option),
                self.prep_value(self.lookup(mod).config[option]),
            ),
            reply_markup=[
                [
                    {
                        "text": self.strings("back_btn"),
                        "callback": self.inline__configure,
                        "args": (mod,),
                    },
                    {"text": self.strings("close_btn"), "callback": self.inline__close},
                ]
            ],
            inline_message_id=inline_message_id,
        )

    def _generate_series_markup(self, call: InlineCall, mod: str, option: str) -> list:
        return [
            [
                {
                    "text": self.strings("enter_value_btn"),
                    "input": self.strings("enter_value_desc"),
                    "handler": self.inline__set_config,
                    "args": (mod, option, call.inline_message_id),
                }
            ],
            [
                *(
                    [
                        {
                            "text": self.strings("remove_item_btn"),
                            "input": self.strings("remove_item_desc"),
                            "handler": self.inline__remove_item,
                            "args": (mod, option, call.inline_message_id),
                        },
                        {
                            "text": self.strings("add_item_btn"),
                            "input": self.strings("add_item_desc"),
                            "handler": self.inline__add_item,
                            "args": (mod, option, call.inline_message_id),
                        },
                    ]
                    if self.lookup(mod).config[option]
                    else []
                ),
            ],
            [
                *(
                    [
                        {
                            "text": self.strings("set_default_btn"),
                            "callback": self.inline__reset_default,
                            "args": (mod, option),
                        }
                    ]
                    if self.lookup(mod).config[option]
                    != self.lookup(mod).config.getdef(option)
                    else []
                )
            ],
            [
                {
                    "text": self.strings("back_btn"),
                    "callback": self.inline__configure,
                    "args": (mod,),
                },
                {"text": self.strings("close_btn"), "callback": self.inline__close},
            ],
        ]

    async def inline__configure_option(
        self,
        call: InlineCall,
        mod: str,
        config_opt: str,
    ):
        module = self.lookup(mod)
        args = [
            utils.escape_html(config_opt),
            utils.escape_html(mod),
            utils.escape_html(module.config.getdoc(config_opt)),
            self.prep_value(module.config.getdef(config_opt)),
            self.prep_value(module.config[config_opt]),
        ]

        try:
            validator = module.config._config[config_opt].validator
            doc = utils.escape_html(
                validator.doc.get(
                    self._db.get(translations.__name__, "lang", "en"),
                    validator.doc["en"],
                )
            )
        except Exception:
            doc = None
            validator = None
            args += [""]
        else:
            args += [self.strings("typehint").format(doc)]
            if validator.internal_id == "Boolean":
                await call.edit(
                    self.strings("configuring_option").format(*args),
                    reply_markup=self._generate_bool_markup(mod, config_opt),
                )
                return

            if validator.internal_id == "Series":
                await call.edit(
                    self.strings("configuring_option").format(*args),
                    reply_markup=self._generate_series_markup(call, mod, config_opt),
                )
                return

        await call.edit(
            self.strings("configuring_option").format(*args),
            reply_markup=[
                [
                    {
                        "text": self.strings("enter_value_btn"),
                        "input": self.strings("enter_value_desc"),
                        "handler": self.inline__set_config,
                        "args": (mod, config_opt, call.inline_message_id),
                    }
                ],
                [
                    {
                        "text": self.strings("set_default_btn"),
                        "callback": self.inline__reset_default,
                        "args": (mod, config_opt),
                    }
                ],
                [
                    {
                        "text": self.strings("back_btn"),
                        "callback": self.inline__configure,
                        "args": (mod,),
                    },
                    {"text": self.strings("close_btn"), "callback": self.inline__close},
                ],
            ],
        )

    async def inline__configure(self, call: InlineCall, mod: str):
        btns = []

        for param in self.lookup(mod).config:
            btns += [
                {
                    "text": param,
                    "callback": self.inline__configure_option,
                    "args": (mod, param),
                }
            ]

        await call.edit(
            self.strings("configuring_mod").format(utils.escape_html(mod)),
            reply_markup=list(utils.chunks(btns, 2))
            + [
                [
                    {
                        "text": self.strings("back_btn"),
                        "callback": self.inline__global_config,
                    },
                    {"text": self.strings("close_btn"), "callback": self.inline__close},
                ]
            ],
        )

    async def inline__global_config(
        self,
        call: Union[Message, InlineCall],
    ):
        to_config = [
            mod.strings("name")
            for mod in self.allmodules.modules
            if hasattr(mod, "config") and callable(mod.strings)
        ]
        kb = []
        for mod_row in utils.chunks(to_config, 3):
            row = [
                {"text": btn, "callback": self.inline__configure, "args": (btn,)}
                for btn in mod_row
            ]
            kb += [row]

        kb += [[{"text": self.strings("close_btn"), "callback": self.inline__close}]]

        if isinstance(call, Message):
            await self.inline.form(
                self.strings("configure"),
                reply_markup=kb,
                message=call,
            )
        else:
            await call.edit(self.strings("configure"), reply_markup=kb)

    async def configcmd(self, message: Message):
        """Configure modules"""
        args = utils.get_args_raw(message)
        if self.lookup(args):
            form = await self.inline.form(
                "◍ <b>Konfiguratsiya yuklanmoqda</b>",
                message,
                {"text": "◍", "data": "empty"},
                ttl=60 * 60,
            )
            await self.inline__configure(form, args)
            return

        await self.inline__global_config(message)

    async def fconfigcmd(self, message: Message):
        """<module_name> <propery_name> <config_value> - Stands for ForceConfig - Set the config value if it is not possible using default method"""
        args = utils.get_args_raw(message).split(maxsplit=2)

        if len(args) < 3:
            await utils.answer(message, self.strings("args"))
            return

        mod, option, value = args

        instance = self.lookup(mod)
        if not instance:
            await utils.answer(message, self.strings("no_mod"))
            return

        if option not in instance.config:
            await utils.answer(message, self.strings("no_option"))
            return

        instance.config[option] = value
        await utils.answer(
            message,
            self.strings("option_saved").format(
                utils.escape_html(option),
                utils.escape_html(mod),
                self.prep_value(instance.config[option]),
            ),
        )
