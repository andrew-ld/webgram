import tornado.web
import tornado.ioloop
import logging
import webgram
import os

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    server = webgram.BareServer()

    web = tornado.web.Application([
        (r"/m3u/", server.get_m3u_generator()),
        (r"/watch/", server.get_stream_watch()),
    ])

    web.listen(server.config.PORT, server.config.HOST)
    os.dup2(os.open(os.devnull, os.O_RDWR), 2)
    tornado.ioloop.IOLoop.current().start()
