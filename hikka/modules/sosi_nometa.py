from .. import loader, utils

@loader.tds
class NoMetaMod(loader.Module):
    """Отключает уведомления и вразумляет людей не писать "Привет, Hi" и др."""

    strings = {
        "name": "NePrivet",
        "no_meta": "<u>Пожалуйста!</u></b>\n<b>Не нужно лишних сообщений</b> по типу <i>'Привет', 'Хай' и др.</i>\nСпрашивай(-те) <b>конкретно</b>, что нужно."
    }

    async def client_ready(self, client, db):
        self.client = client

    @loader.unrestricted
    async def ne_privetcmd(self, message):
        """Если кто-то отправил мету по типу 'Привет', эта команда его вразумит"""
        await self.client.send_message(message.peer_id, self.strings('no_meta'), reply_to=getattr(message, 'reply_to_msg_id', None))
        await message.delete()

    async def watcher(self, message):
        try:
            text = message.raw_text
        except:
            return

        if not message.is_private: return

        meta = [
            'пр', 'прив', 'привет', 'салют', 'алоха', 'hi', 'hello', 'хелло', 'хеллоу', 'хэллоу', 'коничива', 'konichiwa', 'ку',
            'ку ку', 'хай', 'хей', 'хэй', 'hey',
            'здравствуйте', 'здравствуй', 'здорова', 'салом', 'salom', 'салам', 'salam', 'бро', 'брат', 'братан', 'тут?', 'даров', 'дарова'
        ]

        if message.raw_text.lower() in meta:
            await self.client.send_message(message.peer_id, self.strings('no_meta'), reply_to=message.id)
            await self.client.send_read_acknowledge(message.chat_id, clear_mentions=True)