from socketserver import TCPServer
from umodbus import conf
from umodbus.server.tcp import RequestHandler, get_server
import socket
from umodbus.client import tcp
import threading
from copy import deepcopy
from time import sleep, time
from ModbusSharedMemory.memory import MemoryStore
from datetime import datetime


class ModbusSlaveTCP:
    TCPServer.allow_reuse_address = True

    def __init__(self, memory_store, server_ip='localhost', slave_id=1, sync_period=0.05):
        if not isinstance(memory_store, MemoryStore):
            raise ValueError("memory_store should be instance of MemoryStore")

        self.app = get_server(TCPServer, (server_ip, 502), RequestHandler)
        self.memory = memory_store
        self.sync_period = sync_period

        read_hr_routing = self.app.route(slave_ids=[slave_id], function_codes=[3], addresses=list(range(self.memory.get_size())))
        self.read_holding_reg = read_hr_routing(self.read_holding_reg)
        
        write_hr_routing = self.app.route(slave_ids=[slave_id], function_codes=[6, 16], addresses=list(range(self.memory.get_size())))
        self.write_holding_reg = write_hr_routing(self.write_holding_reg)

    def read_holding_reg(self, slave_id, function_code, address):
        return self.memory.get_value(address)

    def write_holding_reg(self, slave_id, function_code, address, value):
        self.memory.set_value(address, value)

    def _start(self):
        try:
            self.app.serve_forever(self.sync_period)
        except ConnectionResetError:
            pass
        finally:
            self.app.shutdown()
            self.app.server_close()

    def kill(self):
        self.app.shutdown()
        self.app.server_close()

    def run(self):
        th = threading.Thread(group=None, target=self._start, daemon=True)
        th.start()


class ModbusMasterTCP:

    def __init__(self, memory_store, server_ip='localhost', default_slave_id=1, sync_period=0.2):
        if not isinstance(memory_store, MemoryStore):
            raise ValueError("memory_store should be instance of MemoryStore")

        self.memory = memory_store
        self.buffered_memory = deepcopy(self.memory)
        self.default_slave_id = default_slave_id
        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
        self.server_ip = server_ip
        self.socket.connect((self.server_ip, 502))
        self.keep_running = False
        self.sync_period = sync_period

    def write_holding_reg(self, address, value, slave_id=None):
        slv_id = self.default_slave_id if slave_id is None else slave_id
        request_adu = tcp.write_single_register(slv_id, address, value)
        tcp.send_message(request_adu, self.socket)

    def read_holding_reg(self, address, slave_id=None):
        slv_id = self.default_slave_id if slave_id is None else slave_id
        request_adu = tcp.read_holding_registers(slv_id, address, 1)
        response = tcp.send_message(request_adu, self.socket)
        
        return response[0]

    def write_multiple_reg(self, starting_addr, values, slave_id=None):
        slv_id = self.default_slave_id if slave_id is None else slave_id
        for starting_idx, ending_idx in self.get_chunk_indices(values, 123): 
            request_adu = tcp.write_multiple_registers(slv_id, starting_addr + starting_idx, values[starting_idx:ending_idx + 1])
            try:
                tcp.send_message(request_adu, self.socket)
            except Exception as e:
                print(len(values[starting_idx:ending_idx + 1]), starting_idx, ending_idx)
                raise e


    def read_multiple_reg(self, starting_addr, count, slave_id=None):
        slv_id = self.default_slave_id if slave_id is None else slave_id
        
        response = [None] * count
        for starting_idx, ending_idx in self.get_chunk_indices(range(count), 125):
            try:
                request_adu = tcp.read_holding_registers(slv_id, starting_idx, ending_idx-starting_idx+1)
            except:
                print(count)
            response[starting_idx:ending_idx+1] = tcp.send_message(request_adu, self.socket)

        return response

    def do_map2(self, slave_id=None):
        slv_id = self.default_slave_id if slave_id is None else slave_id
        server_data = self.read_multiple_reg(0, self.memory.get_size())
        memory_data = [self.memory.get_value(i) for i in range(self.memory.get_size())]
        buffer_data = [self.buffered_memory.get_value(i) for i in range(self.buffered_memory.get_size())]

        outgoing_data = server_data.copy()

        for i in range(self.memory.get_size()):
            mem_value = memory_data[i]
            server_value = server_data[i]
            buf_value = buffer_data[i]

            # make decision
            if server_value != mem_value and mem_value != buf_value and server_value != buf_value:
                # conflict, server and client updated same value
                # shift memory, update memory
                self.buffered_memory.set_value(i, mem_value)
                self.memory.set_value(i, server_value)
            elif server_value != mem_value and mem_value == buf_value:
                # no conflict, server updated, client did not
                # read from server
                self.buffered_memory.set_value(i, server_value)
                self.memory.set_value(i, server_value)
            elif server_value == buf_value and mem_value != buf_value:
                # no conflict, client updated, server did not
                # write to the server
                self.buffered_memory.set_value(i, mem_value)
                outgoing_data[i] = mem_value

        # send
        self.write_multiple_reg(0, outgoing_data, slv_id)       

    def do_map(self, slave_id=None):
        slv_id = self.default_slave_id if slave_id is None else slave_id
        # first write, then read
        for i in range(self.memory.get_size()):
            # server has higher priority in updatyng memory state
            # in case of coflict, server updates
            buf_value = self.buffered_memory.get_value(i)
            mem_value = self.memory.get_value(i)
            server_value = self.read_holding_reg(i, slv_id)

            # make decision
            if server_value != mem_value and mem_value != buf_value and server_value != buf_value:
                # conflict, server and client updated same value
                # shift memory, update memory
                self.buffered_memory.set_value(i, mem_value)
                self.memory.set_value(i, server_value)
            elif server_value != mem_value and mem_value == buf_value:
                # no conflict, server updated, client did not
                # read from server
                self.buffered_memory.set_value(i, server_value)
                self.memory.set_value(i, server_value)
            elif server_value == buf_value and mem_value != buf_value:
                # no conflict, client updated, server did not
                # write to the server
                self.buffered_memory.set_value(i, mem_value)
                self.write_holding_reg(i, mem_value)

    @staticmethod
    def get_chunk_indices(table, chunk_size):
        t_len = len(table)
        last_idx = min(t_len, chunk_size) - 1
        yield (0, last_idx)
        while True:
            last_idx = last_idx + chunk_size
            if last_idx >= t_len:
                yield (last_idx - chunk_size + 1, t_len - 1)
                raise StopIteration
            else:
                yield (last_idx - chunk_size + 1, last_idx)

    def _log(self, message):
        with open("client_log.log", "a") as f:
            f.write("{0}:\t{1}\n".format(datetime.now().strftime("%x %X"), message))

    def _start(self):
        # should be started in another thread
        self.keep_running = True
        try:
            while self.keep_running:
                t0 = time()
                self.do_map2()
                t1 = time()
                try:
                    sleep(self.sync_period-(t1-t0))
                except ValueError:
                    self._log("Sync period exceeded. Data transfer takes longer [{}s] than required synchronization time [{}s]. Consider truncating memory or elongating sync_period." \
                        .format((t1-t0), self.sync_period))

        except ConnectionResetError:
            pass
        finally:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
    
    def kill(self):
        self.keep_running = False
    
    def run(self):
        th = threading.Thread(group=None, target=self._start, daemon=True)
        th.start()
            
