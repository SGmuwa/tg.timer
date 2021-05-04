#!/usr/bin/env python3.9
from asyncio.tasks import create_task
from telethon import TelegramClient, events
import telethon
import asyncio
import aiofiles
from dataclasses import dataclass
import subprocess

from telethon.hints import EntityLike

def get_api_id() -> str:
	with open("./api_id.secret", "r") as f:
		return f.read()

def get_api_hash() -> str:
	with open("./api_hash.secret", "r") as f:
		return f.read()

def get_bot_token() -> str:
	with open("./api_bot_token.secret", "r") as f:
		return f.read()

def get_good_users() -> list:
	with open("./good_users.secret", "r") as f:
		return [int(i) for i in f.read().split()]
good_users = get_good_users()

@dataclass
class Proc:
	process: asyncio.subprocess.Process
	stdin: aiofiles.open
	stdout: aiofiles.open

processes: dict[int, Proc] = dict()

with TelegramClient("check", get_api_id(), get_api_hash()) as client:
	client : TelegramClient = client
	client.start(bot_token=get_bot_token())

	async def send_to_future(user_id, bs: list[bytes]):
		await asyncio.sleep(0.1)
		l = b''.join(bs)
		bs.clear()
		if l:
			await client.send_message(user_id, l.decode())

	async def reader_from_exec(user_id: int, proc: Proc):
		pid = proc.process.pid
		while True:
			print("start read")
			bs = list()
			while True:
				bs.append(await proc.stdout.read(1))
				create_task(send_to_future(user_id, bs))
			text = bs.decode()
			if not text:
				print("end read")
				return
			print("readed")
			await client.send_message(user_id, text)
			print("sendend")

	@client.on(events.NewMessage())
	async def handler(event: telethon.events.newmessage.NewMessage.Event):
		message : telethon.tl.patched.Message = event.message
		user_id = message.peer_id.user_id
		print(user_id, message.message)
		await event.respond(str(user_id))
		if user_id in good_users:
			if user_id not in processes:
				process = subprocess.Popen("./checks.py", stdout=subprocess.PIPE, stdin=subprocess.PIPE, close_fds=True)
				mkfifo
				print(f"/proc/{process.pid}/fd/0")
				processes[user_id] = Proc(
					process,
					await aiofiles.open(f"/proc/{process.pid}/fd/0", "wb"),
					await aiofiles.open(f"/proc/{process.pid}/fd/1", "rb")
				)
				asyncio.create_task(reader_from_exec(user_id, processes[user_id]))
			else:
				# if processes[user_id].stdin.is_closing:
				# 	processes[user_id].kill()
				# 	del processes[user_id]
				# 	await handler(event)
				# else:
					await processes[user_id].stdin.write(message.message.encode())
					print(processes[user_id].process.returncode)
			# await event.respond(str(event))
		

	client.run_until_disconnected()
