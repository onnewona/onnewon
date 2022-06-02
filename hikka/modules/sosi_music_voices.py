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

__version__ = (1, 3, 0)

def register(cb):
	cb(VoicesMod())
	
class VoicesMod(loader.Module):
	"""Voices list"""
	
	strings = {
		"name": "Voices",
		"main": "<b>🐝 Heey! This is your lovely meme voices.</b>",
		}
		
	async def _directed(self, message):
		"""giorno's theme inform"""
		
		hey = """
<b>🐝 Directed by Robert B. YouTube link:</b> https://youtu.be/_UOzcZbqwig"""
		await message.edit(hey)
		
	async def _giorno(self, message):
		"""giorno's theme inform"""
		
		hey = """
<b>🐝 Giorno's Theme. YouTube link:</b> https://youtu.be/WuiY_f0NUzE"""
		await message.edit(hey)
		
	async def _toby(self, message):
		"""toby fox inform"""
		
		hey = """
<b>🐝 Toby Fox - Fallen Down. YouTube link:</b> https://youtu.be/cGBMTAGzWPs"""
		await message.edit(hey)
		
	async def _rick(self, message):
		"""toby fox inform"""
		
		hey = """
<b>🐝 Rick Roll - Never Gonna Give You Up. YouTube link:</b> https://youtu.be/dQw4w9WgXcQ"""
		await message.edit(hey)
		
	async def _putin(self, message):
		"""toby fox inform"""
		
		hey = """
<b>🐝 Wide Putin Walk. YouTube link:</b> https://youtu.be/Wl959QnD3lM"""
		await message.edit(hey)
	
	async def voicescmd(self, message):
		"""general voices list"""
		
		await self.inline.form(
                    self.strings("main", message),
                    reply_markup=[
                    	[{
							"text": "🐝 Directed by", 
							"callback": self._directed
						}],
                    	[{
							"text": "🦁 Giorno's Theme", 
							"callback": self._giorno
						}],
                    	[{
							"text": "🦥 Toby Fox", 
							"callback": self._toby
						}],
                        [{
							"text": "🐱 Rick Roll", 
							"callback": self._rick
						}],
                        [{
							"text": "🐎 Wide Putin", 
							"callback": self._putin
							}],                        
                    ],
                    ttl=10,
                    message=message,
                )

	async def directedcmd(self, message):
		"""music on directed by robert"""

		reply = await message.get_reply_message()
		await message.delete()
		await message.client.send_file(message.to_id, "https://t.me/anonyusa/84", voice_note=True, reply_to=reply.id if reply else None)
		return

	async def rickcmd(self, message):
		"""music on rick roll"""

		reply = await message.get_reply_message()
		await message.delete()
		await message.client.send_file(message.to_id, "https://t.me/anonyusa/79", voice_note=True, reply_to=reply.id if reply else None)
		return
		
	async def putincmd(self, message):
		"""music on wide putin"""

		reply = await message.get_reply_message()
		await message.delete()
		await message.client.send_file(message.to_id, "https://t.me/anonyusa/86", voice_note=True, reply_to=reply.id if reply else None)
		return

	async def giornocmd(self, message):
		"""music on giorno's theme"""

		reply = await message.get_reply_message()
		await message.delete()
		await message.client.send_file(message.to_id, "https://t.me/anonyusa/85", voice_note=True, reply_to=reply.id if reply else None)
		return

	async def tobycmd(self, message):
		"""music on toby fox"""

		reply = await message.get_reply_message()
		await message.delete()
		await message.client.send_file(message.to_id, "https://t.me/anonyusa/83", voice_note=True, reply_to=reply.id if reply else None)
		return
