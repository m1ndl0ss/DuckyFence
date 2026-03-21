from Listener import Listener

keys=[]

def addKey(key):
    keys.append(key)

listener = Listener(on_press=addKey)
listener.listen()

input()

listener.stop()
print(keys)


