from telethon.tl.types import MessageMediaDocument
from telethon.tl.types import DocumentAttributeFilename
from telethon.tl.types import Document
from telethon.tl.types import Message
import typing

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
                    yield f"#EXTINF:-1,{message.message} {filename}"

                else:
                    yield f"#EXTINF:-1,{filename}"

                yield f"{self.config.ROOT_URI}/watch/{peer}/{message.id}"

    @staticmethod
    def get_filename(document: Document) -> str:
        return next(
            a.file_name
            for a in document.attributes
            if isinstance(a, DocumentAttributeFilename)
        )
