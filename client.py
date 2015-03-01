import rsa
import sys
import socket
import threading
from time import sleep, time
import errno
import Queue

from protocol import Protocol

class ChatThread(threading.Thread):

    def __init__(self, name):
        threading.Thread.__init__(self)
        self.public_key, self.private_key = rsa.generate_keys()
        print 'public key', self.public_key
        print 'private key', self.private_key

        self._last_ping = 0
        self.public_keys = {}
        self.name = name
        self.daemon = True
        self.protocol = Protocol()
        # queue that goes between input thread and network thread
        self.send_queue = Queue.Queue()

    def init_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(('hamdulay.co.za', 9000))
        self.sock.setblocking(False)
        print 'connected'

    def send_raw(self, message):
        res = self.sock.sendall(message)

    def send_hello(self, name):
        ''' send "hello" message to server, tell them my name and public key '''
        # name, d, bits
        self.send_raw(self.protocol.gen_hello(name, self.public_key))

    def send_to(self, to, message):
        ''' send an encrypted message to someone '''
        # if we're sending a global message
        if to == 'g':
            # send to everyone except ourselves
            for name in self.public_keys:
                if name == self.name:
                    continue
                self.send_to(name, message)
            return
        elif to not in self.public_keys:
            print 'I do not know who %s is ' % to
            return
        public_key = self.public_keys[to]
        self.send_raw(self.protocol.gen_mesg(self.name, to, message, public_key))

    def handle_helo(self, name, public_key):
        ''' we have received a hello from someone '''
        self.public_keys[name] = public_key
        print name, 'has joined the room'

    def handle_mesg(self, from_, to, ciphertext):
        ''' someone has sent a message to someone '''
        if to != self.name:
            return
        plaintext = rsa.decrypt(ciphertext, self.private_key)
        print from_,':', plaintext

    def handle_bye(self, name):
        print name, 'has left the room'
        del self.public_keys[name]

    def process(self, parsed):
        ''' given some raw data, figure out what it's
            about and return it nicely formatted '''
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
        ''' check if we have a message in our send queue '''
        try:
            message_to_send = self.send_queue.get(False)
            self.send_to(*message_to_send)
        except Queue.Empty, e:
            pass

    def handle_socket(self):
        ''' check if the server has said something '''
        try:
            piece = self.sock.recv(1000000)
        except socket.error, e:
            # there's no data, wait a little bit
            if e.args[0] == errno.EAGAIN or e.args[0] == errno.EWOULDBLOCK:
                sleep(0.1)
                return
            else:
                raise
        self._data += piece
        parts = self._data.split('\n')
        for part in parts:
            if not part:
                continue
            result = self.protocol.parse(part)
            if result:
                self.process(result)
                self._data = ''

    def send_ping(self):
        if time() - 30 > self._last_ping:
            self._last_ping = time()
            self.sock.sendall('ping ping')

    def run(self):
        self.init_socket()
        print 'sending public key to everyone'
        self.send_hello(self.name)

        self._data = ''
        while True:
            # check outbox
            self.handle_outbox()
            # check server inbox
            self.handle_socket()
            self.send_ping()

    def ui_thread(self):
        while True:
            # user input
            inp = raw_input(self.name+'> ').strip()
            if inp.strip() == 'exit':
                sys.exit(0)
            a = inp.split(' ', 1)
            if len(a) != 2:
                print 'who are you sending this message to? if everyone prefix with g'
                print 'the following people are in the room: ' + ', '.join(self.public_keys.keys())
                continue
            person, message = a
            # send message
            self.send_queue.put((person, message), True)


if __name__ == '__main__':
    print '''Welcome to Yaseen's insecure secure chat implementation.

    In order to send a message to everyone in the room start your message with
    "g" and then a space.

    To send a private message start your message with the person's name.
    '''

    name = ''
    while not name:
        name = raw_input('What is your name: ').strip()
        if ' ' in name or name == 'g':
            print 'your name cannot have spaces or be "g"'
            name = ''

    chat_thread = ChatThread(name)
    chat_thread.start()
    sleep(0.5)
    chat_thread.ui_thread()
    print 'quit'
