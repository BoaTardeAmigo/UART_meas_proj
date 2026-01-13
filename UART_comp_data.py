import time
import struct

class UartData:
    def __init__(self, ser):
        self.ser = ser
    #Sends total file size header(4b)
    def send_initial_header(self, total_size):
        self.ser.write(struct.pack("<I", total_size))
        
    #Sends/receives data block being compressed
    def exchange_block(self, raw_chunk):       
        t_start = time.perf_counter()
        
        self.ser.write(raw_chunk)
        
        len_bytes = self.ser.read(2)
        if len(len_bytes) < 2:
            return None, 0
            
        (comp_len,) = struct.unpack("<H", len_bytes)
        payload = self.ser.read(comp_len)
        
        t_end = time.perf_counter()
        
        duration_us = (t_end - t_start) * 1_000_000
        
        return payload, duration_us