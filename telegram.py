#!/usr/bin/env python3

def install(package: str):
    import pip
    pip.main(["install", package])

try:
    from telethon import TelegramClient, events
except ModuleNotFoundError:
    install("telethon")
    from telethon import TelegramClient, events
import telethon
from datetime import datetime, timedelta
try:
    from loguru import logger
except ModuleNotFoundError:
    install("loguru")
    from loguru import logger
from os import environ, remove
import re
try:
    from json5 import load, loads
except ModuleNotFoundError:
    install("json5")
    from json5 import load, loads

logger.trace("application started.")


class Settings:
    def __init__(self, secret_path = environ.get("TELEGRAM_SECRET_PATH", "./secret.json5")):
        with open(secret_path) as f:
            self.json = load(f)
        self._bot_user_id = re.sub(r":.*", "", self.json["bot_token"])
        # remove(secret_path)

    @property
    def session_path(self) -> str:
        return self.json.pop("session_path")

    @property
    def api_id(self) -> int:
        return self.json.pop("api_id")

    @property
    def api_hash(self) -> str:
        return self.json.pop("api_hash")

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

processes = dict()

lastSend = None

logger.trace("Init TelegramClient...")
with TelegramClient(
    settings.session_path,
    settings.api_id,
    settings.api_hash,
    base_logger=logger
).start(bot_token=settings.bot_token) as client:
    client: TelegramClient = client
    logger.trace("Telegram client instance created")

    def split_str_by_length(s: str, chunk_limit: int):
        return [s[i:i+chunk_limit] for i in range(0, len(s), chunk_limit)]

    async def send_to_future(peer_id, msg, **kwargs):
        logger.trace("send_to_future sleep")
        logger.trace("Ready to send {} KiB", len(msg) / 1024)
        if msg:
            logger.trace(f"ready chars {len(msg)}")
            msgs = split_str_by_length(msg, 4096)
            logger.trace(f"splitted! count: {len(msgs)}")
            logger.trace("Sending...")
            for m in msgs:
                await client.send_message(peer_id, m, **kwargs)
            logger.trace("Sent.")
    
    async def getLinkOfMessage(event: telethon.events.newmessage.NewMessage.Event):
        message: telethon.tl.patched.Message = event.message
        chat: telethon.types.Chat = await event.get_chat()
        if chat.username:
            return f"https://t.me/{chat.username}/{message.id}"
        else:
            return f"https://t.me/c/{chat.id}/{message.id}"
        
    async def buildAlertCallText(event: telethon.events.newmessage.NewMessage.Event):
        message: telethon.tl.patched.Message = event.message
        callText = re.sub(r"^/alert@ktpizzaechobot\s*", "", message.text)
        link = await getLinkOfMessage(event)
        output = f"На кухню зовёт @{(await message.get_sender()).username} в чате {link}"
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
            raise Exception("Только команда «/alert@ktpizzaechobot» поддерживается из бесед.")
        elif lastSend is not None and datetime.now() < lastSend + timedelta(minutes=30):
            raise Exception(f"Слишком часто отправляете, подождите {lastSend + timedelta(minutes=30) - datetime.now()}.")
        else:
            lastSend = datetime.now()
            await send_to_future(
                telethon.types.PeerChannel(settings.target_chat),
                await buildAlertCallText(event)
            )

    @client.on(events.NewMessage())
    async def handler(event: telethon.events.newmessage.NewMessage.Event):
        try:
            message: telethon.tl.patched.Message = event.message
            logger.info("got message {}: {}", message.peer_id, message.message)
            await alert(event)
        except Exception as e:
            logger.exception(e)
            await send_to_future(message.peer_id, str(e), reply_to=event.message)

    logger.info("Telegram ready")
    client.run_until_disconnected()
