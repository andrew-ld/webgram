import telethon
import asyncio

from . import (
    Config, StreamTools, Streamer, Checkers
)


class BareServer(Config, StreamTools, Streamer, Checkers):
    client: telethon.TelegramClient

    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.client = telethon.TelegramClient(
            self.config.SESS_NAME,
            self.config.APP_ID,
            self.config.API_HASH,
            loop=loop
        ).start()

        loop.run_until_complete(self.client.get_dialogs())
