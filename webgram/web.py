import typing
import tornado.web
import tornado.gen
import tornado.iostream
from tornado.ioloop import IOLoop

if typing.TYPE_CHECKING:
    from . import BareServer

from pyrogram.api.types import MessageMediaDocument, Message


class Web:
    def get_stream_watch(self: 'BareServer'):
        # noinspection PyAbstractClass
        class MtProtoFileStreamer(tornado.web.RequestHandler):
            __slots__ = ['bare']
            bare: 'BareServer'

            async def get(self):
                mid = self.get_argument("mid", "")
                raw_peer = self.get_argument("peer", "")
                peer = self.bare.cast_raw_peer(raw_peer)

                if isinstance(peer, int):
                    self.set_status(peer)
                    return await self.finish()

                if not mid.isdigit():
                    self.set_status(401)
                    return await self.finish()

                range_header = self.request.headers.get("Range", None)

                if range_header is None:
                    offset, data_to_skip = 0, False
                else:
                    offset, data_to_skip = self.bare.parse_http_range(range_header)

                if offset is False:
                    self.set_status(data_to_skip)
                    return await self.finish()

                message = self.bare.get_message(peer, int(mid))

                if not isinstance(message, Message):
                    self.set_status(404)
                    return await self.finish()

                if not isinstance(message.media, MessageMediaDocument):
                    self.set_status(404)
                    return await self.finish()

                size = message.media.document.size
                read_after = offset + data_to_skip

                self.set_status(206 if read_after else 200)
                self.set_header('Content-Type', 'application/octet-stream')
                self.set_header('Content-Range', f'bytes {read_after}-{size}/{size}')
                self.set_header('Accept-Ranges', 'bytes')

                while offset < size:
                    part, offset = await IOLoop.current().run_in_executor(
                        None,
                        self.bare.iter_download,
                        message,
                        offset
                    )

                    if data_to_skip:
                        self.write(part[data_to_skip:])
                        data_to_skip = False

                    else:
                        self.write(part)

                    await self.flush()

                await self.finish()

        MtProtoFileStreamer.bare = self
        return MtProtoFileStreamer

    def get_m3u_generator(self: 'BareServer'):
        # noinspection PyAbstractClass
        class ChannelToM3uStreamer(tornado.web.RequestHandler):
            __slots__ = ['bare']
            bare: 'BareServer'

            async def get(self):
                raw_peer = self.get_argument("peer", "")
                peer = self.bare.cast_raw_peer(raw_peer)

                if isinstance(peer, int):
                    self.set_status(peer)
                    return await self.finish()

                self.set_header('Content-Type', 'application/octet-stream')
                self.set_header('Content-Disposition', f'filename={raw_peer}.m3u')

                offset = 0

                while True:
                    part, offset = await IOLoop.current().run_in_executor(
                        None,
                        self.bare.iter_files,
                        peer,
                        offset
                    )

                    if part is False:
                        break

                    for block in self.bare.documents_m3u(part, raw_peer):
                        self.write(block + "\n")

                    await self.flush()

        ChannelToM3uStreamer.bare = self
        return ChannelToM3uStreamer
