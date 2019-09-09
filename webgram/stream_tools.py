from telethon.tl.functions.messages import SearchRequest
from telethon.tl.types import MessageMediaDocument, InputMessagesFilterDocument
from telethon.tl.types import DocumentAttributeFilename
from telethon.tl.types import Document
from telethon.tl.types import Message
from telethon.tl.types.messages import MessagesNotModified
import typing
import werkzeug.utils

if typing.TYPE_CHECKING:
    import webgram


class StreamTools:
    def messages_to_m3u(self: 'webgram.BareServer', messages: typing.List[Message], peer) -> typing.Generator:
        for message in messages:
            if not isinstance(message.media, MessageMediaDocument):
                continue

            document = message.media.document
            filename = self.get_filename(document)

            if filename.split(".")[-1] in self.config.ALLOWED_EXT:
                if message.message:
                    name = f"{message.message} {filename}"
                else:
                    name = filename

                yield f"#EXTINF:-1, {werkzeug.utils.secure_filename(name)}"
                yield f"{self.config.ROOT_URI}/watch/{peer}/{message.id}"

    @staticmethod
    def get_filename(document: Document) -> str:
        return next(
            a.file_name
            for a in document.attributes
            if isinstance(a, DocumentAttributeFilename)
        )

    async def iter_files(self: 'webgram.BareServer', peer) -> typing.AsyncGenerator:
        offset = 0

        while True:
            messages = await self.client(SearchRequest(
                peer=peer, add_offset=offset, hash=0,
                filter=InputMessagesFilterDocument(),
                limit=200, max_date=0, min_date=0,
                max_id=0, min_id=0, offset_id=0, q=""
            ))

            if isinstance(messages, MessagesNotModified):
                break

            if not messages.messages:
                break

            yield messages.messages
            offset += len(messages.messages)
