from client import ChatThread

class EveThread(ChatThread):
    def handle_mesg(self, *args):
        # do nefarious things
        pass

print 'I am eve :)'
name = ''
while not name:
    name = raw_input('What is your name: ').strip()
    if ' ' in name or name == 'g':
        print 'your name cannot have spaces or be "g"'
        name = ''

chat_thread = EveThread(name)
chat_thread.start()
sleep(0.5)
chat_thread.ui_thread()
