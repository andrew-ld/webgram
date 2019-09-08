import asyncio
import webgram
import aiohttp.web
import logging

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    server = webgram.BareServer(loop)
    app = aiohttp.web.Application(loop=loop)

    app.add_routes([
        aiohttp.web.get('/m3u/{peer}', server.grab_m3u),
        aiohttp.web.get('/watch/{peer}/{mid}', server.watch_stream)
    ])

    logging.basicConfig(level=logging.DEBUG)
    aiohttp.web.run_app(app, host=server.config.HOST, port=server.config.PORT)
