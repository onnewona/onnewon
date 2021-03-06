import os
from telethon.tl.types import Message
from .. import loader, main, translations, utils


@loader.tds
class CoreMod(loader.Module):
    """Control core userbot settings"""

    strings = {
        "name": "Settings",
        "too_many_args": "ð« <b>Arglar juda koÊ»p</b>",
        "blacklisted": "â <b>Chat {} blacklisted from userbot</b>",
        "unblacklisted": "â <b>Chat {} unblacklisted from userbot</b>",
        "user_blacklisted": "â <b>User {} blacklisted from userbot</b>",
        "user_unblacklisted": "â <b>User {} unblacklisted from userbot</b>",
        "what_prefix": "â <b>What should the prefix be set to?</b>",
        "prefix_incorrect": "ð« <b>Prefix must be one symbol in length</b>",
        "prefix_set": "â <b>Command prefix updated. Type</b> <code>{newprefix}setprefix {oldprefix}</code> <b>to change it back</b>",
        "alias_created": "â <b>Alias created. Access it with</b> <code>{}</code>",
        "aliases": "<b>ð Aliases:</b>\n",
        "no_command": "ð« <b>Command</b> <code>{}</code> <b>does not exist</b>",
        "alias_args": "ð« <b>You must provide a command and the alias for it</b>",
        "delalias_args": "ð« <b>You must provide the alias name</b>",
        "alias_removed": "â <b>Alias</b> <code>{}</code> <b>removed.",
        "no_alias": "<b>ð« Alias</b> <code>{}</code> <b>does not exist</b>",
        "db_cleared": "<b>â Database cleared</b>",
        "check_url": "ð« <b>You need to specify valid url containing a langpack</b>",
        "lang_saved": "<b>â Til quyidagiga oÊ»zgardi: {}</b>",
        "pack_saved": "â <b>Translate pack saved!</b>",
        "incorrect_language": "ð« <b>Incorrect language specified</b>",
        "lang_removed": "â <b>Translations reset to default ones</b>",
        "check_pack": "ð« <b>Invalid pack format in url</b>",
    }

    strings_cn = {
        "name": "è¨­ç½®",
        "lang_saved": "<b>â èªè¨å·²æ´æ¹çº: {}</b>",
    }


    strings_ru = {
        "name": "ÐÐ°ÑÑÑÐ¾Ð¹ÐºÐ¸",
        "lang_saved": "<b>â Ð¯Ð·ÑÐº Ð¸Ð·Ð¼ÐµÐ½Ð¸Ð»ÑÑ Ð½Ð°: {}</b>",
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

        string += "\n".join([f"â«ï¸ <code>{i}</code> &lt;- {y}" for i, y in aliases.items()])

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

    async def solangcmd(self, message: Message):
        """Soso tilini oÊ»zgartirish"""
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
            ) + f" <code>{args}</code>",
        )

    @loader.owner
    async def cleardbcmd(self, message: Message):
        """Clears the entire database, effectively performing a factory reset"""
        self._db.clear()
        self._db.save()
        await utils.answer(message, self.strings("db_cleared"))
