#!/usr/bin/env python3
from telethon import TelegramClient, events
import telethon
import asyncio
import subprocess
from loguru import logger

logger.trace("application started.")

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


processes= dict()

logger.trace("Init TelegramClient...")
with TelegramClient(
        "check",
        get_api_id(),
        get_api_hash(),
        base_logger=logger
    ).start(bot_token=get_bot_token()) as client:
    client: TelegramClient = client

    def split_str_by_length(s: str, chunk_limit: int):
        return [s[i:i+chunk_limit] for i in range(0, len(s), chunk_limit) ]

    async def send_to_future(user_id, bs):
        logger.trace("send_to_future sleep")
        l = b''.join(bs)
        bs.clear()
        logger.trace("Ready to send {} KiB", len(l) / 1024)
        if l:
            logger.trace(f"get message from bytes length {len(l)}")
            msg = l.decode()
            logger.trace(f"ready chars {len(msg)}")
            msgs = split_str_by_length(msg, 4096)
            logger.trace(f"splitted! count: {len(msgs)}")
            logger.trace("Sending...")
            for m in msgs:
                await client.send_message(user_id, m)
            logger.trace("Sent.")

    async def reader_from_exec(user_id: int, proc: subprocess.Popen):
        logger.debug("{} start read", user_id)
        bs = list()
        while not proc.stdout.closed:
            logger.trace("{}", bs[0] if bs else None)
            task = asyncio.get_event_loop().call_later(0.1, lambda: asyncio.get_running_loop().create_task(send_to_future(user_id, bs)))
            to_append = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: proc.stdout.read(1)
            )
            if not to_append:
                break
            bs.append(to_append)
            task.cancel()
        await send_to_future(user_id, bs)
        logger.debug("{} end read", user_id)

    
    async def good_user_handler(event: telethon.events.newmessage.NewMessage.Event):
        message: telethon.tl.patched.Message = event.message
        user_id = message.peer_id.user_id
        if user_id not in processes:
            process = subprocess.Popen(
                ["python3", "checks.py", str(user_id)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                close_fds=False
            )
            processes[user_id] = process
            asyncio.create_task(
                reader_from_exec(
                    user_id,
                    processes[user_id]
                )
            )
        else:
            if processes[user_id].stdin.closed:
                processes[user_id].kill()
                del processes[user_id]
                await handler(event)
            else:
                logger.trace("Write data to checks.py...")
                processes[user_id].stdin.write(message.message.encode() + b"\n")
                try:
                    processes[user_id].stdin.flush()
                except BrokenPipeError as e:
                    processes[user_id].kill()
                    del processes[user_id]
                    await handler(event)
                logger.trace("Write data ready.")
                logger.debug("Return code: {}", processes[user_id].returncode)

    @client.on(events.NewMessage())
    async def handler(event: telethon.events.newmessage.NewMessage.Event):
        try:
            message: telethon.tl.patched.Message = event.message
            user_id = message.peer_id.user_id
            logger.info("got message {}: {}", user_id, message.message)
            if user_id in good_users:
                await good_user_handler(event)
        except Exception as e:
            logger.exception(e)
            await client.send_message(user_id, str(e))

    logger.info("Telegram ready")
    client.run_until_disconnected()
