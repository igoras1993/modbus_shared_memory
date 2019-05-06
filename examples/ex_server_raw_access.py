from ModbusSharedMemory.client_server import ModbusSlaveTCP
from ModbusSharedMemory.memory import MemoryStore
from time import sleep
import os, platform
from random import choice

def clear():
    return os.system('cls' if platform.system() == 'Windows' else 'clear')

# declare memory with size of 20 words = 2*20 = 40 Bytes
mem = MemoryStore(20)

# instantiate modbus server (slave) - PLC
server = ModbusSlaveTCP(mem)

# start serving - memory exchange server - in another thread of execution
server.run() 

# User interface layer
# shows memory and puts random int into 0 address
run = True
while run:
    try:
        clear()
        print(mem.dump())
        mem.set_value(0, choice([0, 1, 2, 3, 4]))
        sleep(0.5)
    except KeyboardInterrupt:
        run = False

# kill server!
server.kill()

