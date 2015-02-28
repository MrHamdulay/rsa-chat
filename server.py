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
        print 'doing helo thing'
        global public_keys, sockets

        self.name = name = result[0]
        sockets[name] = self.request
        public_key = result[1:]

        # let's tell this person all the public keys we know
        for other_name, other_public_key in public_keys.iteritems():
            # why would we send someone their own keys?
            if name == other_name:
                continue
            print other_name
            self.request.sendall(protocol.gen_hello(
                other_name, other_public_key))
            sockets[other_name].sendall(self.buffer)
        public_keys[name] = public_key

    def handle_mesg(self, result):
        global sockets
        # let's broadcast to everyone (purposefully insecure)
        for name, sock in sockets.iteritems():
            sock.sendall(self.buffer)

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

    def finish(self):
        ''' overload to prevent socketserver from closing socket on disconnect '''
        pass

print 'starting server'
server = ServerServer(('', 9000), RequestHandler)
try:
    server.serve_forever()
finally:
    server.shutdown()
