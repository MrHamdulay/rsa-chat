import rsa

class Protocol:
    version = 1

    def gen_hello(self, name, public_key):
        return self.gen('helo %d %s %d %d %d' % (
            Protocol.version,
            name,
            int(public_key[0]), int(public_key[1]), int(public_key[2])))

    def gen_mesg(self, me, to, message, to_public_key):
        data = rsa.encrypt(message, map(int, to_public_key))
        return self.gen('mesg %s %s %s' % (me, to, ' '.join(map(str, data))))

    def gen_bye(self, name):
        return self.gen('bye %s' % name)

    def gen(self, data):
        return '%s\n' % data

    def parse(self, data):
        if len(data) == 0:
            return False
        ms = data.split(' ')
        type = ms[0]
        data = ms[1:]

        if type == 'helo':
            return type, data
            self.public_keys[data[0]] = data[1:]
        elif type == 'mesg':
            return type, data
        elif type == 'bye':
            return type, data[0]
        else:
            raise Exception('unknown type', type)

