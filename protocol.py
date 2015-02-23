import rsa

class Protocol:
    def gen_hello(self, name, public_key):
        return self.gen('helo %s %d %d %d' % (name, int(public_key[0]), int(public_key[1]), int(public_key[2])))

    def gen_mesg(self, me, to, message, to_public_key):
        print 'gen_mesg'
        data = rsa.encrypt(message, map(int, to_public_key))
        print 'encrypted', data
        return self.gen('mesg %s %s %s' % (me, to, ' '.join(map(str, data))))

    def gen(self, data):
        return '%s\n' % data

    def parse(self, data):
        if len(data) == 0:
            return False
        if '\n' not in data:
            return False
        data = data[:data.find('\n')]
        ms = data.split(' ')
        type = ms[0]
        data = ms[1:]
        print type

        if type == 'helo':
            return type, data
            self.public_keys[data[0]] = data[1:]
        elif type == 'mesg':
            return type, data
        else:
            raise Exception('unknown type', type)

