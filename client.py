import rsa
import sys
import socket
import threading
from time import sleep
import errno
import Queue

from protocol import Protocol

class Communicator(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.public_key, self.private_key = rsa.generate_keys()
        print 'public key', self.public_key
        print 'private key', self.private_key

        self.public_keys = {}
        self.name = name
        self.daemon = True
        self.protocol = Protocol()
        self.send_queue = Queue.Queue()

    def init_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(('localhost', 9000))
        self.sock.setblocking(False)
        print 'connected'

    def send_raw(self, message):
        res = self.sock.sendall(message)

    def send_hello(self, name):
        # name, d, bits
        self.send_raw(self.protocol.gen_hello(name, self.public_key))

    def send_to(self, to, message):
        if to not in self.public_keys:
            print 'I do not know who %s is ' % to
            return
        public_key = self.public_keys[to]
        self.send_raw(self.protocol.gen_mesg(self.name, to, message, public_key))

    def handle_helo(self, name, public_key):
        self.public_keys[name] = public_key
        print name, 'has connected'

    def handle_mesg(self, from_, to, ciphertext):
        if to != self.name:
            return
        plaintext = rsa.decrypt(ciphertext, self.private_key)
        print from_,':', plaintext

    def handle_bye(self, name):
        print name, 'has left the room'
        del self.public_keys[name]

    def process(self, parsed):
        if parsed[0] == 'helo':
            name = parsed[1][1]
            public_key = parsed[1][2:]
            self.handle_helo(name, public_key)
        elif parsed[0] == 'mesg':
            from_ = parsed[1][0]
            to = parsed[1][1]
            ciphertext = map(int, parsed[1][2:])
            self.handle_mesg(from_, to, ciphertext)
        elif parsed[0] == 'bye':
            self.handle_bye(parsed[1])

    def handle_outbox(self):
        try:
            message_to_send = self.send_queue.get(False)
            self.send_to(*message_to_send)
        except Queue.Empty, e:
            pass

    def handle_socket(self):
        try:
            piece = self.sock.recv(1000000)
        except socket.error, e:
            if e.args[0] == errno.EAGAIN or e.args[0] == errno.WOULDBLOCK:
                sleep(0.1)
                return
            else:
                raise
        self._data += piece
        result = self.protocol.parse(self._data)
        if result:
            self.process(result)
            self._data = ''



    def run(self):
        self.init_socket()
        print 'sending public key to everyone'
        self.send_hello(self.name)

        self._data = ''
        while True:
            self.handle_outbox()
            self.handle_socket()

    def ui_thread(self):
        while True:
            inp = raw_input('> ').strip()
            if inp.strip() == 'exit':
                sys.exit(0)
            a = inp.split(' ', 1)
            if len(a) != 2:
                continue
            person, message = a
            self.send_queue.put((person, message), True)



name = raw_input('What is your name: ')
communicator = Communicator(name)
communicator.start()
sleep(0.5)
communicator.ui_thread()
print 'quit'
