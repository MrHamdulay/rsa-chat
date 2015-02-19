import rsa
import socket
import threading

class Communicator(threading.Thread):
    def __init__(self):
        self.public_key, self.private_key = rsa.generate_keys()
        self.public_keys = {}

    def init_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', 0))
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        print 'connected'

    def send_raw(self, message):
        data = '%d\0%s\n' % (len(message), message)
        self.sock.sendto(data, ('<broadcast>', 1000))

    def send_hello(self, name, public_key):
        # name, d, bits
        self.send_raw('helo %s %d %d' % (name, self.public_key[0], self.public_key[1])

    def send_to(self, to, message):
        public_key = self.public_keys[to]
        data = rsa.encrypt(message, public_key)
        self.send_raw('mesg %s %s' % (to, data))

    def parse(self, message):
        length_index = message.find('\0')
        length = int(message[:length_index])
        m = message[length_index+1:]
        if not len(m) == length:
            return False
        type, info = m.split(' ')
        return True


    def run():
        self.init_socket()

        data = ''
        while True:
            piece, addr = sock.recvfrom(1000000)
            data += piece
            if self.parse(data):
                data = ''

name = raw_input('What is your name')
communicator = Communicator()
