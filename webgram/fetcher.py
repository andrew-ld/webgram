from telethon.tl.types.messages import MessagesNotModified
from telethon.tl.types import InputMessagesFilterDocument
from telethon.tl.functions.messages import SearchRequest
import typing

if typing.TYPE_CHECKING:
    import webgram


class Fetcher:
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
