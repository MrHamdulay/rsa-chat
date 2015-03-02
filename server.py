import socket
import threading
import SocketServer
from protocol import Protocol
from time import time

protocol = Protocol()
global_lock = threading.Lock()
public_keys = {}
sockets = {}

class ServerServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    ''' Server that doesn't close requests after we handle messages.
        Logs all server messages to file'''
    daemon = True

    def __init__(self, *args, **kwargs):
        SocketServer.TCPServer.__init__(self, *args, **kwargs)
        self.log_file = open('server.log', 'a')

    def close_request(self, request):
        pass
    def shutdown_request(self, request):
        pass

    def log_client(self, socket, line):
        line = '%s [%s]: %s\n' % (time(), socket.getpeername(), str(line))
        self.log_file.write(line)
        self.log_file.flush()

class ChatRequestHandler(SocketServer.BaseRequestHandler):
    ''' Handle client incoming messages, all we do pretty much is
        distribute messages between client sockets'''
    def __init__(self, request, client_address, server):
        self.name = None
        self.buffer = bytes()
        SocketServer.BaseRequestHandler.__init__(self, request, client_address, server)

    def handle_helo(self, result):
        ''' hello handler from clients '''
        global public_keys, sockets

        self.name = name = result[1]
        print self.name, 'has joined'
        self.version = int(result[0])
        # store this clients socket
        sockets[name] = self.request
        public_key = result[2:]
        # ensure client is using latest vesrion
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
        ''' distribute all messages to everyone (purposefully insecure '''
        global sockets
        # let's broadcast to everyone (purposefully insecure)
        for name, sock in sockets.iteritems():
            sock.sendall(self.buffer)

    def handle_disconnection(self):
        ''' when a client disconnects free all the resources'''
        self.server.log_client(self.request, self.name+' has disconnected')
        global sockets
        global_lock.acquire()
        if self.name in sockets:
            del sockets[self.name]
        if self.name in public_keys:
            del public_keys[self.name]

        # tell all other connected clients that this user has disconnected
        for name, sock in sockets.iteritems():
            if name == self.name:
                continue
            sock.sendall(protocol.gen_bye(self.name))
        global_lock.release()

    def handle_ping(self, result):
        self.request.sendall('pong pong')


    def on_parsed_data(self, data):
        self.server.log_client(self.request, data)
        global_lock.acquire()
        # find the handler method for this request
        if hasattr(self, 'handle_'+data[0]):
            getattr(self, 'handle_'+data[0])(data[1])
        else:
            # we couldn't find a handler message for this type of message
            print 'i do not know what', data[0], 'is'

        global_lock.release()

    def handle(self):
        try:
            while True:
                self.buffer += self.request.recv(4096)
                # parse raw data into nice arrays
                result = protocol.parse(self.buffer)
                if not result:
                    return
                # handle this message
                self.on_parsed_data(result)

                self.buffer = bytes()
        finally:
            print self.name, 'has disconnected'
            self.handle_disconnection()

    def finish(self):
        ''' overload to prevent socketserver from closing socket on disconnect '''
        pass

print 'starting server'
server = ServerServer(('0.0.0.0', 9001), ChatRequestHandler)
try:
    server.serve_forever()
finally:
    server.shutdown()
