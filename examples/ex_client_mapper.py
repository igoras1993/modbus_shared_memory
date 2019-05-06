from ModbusSharedMemory.client_server import ModbusMasterTCP
from ModbusSharedMemory.memory import MemoryStore, MemoryVariable
from time import sleep
from textwrap import dedent


def print_variables(memory):
    fmt = dedent("""\
                WORK_MODE: {0},
                PROCESS_STEP: {1},
                CURRENT_VALUE: {2},
                CONTROL_WORD: {3},
                ERROR_STATE: {4}\n""")
    print(fmt.format(
        memory.WORK_MODE, 
        memory.PROCESS_STEP,
        memory.CURRENT_VALUE,
        memory.CONTROL_WORD,
        memory.ERROR_STATE))


# declare mappings, preferd is to have same mapping on server and client side
# but it is your choice. Excange is done by addresses.

# declare memory, 8 words = 16 bytes
mem = MemoryStore(8)

# declare some mappings
# name it as u wish
# e.g. PLC like naming convention

# those variables lays in memory in following places: 
# ( "_" indicates variable place, 
#  "(WW)" represents one word, 
#  "bx" represents x-th bit of that word): 

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

# enough, declare client
client = ModbusMasterTCP(mem)
client.run() # run client exchange service in another thread

# now do what u want with memory
# if u import this file, u can play with variables, remember to kill client at the end! 
# client.kill()
# if u run this file, program will do some actions procedural actions

if __name__ == '__main__':
    mem.WORK_MODE = 4
    print_variables(mem)
    sleep(2)

    mem.PROCESS_STEP = 10
    print_variables(mem)
    sleep(2)

    mem.CURRENT_VALUE = 99999
    print_variables(mem)
    sleep(2)

    mem.CONTROL_WORD = 0b1000000000000000
    print_variables(mem)
    sleep(2)

    client.kill()