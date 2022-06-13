import os
from telethon.tl.types import Message
from .. import loader, main, translations, utils


@loader.tds
class CoreMod(loader.Module):
    """Asosiy userbot sozlamalarini boshqaring"""

    strings = {
        "name": "Sozlamalar",
        "too_many_args": "ಥ_ಥ <b>koʻp arglarga ega</b>",
        "blacklisted": "◍ <b>{} chati userbotdan qora roʻyxatga kiritilgan</b>",
        "unblacklisted": "◍ <b>{} chati userbotdan qora roʻyxatdan olib tashlandi</b>",
        "user_blacklisted": "◍ <b>{} foydalanuvchisi userbotdan qora roʻyxatga kiritilgan</b>",
        "user_unblacklisted": "◍ <b>Foydalanuvchi {} userbotdan qora roʻyxatdan chiqarildi</b>",
        "what_prefix": "❓ <b>Prefiks nimaga o'rnatilishi kerak?</b>",
        "prefix_incorrect": "ಥ_ಥ <b>Prefiks uzunligi bir belgi</b>bo'lishi kerak",
        "prefix_set": "◍ <b>Buyruq prefiksi yangilandi. Turi</b> <code>{newprefix}setprefix {oldprefix}</code> <b>ni orqaga o'zgartirish uchun</b>",
        "alias_created": "◍ <b>Taxallus yaratildi. </b>bilan kiring <code>{}</code>",
        "aliases": "<b>🔗 Taxalluslar:</b>\n",
        "no_command": "ಥ_ಥ <b>Buyruq</b> <code>{}</code> <b>mavjud emas.</b>",
        "alias_args": "ಥ_ಥ <b>Siz buyruq va uning taxallusini ko'rsatishingiz kerak</b>",
        "delalias_args": "ಥ_ಥ <b>Siz taxallus nomini kiritishingiz kerak</b>",
        "alias_removed": "◍ <b>Taxallus</b> <code>{}</code> <b>olib tashlandi.",
        "no_alias": "<b>ಥ_ಥ Taxallus</b> <code>{}</code> <b>mavjud</b>",
        "db_cleared": "<b>◍ Maʼlumotlar bazasi tozalandi</b>",
        "check_url": "ಥ_ಥ <b>Langpackni o'z ichiga olgan yaroqli urlni ko'rsatishingiz kerak</b>",
        "lang_saved": "{} <b>Til quyidagiga oʻzgardi:</b>",
        "pack_saved": "◍ <b>Tarjima toʻplami saqlandi!</b>",
        "incorrect_language": "ಥ_ಥ <b>Noto'g'ri til ko'rsatilgan</b>",
        "lang_removed": "◍ <b>Tarjimalar asl holatiga qaytarildi</b>",
        "check_pack": "ಥ_ಥ <b>Url manzilidagi paket formati noto‘g‘ri</b>",
    }

    strings_cn = {
        "too_many_args": "ಥ_ಥ <b>有很多爭論/b>",
        "blacklisted": "◍ <b>聊天 {} 從 userbot 列入黑名單</b>",
        "unblacklisted": "◍ <b>聊天 {} 未從 userbot 列入黑名單</b>",
        "user_blacklisted": "◍ <b>用戶 {} 從 userbot 列入黑名單</b>",
        "user_unblacklisted": "◍ <b>用戶 {} 未從 userbot 列入黑名單</b>",
        "what_prefix": "<b>前綴應該設置成什麼？</b>",
        "prefix_incorrect": "ಥ_ಥ <b>前綴長度必須是一個符號</b>",
        "prefix_set": "◍ <b>命令前綴已更新。輸入</b> <code>{newprefix}setprefix {oldprefix}</code> <b>把它改回來</b>",
        "alias_created": "◍ <b>已創建別名。使用</b> <code>{}</code> 訪問它",
        "aliases": "<b>🔗 別名:</b>\n",
        "no_command": "ಥ_ಥ <b>命令</b> <code>{}</code> <b>不存在</b>",
        "alias_args": "ಥ_ಥ <b>您必須提供命令及其別名</b>",
        "delalias_args": "ಥ_ಥ <b>您必須提供別名</b>",
        "alias_removed": "◍ <b>別名</b> <code>{}</code> <b>已移除.",
        "no_alias": "<b>ಥ_ಥ 別名</b> <code>{}</code> <b>不存在</b>",
        "db_cleared": "<b>◍ 數據庫已清除</b>",
        "check_url": "ಥ_ಥ <b>您需要指定包含 langpack 的有效 url</b>",
        "lang_saved": "{} <b>語言更改如下:</b>",
        "pack_saved": "◍ <b>翻譯包已保存!</b>",
        "incorrect_language": "ಥ_ಥ <b>指定的語言不正確</b>",
        "lang_removed": "◍ <b>翻譯重置為默認翻譯</b>",
        "check_pack": "ಥ_ಥ <b>url 中的包格式無效</b>",
    }

    async def client_ready(self, client, db):
        self._db = db
        self._client = client

    async def blacklistcommon(self, message: Message):
        args = utils.get_args(message)

        if len(args) > 2:
            await utils.answer(message, self.strings("too_many_args"))
            return

        chatid = None
        module = None

        if args:
            try:
                chatid = int(args[0])
            except ValueError:
                module = args[0]

        if len(args) == 2:
            module = args[1]

        if chatid is None:
            chatid = utils.get_chat_id(message)

        module = self.allmodules.get_classname(module)
        return f"{str(chatid)}.{module}" if module else chatid

    async def blacklistcmd(self, message: Message):
        """Blacklist the bot from operating somewhere"""
        chatid = await self.blacklistcommon(message)

        self._db.set(
            main.__name__,
            "blacklist_chats",
            self._db.get(main.__name__, "blacklist_chats", []) + [chatid],
        )

        await utils.answer(message, self.strings("blacklisted").format(chatid))

    async def unblacklistcmd(self, message: Message):
        """Unblacklist the bot from operating somewhere"""
        chatid = await self.blacklistcommon(message)

        self._db.set(
            main.__name__,
            "blacklist_chats",
            list(
                set(self._db.get(main.__name__, "blacklist_chats", [])) - set([chatid])
            ),
        )

        await utils.answer(message, self.strings("unblacklisted").format(chatid))

    async def getuser(self, message: Message):
        try:
            return int(utils.get_args(message)[0])
        except (ValueError, IndexError):
            reply = await message.get_reply_message()

            if reply:
                return reply.sender_id

            if message.is_private:
                return message.to_id.user_id

            await utils.answer(message, self.strings("who_to_unblacklist"))
            return

    async def blacklistusercmd(self, message: Message):
        """Prevent this user from running any commands"""
        user = await self.getuser(message)

        self._db.set(
            main.__name__,
            "blacklist_users",
            self._db.get(main.__name__, "blacklist_users", []) + [user],
        )

        await utils.answer(message, self.strings("user_blacklisted").format(user))

    async def unblacklistusercmd(self, message: Message):
        """Allow this user to run permitted commands"""
        user = await self.getuser(message)

        self._db.set(
            main.__name__,
            "blacklist_users",
            list(set(self._db.get(main.__name__, "blacklist_users", [])) - set([user])),
        )

        await utils.answer(
            message,
            self.strings("user_unblacklisted").format(user),
        )

    @loader.owner
    async def setprefixcmd(self, message: Message):
        """Sets command prefix"""
        args = utils.get_args_raw(message)

        if not args:
            await utils.answer(message, self.strings("what_prefix"))
            return

        if len(args) != 1:
            await utils.answer(message, self.strings("prefix_incorrect"))
            return

        oldprefix = self.get_prefix()
        self._db.set(main.__name__, "command_prefix", args)
        await utils.answer(
            message,
            self.strings("prefix_set").format(
                newprefix=utils.escape_html(args[0]),
                oldprefix=utils.escape_html(oldprefix),
            ),
        )

    @loader.owner
    async def aliasescmd(self, message: Message):
        """Print all your aliases"""
        aliases = self.allmodules.aliases
        string = self.strings("aliases")

        string += "\n".join([f"▫️ <code>{i}</code> &lt;- {y}" for i, y in aliases.items()])

        await utils.answer(message, string)

    @loader.owner
    async def addaliascmd(self, message: Message):
        """Set an alias for a command"""
        args = utils.get_args(message)

        if len(args) != 2:
            await utils.answer(message, self.strings("alias_args"))
            return

        alias, cmd = args
        ret = self.allmodules.add_alias(alias, cmd)

        if ret:
            self.set(
                "aliases",
                {
                    **self.get("aliases", {}),
                    alias: cmd,
                },
            )
            await utils.answer(
                message,
                self.strings("alias_created").format(utils.escape_html(alias)),
            )
        else:
            await utils.answer(
                message,
                self.strings("no_command").format(utils.escape_html(cmd)),
            )

    @loader.owner
    async def delaliascmd(self, message: Message):
        """Remove an alias for a command"""
        args = utils.get_args(message)

        if len(args) != 1:
            await utils.answer(message, self.strings("delalias_args"))
            return

        alias = args[0]
        removed = self.allmodules.remove_alias(alias)

        if not removed:
            await utils.answer(
                message,
                self.strings("no_alias").format(utils.escape_html(alias)),
            )
            return

        current = self.get("aliases", {})
        del current[alias]
        self.set("aliases", current)
        await utils.answer(
            message,
            self.strings("alias_removed").format(utils.escape_html(alias)),
        )

    async def dllangpackcmd(self, message: Message):
        """[link to a langpack | empty to remove] - Change Hikka translate pack (external)"""
        args = utils.get_args_raw(message)

        if not args:
            self._db.set(translations.__name__, "pack", False)
            await self.translator.init()
            await utils.answer(message, self.strings("lang_removed"))
            return

        if not utils.check_url(args):
            await utils.answer(message, self.strings("check_url"))
            return

        self._db.set(translations.__name__, "pack", args)
        success = await self.translator.init()
        await utils.answer(
            message, self.strings("pack_saved" if success else "check_pack")
        )

    async def soso_tilcmd(self, message: Message):
        """Soso tilini oʻzgartirish"""
        args = utils.get_args_raw(message)
        if not args or len(args) != 2:
            await utils.answer(message, self.strings("incorrect_language"))
            return

        possible_pack_path = os.path.join(
            utils.get_base_dir(),
            f"langpacks/{args.lower()}.json",
        )

        if os.path.isfile(possible_pack_path):
            self._db.set(translations.__name__, "pack", args.lower())

        self._db.set(translations.__name__, "lang", args.lower())
        await self.translator.init()

        await utils.answer(
            message,
            self.strings("lang_saved").format(
                utils.get_lang_flag(args.lower() if args.lower() != "en" else "gb")
            ) + f" <code>{args}</code>"
        )

    @loader.owner
    async def cleardbcmd(self, message: Message):
        """Clears the entire database, effectively performing a factory reset"""
        self._db.clear()
        self._db.save()
        await utils.answer(message, self.strings("db_cleared"))
