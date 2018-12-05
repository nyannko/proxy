import base64
import hashlib
import struct
from struct import Struct


class Message:

    def __init__(self, cir_id, msg_type, data):
        self.cir_id = cir_id
        self.data = data
        self.msg_type = msg_type  # used for distinguish from address and data
        # self.format = Struct('!I4s4s%ds' % len(data))

    def encryption(self, plain_text):
        encrypted_message = base64.b64encode(plain_text)
        return encrypted_message

    @classmethod
    def decryption(cls, encrypted_message):
        plain_text = base64.b64decode(encrypted_message)
        return plain_text

    def to_bytes(self):
        """
        Convert Message to str(bytes)
        :return: str(bytes)
        """
        # data = self.encryption(self.data)
        data = self.encryption(self.data)
        cir_id = struct.pack('!I', self.cir_id)
        data_len = struct.pack('!I', len(data))
        msg_type = struct.pack('!4s', self.msg_type)
        return data_len + cir_id + msg_type + data

    def from_bytes(self, byte):
        """
        Verify message integrity
        :param byte: str
        :return: Message
        """
        [cir_id, length, idx, msg_type, data] = self.format.unpack(byte)
        assert length == len(data)
        assert len(cir_id) == 32
        assert len(msg_type) == 4
        assert len(idx) == 4
        assert len(data) == len(self.data)
        return length, Message(cir_id, idx, msg_type, data)

    @classmethod
    def parse_stream(cls, byte):
        """
        :param byte: str(bytes)
        :return: List[Message], str(bytes)
        """
        offset = 0
        prefix = 12  # (4 data_len + 4 cir_id + 4 msg_type)
        messages = []
        data_remaining = b''
        while True:
            try:
                length, idx, msg_type = struct.unpack('!II4s', byte[offset:offset + 12])
                print "length", length, idx, msg_type
            except struct.error as e:
                print "unpack requires a string argument of length 12: ", e.message
                data_remaining = byte[offset:]
                break

            expected_data_length = offset + prefix + length
            if expected_data_length > len(byte):
                data_remaining = byte[offset:]
                break
            data = byte[offset + prefix:expected_data_length]
            print "before decode", data[:20]
            data = cls.decryption(data)
            print "decode_data", data[:20]
            messages.append(cls(idx, msg_type, data))  # append Message(idx, data, msg_type) to message queue

            offset = expected_data_length
            if offset == len(byte):
                break
        return messages, data_remaining
