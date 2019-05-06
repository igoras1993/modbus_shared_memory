from copy import deepcopy
from time import sleep, time
from math import log10
from collections import defaultdict

class MemoryVariable:
    allowed_types = {'bool', 'byte', 'word', 'uint32'}
    type_sizes = {'bool': 1, 'byte': 8, 'word': 16, 'uint32': 32} # size in bits

    def __init__(self, address, bit_number=None, byte_number=None, var_type='word'):
        """
        User for storing named variables in MemoryStrore
        :param address: address of variable in memory, in words (double byte)
        :param var_type: type of variable, should be one of {'bool', 'byte', 'word', 'uint32'}
        :param bit_number: number of bit, in range (0..15), should be None fo variables other than 'bool'
        :param byte_number: number of byte, should be one of (0, 1) for variable type 'byte', None otherwise
        :return: MemoryVariable instance
        """
        
        # Careful assertions
        if var_type not in MemoryVariable.allowed_types:
            raise ValueError("var_type should be one of {}".format(MemoryVariable.allowed_types))

        if var_type == 'word':
            # bit number and byte_number should be none
            if bit_number is not None or byte_number is not None:
                raise ValueError("For 'word' var_type, bit_number and byte_number should be None")
        
        elif var_type == 'uint32':
            # bit and byte number should be none
            if bit_number is not None or byte_number is not None:
                raise ValueError("For 'uint32' var_type, bit_number and byte_number should be None")
        
        elif var_type == 'bool':
            # bit_number should be in range of (0..15) and byte_number should be None
            if byte_number is not None:
                raise ValueError("For 'bool' var_type, byte_number should be None")
        
            if not bit_number in range(16):
                raise ValueError("for 'bool' var_type, bit_number should be in range of (0..15)")
        
        elif var_type == 'byte':
            # bit number should be None and byte_number should be in range
            if bit_number is not None:
                raise ValueError("For 'byte' var_type, bit_number should be None")
            
            if not byte_number in range(2):
                raise ValueError("For 'byte' var_type, byte_number should be in (0, 1), but was {}".format(byte_number))
        
        
        self.type = var_type
        self.bit_number = bit_number
        self.byte_number = byte_number
        self.address = address
    
    @classmethod
    def bool(cls, address, bit_number):
        return cls(address=address, var_type='bool', bit_number=bit_number, byte_number=None)
    
    @classmethod
    def byte(cls, address, byte_number):
        return cls(address=address, var_type='byte', bit_number=None, byte_number=byte_number)

    @classmethod
    def word(cls, address):
        return cls(address=address, var_type='word', bit_number=None, byte_number=None)

    @classmethod
    def uint32(cls, address):
        return cls(address=address, var_type='uint32', bit_number=None, byte_number=None)

    def build_value_stack(self, value, memory_instance):
        if not isinstance(memory_instance, MemoryStore):
            raise ValueError("memory_instance should be instance of MemoryStore")

        if self.type == 'bool':
            if not isinstance(value, bool):
                raise ValueError("Value should be bool type")

            number = memory_instance.get_value(self.address)
            mask = 1 << self.bit_number
            return ((number & ~mask) | ((1*value << self.bit_number) & mask), )
        
        elif self.type == 'byte':
            if not 0 <= value <= 255:
                raise ValueError("value for 'byte' type should be in range of (0, 255)")
            old_value_mask = memory_instance.get_value(self.address) & (0b1111111100000000 >> self.byte_number*8)
            return ((value << self.byte_number*8) | old_value_mask, )
        
        elif self.type == 'word':
            if not 0 <= value <= 65535:
                raise ValueError("value for 'word' type should be in range of (0, 65535)")

            return (value, )
        
        elif self.type == 'uint32':
            if not 0 <= value <= 4294967295:
                raise ValueError("value for type 'uint32' should be in range of (0, 4294967295)")

            return (65535 & value, value >> 16)
    
    def get_memory_value(self, memory_instance):
        if not isinstance(memory_instance, MemoryStore):
            raise ValueError("memory_instance should be instance of MemoryStore")
        
        if self.type == 'bool':
            mask = 1 << self.bit_number
            return bool(mask & memory_instance.get_value(self.address))
        
        elif self.type == 'byte':
            mask = 0b11111111 << self.byte_number*8
            return (mask & memory_instance.get_value(self.address)) >> self.byte_number*8
        
        elif self.type == 'word':
            return memory_instance.get_value(self.address)
        
        elif self.type == 'uint32':
            lsw = memory_instance.get_value(self.address)
            msw = memory_instance.get_value(self.address + 1)
            return lsw | (msw << 16) 

class MemoryStore:
    def __init__(self, size):
        self._store = defaultdict(lambda: 0)
        self._size = size

    def get_value(self, address):
        if 0 > address > self._size:
            raise ValueError("Size exceeded")
        
        return self._store[address]
    
    def set_value(self, address, value):
        if 0 > address > self._size:
            raise ValueError("Size exceeded")
        self._store[address] = value

    def get_size(self):
        return self._size

    def __setattr__(self, name, value):
        # special care for MemoryVariable values
        if isinstance(value, MemoryVariable):
            # 1. Setting for the first time
            # check address
            if value.address*16 + MemoryVariable.type_sizes[value.type] > 16*self.get_size():
                raise ValueError("Address {} for type {} exceeds maximum memory size ({}B)".format(value.address, value.type, self.get_size()))

            # register
            self.__dict__[name] = value

        elif isinstance(self.__dict__.get(name, None), MemoryVariable):
            # 2. Setting existing memory_value
            # build value and take words from stack
            stack = self.__dict__[name].build_value_stack(value, self)
            for idx, word_value in enumerate(stack):
                self.set_value((self.__dict__[name].address + idx), word_value)

        else:
            # ordinary setting
            super().__setattr__(name, value)

    def __getattribute__(self, name):
        # special care for MemoryVariable values
        if isinstance(super().__getattribute__("__dict__").get(name, None), MemoryVariable):
            return self.__dict__[name].get_memory_value(self)
        
        else:
            # ordinary getting
            return super().__getattribute__(name)

    def dump(self, cols=5):
        leading = int(log10(self._size) + 1)
        fmt = "'{0:0" + str(leading) + "}': {1:05}"
        pairs = [fmt.format(key, value) for key, value in self._store.items()]
        out = ""
        for idx, pair in enumerate(pairs):
            out += pair + " | "
            if ((idx+1) % cols) == 0:
                out += "\n"
        out += "\n"
        return out