#!/usr/bin/env python3

import asyncio
from asyncio import sleep
from telethon import TelegramClient, events
import telethon
from telethon.sessions import StringSession
from datetime import datetime, timedelta
from loguru import logger
from os import environ, remove
import re
from json5 import load, loads
from dateutil import parser
import signal
from collections import deque

logger.trace("application started.")

NEED_TO_WAIT_S = int(environ.get("NEED_TO_WAIT_S", "5400"))

searcher_datetime = re.compile(r"\b(?:(?:[iI]\s?think\s?at\s?)|(?:[яЯ]\s?думаю\s?в\s?))(\d{4}-\d{2}-\d{2}(?:T|\s)(?:\d{1,2}):(?:\d{1,2})(?::(?:\d{1,2})(?:\.\d{1,6})?)?(?:\s?[+-]\d{2}:\d{2}|Z))\b")
searcher_delta = re.compile(r" \((?:⏳|⌛️) \-?(?:\d+ days, )?\d{1,2}(?::\d{1,2}(?::\d{1,2})?)?\)")

need_stop = False

class Settings:
    def __init__(
        self,
        secret_path = environ.get("TELEGRAM_SECRET_PATH", "./secret.json5"),
        content = environ.get("TELEGRAM_SECRET", None)
    ):
        if content:
            logger.debug("use secret environment")
            self.json = loads(content)
        else:
            logger.debug("use secret file")
            with open(secret_path) as f:
                self.json = load(f)
            try:
                remove(secret_path)
            except Exception as e:
                logger.warning("Can't remove secret file, error: «{}»", e)
        self._is_session_and_auth_key_configurated = None

    @property
    def session_and_auth_key(self) -> str:
        output = self.json.pop("session_and_auth_key", None)
        if self._is_session_and_auth_key_configurated is None:
            if output:
                self._is_session_and_auth_key_configurated = True
            else:
                self._is_session_and_auth_key_configurated = False
        return output

    @property
    def is_session_and_auth_key_configurated(self) -> str:
        if self._is_session_and_auth_key_configurated is None:
            return "session_and_auth_key" in self.json
        else:
            return self._is_session_and_auth_key_configurated

    @property
    def api_id(self) -> int:
        return self.json.pop("api_id", 1)

    @property
    def api_hash(self) -> str:
        return self.json.pop("api_hash", "0")


settings = Settings()

logger.trace("Init TelegramClient...")
with TelegramClient(
    StringSession(settings.session_and_auth_key),
    settings.api_id,
    settings.api_hash,
    base_logger=logger
) as client:
    client: TelegramClient = client
    logger.trace("Telegram client instance created")
    if not settings.is_session_and_auth_key_configurated:
        raise Exception(f"Use session, instead of api_id and api_hash. Set session_and_auth_key to value: «{client.session.save()}»")

    username = ""

    async def get_username():
        global username
        if not username:
            username = (await client.get_me()).username
        return username

    def split_str_by_length(s: str, chunk_limit: int):
        return [s[i:i+chunk_limit] for i in range(0, len(s), chunk_limit)]

    async def send_to_future(peer_id, msg, **kwargs) -> list[telethon.types.Message]:
        logger.trace("send_to_future: begin")
        logger.trace("Ready to send {} KiB", len(msg) / 1024)
        sendent = []
        if msg:
            logger.trace(f"ready chars {len(msg)}")
            msgs = split_str_by_length(msg, 4096)
            logger.trace(f"splitted! count: {len(msgs)}")
            logger.trace("Sending...")
            for m in msgs:
                sendent.append(await client.send_message(peer_id, m, **kwargs))
            logger.trace("Sent.")
        logger.trace("sendent: {sendent}", sendent=sendent)
        return sendent
    
    async def getLinkOfMessage(message: telethon.tl.patched.Message):
        chat: telethon.types.Chat = await message.get_chat()
        if chat.username:
            return f"https://t.me/{chat.username}/{message.id}"
        else:
            return f"https://t.me/c/{chat.id}/{message.id}"
    
    def format_timedelta(td):
        total_seconds = int(td.total_seconds())  # Общее количество секунд
        sign = '-' if total_seconds < 0 else ''  # Определяем знак
        total_seconds = abs(total_seconds)  # Берем абсолютную величину для расчета частей
        days, remainder = divmod(total_seconds, 86400)  # Определяем дни и остаток
        hours, remainder = divmod(remainder, 3600)  # Определяем часы и остаток
        minutes, seconds = divmod(remainder, 60)  # Определяем минуты и остаток
        # Формируем строку в зависимости от наличия дней и часов
        if days > 0:
            return f"{sign}{days} days, {hours:02}:{minutes:02}:{seconds:02}"
        elif hours > 0:
            return f"{sign}{hours}:{minutes:02}:{seconds:02}"
        else:
            return f"{sign}{minutes}:{seconds:02}"
    
    messages = {}
    
    queue: deque[telethon.types.Message] = deque()
    
    scheduler_is_running = False
    
    async def scheduler():
        global scheduler_is_running
        scheduler_is_running = True
        global need_stop
        while not need_stop:
            try:
                try:
                    msg = queue.popleft()
                except IndexError:
                    scheduler_is_running = False
                    break
                msg_new = await consume(msg)
                del messages[msg.id]
                if msg_new:
                    messages[msg_new.id] = msg_new
                    queue.append(msg_new)
            except Exception as e:
                logger.exception(e)
            await sleep(1)
    
    async def consume(message: telethon.types.Message) -> telethon.types.Message:
        message: telethon.types.Message = messages[message.id]
        found = searcher_datetime.search(message.message).group(1)
        parsed = parser.parse(found)
        try:
            old_str = searcher_delta.search(message.message).group(0)
        except AttributeError:
            old_str = found
        n = datetime.now().astimezone()
        if parsed - n < timedelta(minutes=-10):
            if old_str != found:
                await message.edit(message.message.replace(old_str, "", 1))
            return
        new_str = f"{found if old_str == found else ''} ({'⏳' if parsed > n else '⌛️'} {format_timedelta(parsed - n)})"
        logger.debug("new_str: {}", new_str)
        message = await message.edit(message.message.replace(old_str, new_str, 1))
        messages[message.id] = message
        return message
    
    async def alert(event: telethon.events.newmessage.NewMessage.Event):
        message: telethon.tl.patched.Message = event.message
        if not (await client.get_me()).is_self:
            logger.debug(f"Sender is not me! Skip: {message.text}")
            return
        found = searcher_datetime.search(message.message)
        logger.debug(found)
        if not found:
            return
        found = found.groups()[0]
        parsed = parser.parse(found)
        n = datetime.now().astimezone()
        if parsed - n > timedelta(minutes=-10):
            queue.append(message)
            if not scheduler_is_running:
                await scheduler()

    @client.on(events.NewMessage())
    async def handler_new(event: telethon.events.newmessage.NewMessage.Event):
        try:
            message: telethon.tl.patched.Message = event.message
            logger.info("got message {}: {}", message.peer_id, message.message)
            messages[message.id] = message
            await alert(event)
        except Exception as e:
            logger.exception(e)
            await send_to_future(
                message.peer_id,
                str(e),
                reply_to=event.message,
                link_preview=False
            )
    
    @client.on(events.MessageEdited())
    async def handler_edit(event: telethon.events.messageedited.MessageEdited.Event):
        if event.message.id in messages:
            messages[event.message.id] = event.message
    
    async def handler_signal():
        global need_stop
        if need_stop:
            exit(1)
        need_stop=True
        await client.disconnect()
    
    signal.signal(signal.SIGINT, handler_signal)
    signal.signal(signal.SIGINT, handler_signal)
    logger.info("Telegram ready")
    loop = client.loop
    for signame in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(getattr(signal, signame),
                                lambda: asyncio.create_task(handler_signal()))
    client.run_until_disconnected()

need_stop = True
