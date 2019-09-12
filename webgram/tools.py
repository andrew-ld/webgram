import typing
import werkzeug.utils
import re
import html

from pyrogram.api.functions.channels import GetMessages
from pyrogram.api.functions.upload import GetFile
from pyrogram.api.types.message import Message
from pyrogram.api.functions.messages.search import Search
from pyrogram.api.types import InputMessagesFilterDocument, DocumentAttributeFilename, InputDocumentFileLocation, \
    InputMessageID
from pyrogram.api.types.messages import MessagesNotModified

if typing.TYPE_CHECKING:
    from . import BareServer


RANGE_REGEX = re.compile(r"bytes=([0-9]+)-")
BLOCK_SIZE = 1024 * 1024


class Tools:
    def iter_files(self: 'BareServer', peer: int, offset: int):
        messages = self.client.send(
            Search(
                peer=peer,
                add_offset=offset,
                filter=InputMessagesFilterDocument(),
                q="",
                hash=0,
                limit=200,
                max_date=0,
                min_date=0,
                max_id=0,
                min_id=0,
                offset_id=0,
            )
        )

        if isinstance(messages, MessagesNotModified):
            return False, None

        if not messages.messages:
            return False, None

        offset += len(messages.messages)
        return messages.messages, offset

    def iter_download(self: 'BareServer', message: Message, offset: int):
        session = self.client.media_sessions.get(
            message.media.document.dc_id
        )

        part = session.send(
            GetFile(
                offset=offset,
                limit=BLOCK_SIZE,
                location=InputDocumentFileLocation(
                    id=message.media.document.id,
                    access_hash=message.media.document.access_hash,
                    file_reference=message.media.document.file_reference,
                    thumb_size=""
                ),
            )
        ).bytes

        return part, offset + len(part)

    def get_message(self: 'BareServer', peer, mid: int) -> Message:
        res = self.client.send(
            GetMessages(
                channel=peer,
                id=[InputMessageID(id=mid)]
            )
        )

        if not res.messages:
            return False

        return res.messages[0]

    def get_channels(self: 'BareServer'):
        return filter(lambda x: x.chat.type == "channel", self.client.get_dialogs())

    def homepage_row(self: 'BareServer', chat) -> str:
        return self.config.HOMEPAGE_ROW.format(
            name=html.escape(chat.chat.title),
            id=chat.chat.id
        )

    def documents_m3u(self: 'BareServer', messages: typing.List[Message], raw_peer: str) -> typing.Generator:
        for message in messages:
            filename = next(
                a.file_name
                for a in message.media.document.attributes
                if isinstance(a, DocumentAttributeFilename)
            )

            if filename.split(".")[-1] in self.config.ALLOWED_EXT:
                if message.message:
                    name = f"{message.message} {filename}"
                else:
                    name = filename

                yield f"#EXTINF:-1, {werkzeug.utils.secure_filename(name)}"
                yield f"{self.config.ROOT_URI}/watch/?peer={raw_peer}&mid={message.id}"

    def parse_http_range(self, header: str):
        matches = RANGE_REGEX.search(header)

        if matches is None:
            return False, 400

        offset = matches.group(1)

        if not offset.isdigit():
            return False, 400

        offset = int(offset)
        safe_offset = (offset // BLOCK_SIZE) * BLOCK_SIZE
        data_to_skip = offset - safe_offset

        return safe_offset, data_to_skip

    def cast_raw_peer(self: 'BareServer', raw_peer: str):
        if not raw_peer.startswith("-100"):
            return 400

        if not raw_peer[4:].isdigit():
            return 400

        try:

            return self.client.resolve_peer(raw_peer)

        except TypeError:
            return 404
