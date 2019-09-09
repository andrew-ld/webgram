from telethon.tl.types import MessageMediaDocument
from telethon.tl.types import Message
from aiohttp import web
import typing
import re
import telethon

if typing.TYPE_CHECKING:
    import webgram


RANGE_REGEX = re.compile(r"bytes=([0-9]+)-")
BLOCK_SIZE = telethon.client.downloads.MAX_CHUNK_SIZE


class Streamer:
    async def watch_stream(self: 'webgram.BareServer', request: web.Request) -> web.Response:
        peer = self.to_int_safe(request.match_info["peer"])
        mid = request.match_info["mid"]

        if not mid.isdigit() or not await self.validate_peer(peer):
            return web.Response(status=404)

        message: Message = await self.client.get_messages(peer, ids=int(mid))

        if message is None or not isinstance(message.media, MessageMediaDocument):
            return web.Response(status=404)

        offset = request.headers.get("Range", 0)

        if not isinstance(offset, int):
            matches = RANGE_REGEX.search(offset)

            # noinspection PyUnresolvedReferences
            if not isinstance(matches, re.Match):
                return web.Response(status=400)

            offset = matches.group(1)

            if not offset.isdigit():
                return web.Response(status=400)

            offset = int(offset)

        file_size = message.media.document.size
        download_skip = (offset // BLOCK_SIZE) * BLOCK_SIZE
        read_skip = offset - download_skip

        if download_skip >= file_size:
            return web.Response(status=416)

        if read_skip > BLOCK_SIZE:
            return web.Response(status=500)

        resp = web.StreamResponse(
            headers={
                'Content-Type': 'application/octet-stream',
                'Accept-Ranges': 'bytes',
                'Content-Range': f'bytes {offset}-{file_size}/{file_size}'
            },

            status=206 if offset else 200,
        )

        await resp.prepare(request)

        cls = self.client.iter_download(message.media, offset=download_skip)

        async for part in cls:
            if len(part) < read_skip:
                read_skip -= len(part)

            elif read_skip:
                await resp.write(part[read_skip:])
                read_skip = 0

            else:
                await resp.write(part)

        return resp

    async def grab_m3u(self: 'webgram.BareServer', request: web.Request) -> web.Response:
        peer = self.to_int_safe(request.match_info["peer"])

        if not await self.validate_peer(peer):
            return web.Response(status=404)

        resp = web.StreamResponse(
            status=200,
            headers={
                'Content-Type': 'application/octet-stream',
                'Content-Disposition': f'filename={peer}.m3u'
            }
        )

        await resp.prepare(request)

        async for messages in self.iter_files(peer):
            for part in self.messages_to_m3u(messages, peer):
                await resp.write(part.encode(self.config.ENCODING))
                await resp.write(b"\n")

            await resp.drain()

        return resp
