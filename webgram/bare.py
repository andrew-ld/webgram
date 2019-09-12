import pyrogram
import pyrogram.session

from . import (
    Config, Tools, Web
)

from pyrogram.api.functions.help import GetConfig
from pyrogram.api.functions.auth import ExportAuthorization, ImportAuthorization


class BareServer(Config, Tools, Web):
    __slots__ = ['client']
    client: pyrogram.Client

    def __init__(self):
        self.client = pyrogram.Client(
            self.config.NAME,
            api_id=self.config.APP_ID,
            api_hash=self.config.APP_HASH
        ).start()

        # populate peer db
        self.client.get_dialogs()

        config = self.client.send(GetConfig())
        dc_ids = [x.id for x in config.dc_options]

        for dc_id in dc_ids:
            if dc_id != self.client.session.dc_id:
                exported_auth = self.client.send(
                    ExportAuthorization(
                        dc_id=dc_id
                    )
                )

                session = pyrogram.session.Session(
                    self.client,
                    dc_id,
                    pyrogram.session.Auth(
                        self.client,
                        dc_id
                    ).create(),
                    is_media=True,
                )

                session.start()

                session.send(
                    ImportAuthorization(
                        id=exported_auth.id,
                        bytes=exported_auth.bytes
                    )
                )

            else:
                session = pyrogram.session.Session(
                    self.client,
                    dc_id,
                    self.client.storage.auth_key,
                    is_media=True,
                )

                session.start()

            self.client.media_sessions[dc_id] = session
