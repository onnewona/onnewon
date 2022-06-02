# ▀█▀ █▀▀ █▀▄▀█ █░█ █▀█
# ░█░ ██▄ █░▀░█ █▄█ █▀▄
# ═══════════════════════
# █▀▀ █▀█ █▄▀ █ █▄░█ █▀█ █░█
# ██▄ █▀▄ █░█ █ █░▀█ █▄█ ▀▄▀
# ═════════════════════════════
# meta developer: @netuzb
# meta channel: @umodules

from telethon import events
from .. import loader, utils
from asyncio import sleep
import random

version = (4, 4, 28)

def register(cb):
 cb(DeanonizeMod())
 
class DeanonizeMod(loader.Module):
 """Deanonize a person"""
 
 strings = {
  "name": "Deanonize",
  "main": "<b>🌇 Person successfully deanoned:</b>\n",
  }
  
 async def _get_info(self, message):
  """get information"""
  
  text = utils.get_args_raw(message)
  hey = f"""
<b>🏙️ Information is frozen.</b>"""
  await message.edit(hey)
 
 async def deanoncmd(self, message):
  """deanonize user"""
  
  text = utils.get_args_raw(message)
  sosi = f"""
<b>🌇 This person's social media:</b>

🌉 <a href="https://youtube.com/{text}">YouTube</a> | <a href="https://telegram.me/{text}">Telegram</a> | <a href="https://www.twitch.tv/{text}">Twitch</a>
🌉 <a href="https://pornhub.com/users/{text}">Pornhub</a> | <a href="https://steamcommunity.com/id/{text}">Steam</a> | <a href="https://www.smule.com/{text}">Smule</a>
🌉 <a href="https://{text}.blogspot.com">Blogspot</a> | <a href="https://www.roblox.com/user.aspx?username={text}">Roblox</a> | <a href="https://nitter.net/{text}">Nitter</a>
🌉 <a href="https://dumpor.com/v/{text}">Dumpor</a> | <a href="https://instagram.com/{text}">Instagram</a> | <a href="https://github.com/{text}">Github</a>
🌉 <a href="https://vk.com/{text}">VK.com</a> | <a href="https://www.pinterest.com/{text}">Pinterest</a> | <a href="https://ok.ru/{text}">OK.ru</a>
🌉 <a href="https://gitlab.com/{text}">Gitlab</a> | <a href="https://soundcloud.com/{text}">SoundCloud</a> | <a href="https://www.reddit.com/user/{text}">Reddit</a>"""
  await message.edit("🌉 <b> Checking information...</b>")
  await sleep(2, 0)
  await message.delete()
  await self.inline.form(
                    text = sosi,
                    reply_markup=[
                     [{
       "text": "🌉 Close this information", 
       "callback": self._get_info
      }],                    
                    ],
                    ttl=10,
                    message=message,
                )