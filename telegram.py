#!/usr/bin/env python3

import asyncio
from asyncio import sleep
from telethon import TelegramClient, events
import telethon
from telethon.sessions import StringSession
from datetime import datetime, timedelta, date
from loguru import logger
from os import environ, remove
import re
from json5 import load, loads
from dateutil.parser import parse
import signal
from collections import deque
from zoneinfo import ZoneInfo

logger.trace("application started.")

MAX_PAST_TIME_S = int(environ.get("MAX_PAST_TIME_S", "5400"))
assert MAX_PAST_TIME_S >= 0.0
assert MAX_PAST_TIME_S < 86400.0 # less than 1 day. For support time without day
PARSE_TIMEZONE_DEFAULT = ZoneInfo(environ.get("PARSE_TIMEZONE_DEFAULT", "UTC"))
SCHEDULER_SLEEP_START_S = float(environ.get("SCHEDULER_SLEEP_START_S", 1.0))
assert SCHEDULER_SLEEP_START_S >= 1.0
assert SCHEDULER_SLEEP_START_S < 3155673600.0 # 100 years
SCHEDULER_SLEEP_ALWAYS_ADD_S = float(environ.get("SCHEDULER_SLEEP_ALWAYS_ADD_S", 0.05))
assert SCHEDULER_SLEEP_ALWAYS_ADD_S >= 0.0
assert SCHEDULER_SLEEP_ALWAYS_ADD_S < 3155673600.0 # 100 years
SCHEDULER_SLEEP_FLOOD_STRATEGY = environ.get("SCHEDULER_SLEEP_FLOOD_STRATEGY", "just wait").lower()
assert SCHEDULER_SLEEP_FLOOD_STRATEGY in ["remember per scheduler", "remember per instance", "just wait", "don't wait", "exit scheduler", "exit program"]
SCHEDULER_SLEEP_MAX_S = float(environ.get("SCHEDULER_SLEEP_MAX_S", 1800.0))
assert SCHEDULER_SLEEP_MAX_S >= SCHEDULER_SLEEP_START_S
assert SCHEDULER_SLEEP_MAX_S < 3155673600.0 # 100 years
SCHEDULER_TELEGRAM_SERVER_CAN_OVERRIDE_MAX_S_STRATEGY = environ.get("SCHEDULER_TELEGRAM_SERVER_CAN_OVERRIDE_MAX_S_STRATEGY", "remember per instance")
assert SCHEDULER_TELEGRAM_SERVER_CAN_OVERRIDE_MAX_S_STRATEGY in ["remember per scheduler", "remember per instance", "don't override"]
IS_TRIGGER_AT_EDIT_MESSAGE = loads(environ.get("IS_TRIGGER_AT_EDIT_MESSAGE", "true"))
assert IS_TRIGGER_AT_EDIT_MESSAGE == True or IS_TRIGGER_AT_EDIT_MESSAGE == False
SEARCHER_DATETIME_REGEX = environ.get("SEARCHER_DATETIME_REGEX", r"\b(?:(?:(?:[iI]\s?think\s?)?[Aa]t\s?)|(?:(?:[яЯ]\s?думаю\s?)?(?:[вВкК]|(?:до)|(?:До))\s?))((\d{4}-\d{2}-\d{2})?(?:T|\s)?(?:\d{1,2}):(?:\d{1,2})(?::(?:\d{1,2})(?:\.\d{1,6})?)?(\s?[+-]\d{2}:\d{2}|Z)?)\b")
SEARCHER_DELTA_REGEX = environ.get("SEARCHER_DELTA_REGEX", r" \((?:⏳|⌛️) \-?(?:\d+ days, )?\d{1,2}(?::\d{1,2}(?::\d{1,2})?)?\)")

searcher_datetime = re.compile(SEARCHER_DATETIME_REGEX)
del SEARCHER_DATETIME_REGEX
searcher_delta = re.compile(SEARCHER_DELTA_REGEX)
del SEARCHER_DELTA_REGEX

need_stop = False

def myParse(m: str, old_date: date = None, now: datetime = None) -> tuple[str, datetime, datetime]:
    if now == None:
        now = datetime.now().astimezone()
    match = searcher_datetime.search(m)
    if match == None:
        return None, None, now
    (found, date, timezone) = match.groups()
    parsed = parse(found)
    if timezone == None:
        parsed = parsed.replace(tzinfo=PARSE_TIMEZONE_DEFAULT)
    del timezone
    if date == None:
        if old_date == None:
            if (parsed + timedelta(seconds=MAX_PAST_TIME_S)) < now:
                parsed += timedelta(days=1)
        else:
            parsed = parsed.replace(year=old_date.year, month=old_date.month, day=old_date.day)
    return found, parsed, now

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
    
    def format_timedelta(td: timedelta) -> str:
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
    
    dates = {}
    
    queue: deque[telethon.types.Message] = deque()
    
    scheduler_is_running = False
    
    async def scheduler():
        global need_stop, scheduler_is_running, SCHEDULER_SLEEP_START_S, SCHEDULER_SLEEP_MAX_S
        scheduler_is_running = True
        logger.info("scheduler is running... period_s = SCHEDULER_SLEEP_START_S = {}, SCHEDULER_SLEEP_FLOOD_STRATEGY = {}, SCHEDULER_SLEEP_ALWAYS_ADD_S = {}, SCHEDULER_SLEEP_MAX_S = {}", SCHEDULER_SLEEP_START_S, SCHEDULER_SLEEP_FLOOD_STRATEGY, SCHEDULER_SLEEP_ALWAYS_ADD_S, SCHEDULER_SLEEP_MAX_S)
        period_s: float = SCHEDULER_SLEEP_START_S
        sleep_max_s: float = SCHEDULER_SLEEP_MAX_S
        while not need_stop:
            try:
                try:
                    msg = queue[0]
                except IndexError:
                    break
                msg_new = None
                try:
                    msg_new = await consume(msg)
                except telethon.errors.rpcerrorlist.MessageNotModifiedError as e:
                    logger.exception(e)
                queue.popleft()
                del messages[msg.id]
                if msg_new:
                    logger.debug("new message to queue from consumer: {}", msg_new)
                    messages[msg_new.id] = msg_new
                    queue.append(msg_new)
            except telethon.errors.rpcerrorlist.FloodWaitError as e:
                logger.exception(e)
                logger.info("current period_s = {}, sleep_max_s = {}, SCHEDULER_SLEEP_MAX_S = {}", period_s, sleep_max_s, SCHEDULER_SLEEP_MAX_S)
                if "remember per scheduler" == SCHEDULER_TELEGRAM_SERVER_CAN_OVERRIDE_MAX_S_STRATEGY:
                    sleep_max_s = max(sleep_max_s, e.seconds)
                elif "remember per instance" == SCHEDULER_TELEGRAM_SERVER_CAN_OVERRIDE_MAX_S_STRATEGY:
                    SCHEDULER_SLEEP_MAX_S = sleep_max_s = max(SCHEDULER_SLEEP_MAX_S, sleep_max_s, e.seconds)
                elif "don't override" == SCHEDULER_TELEGRAM_SERVER_CAN_OVERRIDE_MAX_S_STRATEGY:
                    pass
                else:
                    raise NotImplementedError("SCHEDULER_TELEGRAM_SERVER_CAN_OVERRIDE_MAX_S_STRATEGY", SCHEDULER_TELEGRAM_SERVER_CAN_OVERRIDE_MAX_S_STRATEGY)
                if "remember per scheduler" == SCHEDULER_SLEEP_FLOOD_STRATEGY:
                    period_s = max(period_s, e.seconds)
                elif "remember per instance" == SCHEDULER_SLEEP_FLOOD_STRATEGY:
                    SCHEDULER_SLEEP_START_S = max(SCHEDULER_SLEEP_START_S, e.seconds)
                    period_s = max(period_s, SCHEDULER_SLEEP_START_S)
                elif "just wait" == SCHEDULER_SLEEP_FLOOD_STRATEGY:
                    logger.info("just sleep for {} s", e.seconds)
                    await sleep(e.seconds)
                    continue
                elif "don't wait" == SCHEDULER_SLEEP_FLOOD_STRATEGY:
                    pass
                elif "exit scheduler" == SCHEDULER_SLEEP_FLOOD_STRATEGY:
                    dates.clear()
                    return
                elif "exit program" == SCHEDULER_SLEEP_FLOOD_STRATEGY:
                    exit(2)
                else:
                    raise NotImplementedError("SCHEDULER_SLEEP_FLOOD_STRATEGY", SCHEDULER_SLEEP_FLOOD_STRATEGY)
                logger.info("new period_s = {}, sleep_max_s = {}, SCHEDULER_SLEEP_MAX_S = {}", period_s, sleep_max_s, SCHEDULER_SLEEP_MAX_S)
            except Exception as e:
                logger.exception(e)
            logger.debug("sleep for {} s", period_s)
            await sleep(period_s)
            period_s = min(sleep_max_s, period_s+SCHEDULER_SLEEP_ALWAYS_ADD_S)
        scheduler_is_running = False
        logger.info("scheduler is stopping... period_s = {}", period_s)
    
    async def consume(message: telethon.types.Message) -> telethon.types.Message:
        message: telethon.types.Message = messages[message.id]
        found, parsed, n = myParse(message.message, dates.get(message.id))
        if parsed == None:
            logger.warning("parsed date not found in consumer. Panic drop message without edit or restore. {}", message)
            del dates[message.id]
            return
        try:
            old_str = searcher_delta.search(message.message).group(0)
        except AttributeError:
            old_str = found
        if parsed - n < timedelta(seconds=-MAX_PAST_TIME_S):
            if old_str != found:
                await message.edit(message.message.replace(old_str, "", 1))
            del dates[message.id]
            return
        new_str = f"{found if old_str == found else ''} ({'⏳' if parsed > n else '⌛️'} {format_timedelta(parsed - n)})"
        logger.debug("new_str: {}", new_str)
        try:
            new_message = await message.edit(message.message.replace(old_str, new_str, 1))
        except telethon.errors.rpcerrorlist.MessageIdInvalidError as e:
            logger.exception(e)
            del dates[message.id]
            return
        dates[new_message.id] = parsed
        if new_message.id != message.id:
            del dates[message.id]
        return new_message
    
    async def alert(event: telethon.events.newmessage.NewMessage.Event):
        message: telethon.tl.patched.Message = event.message
        logger.debug("got message {}: {}", message.peer_id, message.message)
        if not (await client.get_me()).id == message.sender_id:
            logger.debug("Sender is not me! Skip: %s", message.text)
            return
        if not message or not message.message:
            logger.debug("message is empty: %s", message)
            return
        found, parsed, n = myParse(message.message)
        logger.debug(found)
        if not found:
            return
        if parsed - n > timedelta(seconds=-MAX_PAST_TIME_S):
            messages[message.id] = message
            queue.append(message)
            if not scheduler_is_running:
                await scheduler()

    @client.on(events.NewMessage())
    async def handler_new(event: telethon.events.newmessage.NewMessage.Event):
        try:
            message: telethon.tl.patched.Message = event.message
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
        elif IS_TRIGGER_AT_EDIT_MESSAGE:
            return await handler_new(event)
    
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
