from telethon.tl.types import MessageMediaDocument
from telethon.tl.types import Message
from aiohttp import web
import typing

if typing.TYPE_CHECKING:
    import webgram


class Streamer:
    async def watch_stream(self: 'webgram.BareServer', request: web.Request) -> web.Response:
        peer = self.to_int_safe(request.match_info["peer"])
        mid = request.match_info["mid"]

        if not mid.isdigit() or not await self.validate_peer(peer):
            return web.Response(status=404)

        message: Message = await self.client.get_messages(peer, ids=int(mid))

        if message is None or not isinstance(message.media, MessageMediaDocument):
            return web.Response(status=404)

        resp = web.StreamResponse(
            status=200,
            headers={
                'Content-Type': 'application/octet-stream',
                'Transfer-Encoding': 'chucked',
            }
        )

        await resp.prepare(request)

        async for part in self.client.iter_download(message.media):
            await resp.write(part)
            await resp.drain()

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
