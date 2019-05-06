from ModbusSharedMemory.client_server import ModbusSlaveTCP
from ModbusSharedMemory.memory import MemoryStore, MemoryVariable
from textwrap import dedent
from random import choice as random_choice
import os, platform
from time import sleep

def clear():
    return os.system('cls' if platform.system() == 'Windows' else 'clear')


# declare memory, 8 words = 16 bytes
mem = MemoryStore(8)

# declare some mappings
# name it as u wish
# e.g. PLC like naming convention

# those variables lays in memory in following places: 
# ( "_" indicates variable place, 
#  "(WW)" represents one word, 
# "bx" represents x-th bit of that word): 

#  _
# (WW)(WW)(WW)(WW)(WW)(WW)(WW)(WW)
mem.WORK_MODE = MemoryVariable.byte(address=0, byte_number=0) # 8 bit long

#   _
# (WW)(WW)(WW)(WW)(WW)(WW)(WW)(WW)
mem.PROCESS_STEP = MemoryVariable.byte(address=0, byte_number=1) # 8 bit long

#      __  __
# (WW)(WW)(WW)(WW)(WW)(WW)(WW)(WW)
mem.CURRENT_VALUE = MemoryVariable.uint32(address=1) # this one takes 32 bits = 4 bytes = 2 words, 
                                                     # declare next variable at add>=3 or they 
                                                     # will overlap

#              __
# (WW)(WW)(WW)(WW)(WW)(WW)(WW)(WW)
mem.CONTROL_WORD = MemoryVariable.word(address=3) # this takes 16 bits = 2bytes = 1 word

#              b0
# (WW)(WW)(WW)(WW)(WW)(WW)(WW)(WW)
mem.ERROR_STATE = MemoryVariable.bool(address=3, bit_number=0) # we can overlap by intention, 
                                                               # playing with word bits

# enough, start the server
server = ModbusSlaveTCP(mem) # new server
server.run()                 # run at another thread

if __name__ == "__main__":
    # simple debug screen
    run = True
    while run:
        try:
            clear()
            fmt = dedent("""\
                WORK_MODE: {0},
                PROCESS_STEP: {1},
                CURRENT_VALUE: {2},
                CONTROL_WORD: {3},
                ERROR_STATE: {4}""")
            print(fmt.format(
                mem.WORK_MODE, 
                mem.PROCESS_STEP,
                mem.CURRENT_VALUE,
                mem.CONTROL_WORD,
                mem.ERROR_STATE))
            
            # we can also modify some values, client will see this changes, it is that simple
            mem.ERROR_STATE = random_choice([True, False])
            sleep(0.5)
        except KeyboardInterrupt:
            run = False

    server.kill()