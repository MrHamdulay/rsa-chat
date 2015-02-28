import socket
import threading
import SocketServer
from protocol import Protocol

protocol = Protocol()
global_lock = threading.Lock()
public_keys = {}
sockets = {}

class ServerServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    daemon = True
    def close_request(self, request):
        pass
    def shutdown_request(self, request):
        pass

class RequestHandler(SocketServer.BaseRequestHandler):
    def handle_helo(self, result):
        global public_keys, sockets

        self.name = name = result[1]
        self.version = int(result[0])
        sockets[name] = self.request
        public_key = result[2:]
        if self.version != Protocol.version:
            self.request.sendall(protocol.gen_mesg(
                'God',
                self.name,
                'Your client is out of date, please update',
                public_key))
            return

        # let's tell this person all the public keys we know
        for other_name, other_public_key in public_keys.iteritems():
            # why would we send someone their own keys?
            if name == other_name:
                continue
            self.request.sendall(protocol.gen_hello(
                other_name, other_public_key))
            sockets[other_name].sendall(self.buffer)
        public_keys[name] = public_key

    def handle_mesg(self, result):
        global sockets
        # let's broadcast to everyone (purposefully insecure)
        for name, sock in sockets.iteritems():
            sock.sendall(self.buffer)

    def handle_disconnection(self):
        global sockets
        global_lock.acquire()
        if self.name in sockets:
            del sockets[self.name]
        if self.name in public_keys:
            del public_keys[self.name]
        for name, sock in sockets.iteritems():
            if name == self.name:
                continue
            sock.sendall(protocol.gen_bye(self.name))
        global_lock.release()


    def on_parsed_data(self, data):
        global_lock.acquire()
        if hasattr(self, 'handle_'+data[0]):
            getattr(self, 'handle_'+data[0])(data[1])
        else:
            print 'i do not know what', data[0], 'is'

        global_lock.release()

    def handle(self):
        # i know, the fuck?
        if not hasattr(self, 'buffer'):
            self.name = None
            self.buffer = bytes()

        try:
            while True:
                self.buffer += self.request.recv(4096)
                result = protocol.parse(self.buffer)
                if not result:
                    return

                self.on_parsed_data(result)

                self.buffer = bytes()
        finally:
            print self.name, 'has disconnected'
            self.handle_disconnection()

    def finish(self):
        ''' overload to prevent socketserver from closing socket on disconnect '''
        pass

print 'starting server'
server = ServerServer(('0.0.0.0', 9000), RequestHandler)
try:
    server.serve_forever()
finally:
    server.shutdown()
