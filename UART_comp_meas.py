import struct
import time

class UartMeas:
    def __init__(self, ser):
        self.ser = ser
        self.fmt = "<IIIII" 
        self.rec_size = struct.calcsize(self.fmt)

    def fetch_and_parse(self):
        start = time.time()
        found = False
        while time.time() - start < 5:
            if self.ser.read(1) == b'\xa5':
                if self.ser.read(1) == b'\x5a':
                    found = True
                    break
        if not found: return []

        # Assuming header format [0xA5, 0x5A, Type, Len_low, Len_high]
        header = self.ser.read(3)
        msg_type = header[0]
        payload_len = struct.unpack("<H", header[1:3])[0]

        if msg_type != 1: return []

        raw_payload = self.ser.read(payload_len)
        results = []
        
        for i in range(0, payload_len, self.rec_size):
            chunk = raw_payload[i : i + self.rec_size]
            if len(chunk) < self.rec_size: break
            
            d = struct.unpack(self.fmt, chunk)
            
            in_len, out_len, comp_us = d[1], d[2], d[3]
            results.append({
                "block_id": d[0],
                "in_len": in_len,
                "out_len": out_len,
                "ratio": out_len / in_len if in_len > 0 else 0,
                "efficiency": (in_len - out_len) / comp_us if comp_us > 0 else 0,
                "comp_us": comp_us,
                "tx_us": d[4]
            })
        return results