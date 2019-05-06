from ModbusSharedMemory.client_server import ModbusMasterTCP
from ModbusSharedMemory.memory import MemoryStore

# raw memory usage example

# some specific exceptions to handle
class InvalidAddress(Exception):
    """Invalid address provided"""


class InvalidValue(Exception):
    """Invalid value provided"""

# some input parsing
def parse_address(addr_str, valid_range=(0, 9)):
    if not isinstance(addr_str, str):
        raise InvalidAddress

    if not addr_str.isnumeric():
        raise InvalidAddress

    address = int(addr_str)
    if not valid_range[0] <= address <= valid_range[1]:
        raise InvalidAddress

    return address

def parse_value(value_str, signed=False):
    if not isinstance(value_str, str):
        raise InvalidValue

    try:
        value = int(value_str)
    except ValueError:
        raise InvalidValue
    
    if signed and not (-32768 <= value <= 32767):
        raise InvalidValue
    elif not signed and not (0 <= value <= 65535):
        raise InvalidValue
    return value


# from line 46 to 53 goes all the magic, rest is just playing with memory

if __name__ == "__main__":
    # declare memory with size of 20 words = 2*20 = 40 Bytes
    mem = MemoryStore(20)

    # instatiate modbus client (master) - HMI
    client = ModbusMasterTCP(mem, sync_period=1)

    # start client memory exchange in another thread of execution
    client.run()

    # User interface layer, do what you wish with mem variable
    run = True
    while run:
        try:
            print("Type [R] to print memory state, or:")
            address = input("Select address [0, 19]: ")
            if address == "R":
                print(mem.dump())
                continue
            
            value = input("Type value [0, 65535]: ")
            
            address = parse_address(address, valid_range=(0, 19))
            value = parse_value(value, signed=False)
            mem.set_value(address, value)
        except KeyboardInterrupt:
            run = False
        except InvalidAddress:
            print("Address should be an integer in [0, 19] range!")
        except InvalidValue:
            print("Value should be an integer in [0, 65535] range!")

    # kill client!
    client.kill()


