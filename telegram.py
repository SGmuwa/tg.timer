#!/usr/bin/env python3.9
from asyncio.tasks import create_task
from re import sub
from telethon import TelegramClient, events
import telethon
import asyncio
import aiofiles
from dataclasses import dataclass
import subprocess
from pathlib import Path
import os
from loguru import logger

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
    client: TelegramClient = client
    client.start(bot_token=get_bot_token())

    async def send_to_future(user_id, bs: list[bytes]):
        logger.trace("send_to_future sleep")
        await asyncio.sleep(0.8)
        l = b''.join(bs)
        bs.clear()
        logger.trace("Ready to send {} KiB", len(l) / 1024)
        if l:
            logger.trace("Sending...")
            await client.send_message(user_id, l.decode())
            logger.trace("Sent.")

    async def reader_from_exec(user_id: int, proc: Proc):
        pid = proc.process.pid
        while True:
            logger.debug("start read")
            bs = list()
            while True:
                logger.trace("Reading...")
                bs.append(
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: proc.process.stdout.read(1)
                    )
                )
                logger.trace("Readed")
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
        message: telethon.tl.patched.Message = event.message
        user_id = message.peer_id.user_id
        logger.info("{}: {}", user_id, message.message)
        await event.respond(str(user_id))
        if user_id in good_users:
            if user_id not in processes:
                # Path(f"./{user_id}/").mkdir(parents=True, exist_ok=True)
                # os.mkfifo(f"./{user_id}/in")
                # os.mkfifo(f"./{user_id}/out")
                # stdin = os.open(f"./{user_id}/in", os.O_WRONLY)
                # if stdin < 1:
                # 	raise EOFError(f"Can't open «./{user_id}/in»")
                # stdout = os.open(f"./{user_id}/out", os.O_ASYNC & os.O_RDONLY)
                # if stdout < 1:
                # 	raise EOFError(f"Can't open «./{user_id}/out»")
                process = subprocess.Popen(
                    "./checks.py",
					stdin=subprocess.PIPE,
					stdout=subprocess.PIPE,
					stderr=subprocess.STDOUT,
					close_fds=False
				)
                processes[user_id] = Proc(
                    process,
                    stdin=10,
                    stdout=12,
                )
                asyncio.create_task(reader_from_exec(
                    user_id, processes[user_id]))
            else:
                # if processes[user_id].stdin.is_closing:
                # 	processes[user_id].kill()
                # 	del processes[user_id]
                # 	await handler(event)
                # else:
                logger.trace("Write data to checks.py...")
                processes[user_id].process.stdin.write(message.message.encode() + b"\n\0\-1")
                processes[user_id].process.stdin.flush()
                logger.trace("Write data ready.")
                logger.debug("Return code: {}", processes[user_id].process.returncode)
            # await event.respond(str(event))

    logger.info("Telegram ready")
    client.run_until_disconnected()
