from struct import Struct
import struct


class Message:

    # input: idx --> str, data --> byte, return --> byte
    def __init__(self, idx, data):
        self.idx = idx
        self.data = data
        self.format = Struct('!I4s%ds' % len(data))

    def to_bytes(self):
        byte_id = struct.pack('!4s', self.idx)
        data_len = struct.pack('!I', len(self.data))
        return data_len + byte_id + self.data

    def from_bytes(self, byte):
        [length, idx, data] = self.format.unpack(byte)
        print length, idx, data
        assert length == len(data)
        assert len(idx) == 4
        assert len(data) == len(self.data)
        return length, Message(idx, data)

    @classmethod
    def parse_stream(cls, byte):
        offset = 0
        messages = []
        while True:
            length, idx = struct.unpack('!I4s', byte[offset:offset + 8])
            data = byte[offset + 8:offset + 8 + length]
            messages.append(data)
            cls.map_id_msg(idx, data)
            offset += length + 8
            if offset >= len(byte):
                break
        return messages
        # return a list of unpacked messages
        # idx, data, buffer = Message.read_from(data)

    @classmethod
    def map_id_msg(cls, idx, data):
        messages = {}
        if idx in messages:
            messages[idx].append(data)
        else:
            messages[idx] = []
        return messages
