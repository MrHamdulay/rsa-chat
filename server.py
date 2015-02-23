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
    def handle(self):
        global public_keys
        #self.request.setblocking(False)

        if not hasattr(self, 'buffer'):
            self.buffer = bytes()
        print 'handler :/'

        while True:
            self.buffer += self.request.recv(4096)
            print self.buffer
            result = protocol.parse(self.buffer)
            if not result:
                return
            print 'we have got', result
            global_lock.acquire()
            if result[0] == 'helo':
                name = result[1][0]
                public_key = result[1][1:]
                print result
                print '1', public_key
                # let's tell this person all the public keys we know
                for other_name, other_public_key in public_keys.iteritems():
                    if name == other_name:
                        continue
                    print 'telling ', name, 'about', other_name
                    self.request.sendall(protocol.gen_hello(other_name, other_public_key))
                public_keys[name] = public_key

                # send everyone the new public key
                print 'lets send the public key to everyone'
                for other_name, sock in sockets.iteritems():
                    if name == other_name:
                        continue
                    print 'distributing to ', other_name
                    sock.sendall(self.buffer)
                sockets[name] = self.request
            elif result[0] == 'mesg':
                print 'mesg from', result[1][0]
                # let's broadcast to everyone (purposefully insecure)
                for name, sock in sockets.iteritems():
                    print 'distributing name to', name
                    print self.buffer
                    sock.sendall(self.buffer)
            elif result[0] == 'clear':
                public_keys = {}
            else:
                print 'i do not know what', result[0], 'is'
            global_lock.release()
            self.buffer = bytes()

    def finish(self):
        pass

print 'starting server'
server = ServerServer(('', 9000), RequestHandler)
try:
    server.serve_forever()
finally:
    server.shutdown()
