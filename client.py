import rsa
import sys
import socket
import threading

class Communicator(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.public_key, self.private_key = rsa.generate_keys()
        self.public_keys = {}
        self.name = name

    def init_socket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', 0))
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        print 'connected'

    def send_raw(self, message):
        print 'sending'
        data = '%d\0%s\n' % (len(message), message)
        self.sock.sendto(data, ('<broadcast>', 1000))

    def send_hello(self, name, public_key):
        # name, d, bits
        self.send_raw('helo %s %d %d' % (name, self.public_key[0], self.public_key[1]))

    def send_to(self, to, message):
        if to not in self.public_keys:
            print 'I do not know who %s is ' % to
            return
        public_key = self.public_keys[to]
        data = rsa.encrypt(message, public_key)
        self.send_raw('mesg %s %s %s' % (self.name, to, data))

    def parse(self, message):
        length_index = message.find('\0')
        length = int(message[:length_index])
        m = message[length_index+1:]
        if not len(m) == length:
            return False
        ms = m.split(' ')
        info = ms[0]
        data = ms[1:]

        if type == 'hello':
            self.public_keys[data[0]] = data[1:]
        elif type == 'mesg' and data[1] == self.name:
            print '%s says: %s' % (data[0], rsa.decrypt(data[2], self.private_key))
        return True


    def run(self):
        self.init_socket()

        data = ''
        print 'network thread begun'
        while True:
            piece, addr = self.sock.recvfrom(1000000)
            data += piece
            if self.parse(data):
                data = ''

name = 'yaseen'#raw_input('What is your name: ')
communicator = Communicator(name)
communicator.start()

while True:
    inp = raw_input('> ')
    if not inp:
        sys.exit(0)
    if ' ' not in inp:
        print 'Please address a person in your message'
        continue
    person, message = raw_input('> ').split(' ', 1)
    communicator.send_to(person, message)
