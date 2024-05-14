#!/usr/bin/env python3

from telethon import TelegramClient, events
import telethon
from telethon.sessions import StringSession
from datetime import datetime, timedelta
from loguru import logger
from os import environ, remove
import re
from json5 import load, loads

logger.trace("application started.")

NEED_TO_WAIT_S = int(environ.get("NEED_TO_WAIT_S", "5400"))

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
        self._bot_user_id = re.sub(r":.*", "", self.json["bot_token"])
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

    @property
    def bot_token(self) -> str:
        return self.json.pop("bot_token")

    @property
    def target_chat(self) -> int:
        return self.json["target_chat"]
    
    @property
    def bot_user_id(self):
        return self._bot_user_id


settings = Settings()

lastSend = None

logger.trace("Init TelegramClient...")
with TelegramClient(
    StringSession(settings.session_and_auth_key),
    settings.api_id,
    settings.api_hash,
    base_logger=logger
).start(bot_token=settings.bot_token) as client:
    client: TelegramClient = client
    logger.trace("Telegram client instance created")
    if not settings.is_session_and_auth_key_configurated:
        raise Exception(f"Use session, instead of api_id and api_hash. Set session_and_auth_key to value: «{client.session.save()}»")

    def split_str_by_length(s: str, chunk_limit: int):
        return [s[i:i+chunk_limit] for i in range(0, len(s), chunk_limit)]

    async def send_to_future(peer_id, msg, **kwargs):
        logger.trace("send_to_future sleep")
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
        
    async def buildAlertCallText(event: telethon.events.newmessage.NewMessage.Event):
        message: telethon.tl.patched.Message = event.message
        callText = re.sub(r"^/alert@ktpizzaechobot\s*", "", message.text)
        link = await getLinkOfMessage(message)
        sender: telethon.types.User = await message.get_sender()
        logger.trace("sender: {sender}", sender=sender)
        output = f"На кухню зовёт "
        if sender.username and sender.first_name:
            output += f"{sender.first_name} @{(sender.username)}"
        elif sender.username:
            output += f"@{sender.username}"
        elif sender.first_name:
            output += sender.first_name
        else:
            output += f"аноним с id={sender.id}"
        output += f" в чате {link}"
        if callText:
            output += f": «{callText}»"
        return output
    
    async def alert(event: telethon.events.newmessage.NewMessage.Event):
        global lastSend
        message: telethon.tl.patched.Message = event.message
        if message.sender_id == settings.bot_user_id:
            logger.warning(f"Sender is bot! Skip: {message.text}")
            return
        elif not message.text.startswith("/alert@ktpizzaechobot"):
            logger.debug("Только команда «/alert@ktpizzaechobot» поддерживается из бесед. {event}", event=event)
        elif not message.text.startswith("/alert@ktpizzaechobot "):
            logger.warning("Для вызова всех на кухню необходимо написать команду-приглашение, пробел, пригласительный текст. {event}", event=event)
            await send_to_future(
                message.peer_id,
                f"Для вызова всех на кухню необходимо написать команду-приглашение, пробел, пригласительный текст. Команды-приглашения без пригласительного текста отключены.",
                reply_to=event.message,
                link_preview=False
            )
        elif lastSend is not None and datetime.now() < lastSend + timedelta(seconds=NEED_TO_WAIT_S):
            logger.warning("Слишком частые оповещения {event}", event=event)
            await send_to_future(
                message.peer_id,
                f"Слишком частые оповещения, нужно подождать {lastSend + timedelta(seconds=NEED_TO_WAIT_S) - datetime.now()}",
                reply_to=event.message,
                link_preview=False
            )
        else:
            lastSend = datetime.now()
            sendent = await send_to_future(
                telethon.types.PeerChannel(settings.target_chat),
                await buildAlertCallText(event),
                link_preview=False
            )
            if sendent:
                link = await getLinkOfMessage(sendent[0])
                await send_to_future(
                    message.peer_id,
                    f"Зов создан: {link}",
                    reply_to=event.message,
                    link_preview=False
                )

    @client.on(events.NewMessage())
    async def handler(event: telethon.events.newmessage.NewMessage.Event):
        try:
            message: telethon.tl.patched.Message = event.message
            logger.info("got message {}: {}", message.peer_id, message.message)
            await alert(event)
        except Exception as e:
            logger.exception(e)
            await send_to_future(
                message.peer_id,
                str(e),
                reply_to=event.message,
                link_preview=False
            )
    logger.info("Telegram ready")
    client.run_until_disconnected()
