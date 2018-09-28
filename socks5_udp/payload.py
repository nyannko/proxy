from pyipv8.ipv8.deprecated.payload import Payload


class ChallengeResponsePayload(Payload):
    """
    Check Identity of server or client
    """
    format_list = ['4s', 'raw']

    def __init__(self, message):
        super(ChallengeResponsePayload, self).__init__()
        self.message = message

    def to_pack_list(self):
        return [('raw', self.message)]

    @classmethod
    def from_unpack_list(cls, message):
        return cls(message)


class IdentityRequestPayload(Payload):
    """
    Check Identity of server or client
    """
    format_list = ['raw']

    def __init__(self, message):
        super(IdentityRequestPayload, self).__init__()
        self.message = message

    def to_pack_list(self):
        return [('raw', self.message)]

    @classmethod
    def from_unpack_list(cls, message):
        return cls(message)


class IdentityResponsePayload(Payload):
    """
    Check Identity of server or client
    """
    format_list = ['raw']

    def __init__(self, message):
        super(IdentityResponsePayload, self).__init__()
        self.message = message

    def to_pack_list(self):
        return [('raw', self.message)]

    @classmethod
    def from_unpack_list(cls, message):
        return cls(message)


class TargetAddressPayload(Payload):
    """
    Target IP address
    """
    format_list = ['raw']

    def __init__(self, message):
        super(TargetAddressPayload, self).__init__()
        self.message = message

    def to_pack_list(self):
        return [('raw', self.message)]

    @classmethod
    def from_unpack_list(cls, message):
        return cls(message)


class Message(Payload):
    format_list = ['4s', 'raw']

    def __init__(self, seq_id, message):
        self.seq_id = seq_id
        self.message = message

    def to_pack_list(self):
        data = [('4s', self.seq_id),
                ('raw', self.message)]
        return data

    @classmethod
    def from_unpack_list(cls, seq_id, message):
        return cls(seq_id, message)


# class Message(Payload):
#     format_list = ['H','raw']
#
#     def __init__(self, index, message):
#         self.index = index
#         self.message = message
#
#     def to_pack_list(self):
#         data = [('H', self.index), ('raw', self.message)]
#         return data
#
#     @classmethod
#     def from_unpack_list(cls, index, message):
#         return cls(index, message)

class PayoutPayload(Payload):
    """
    Check Identity of server or client
    """
    format_list = ['I']

    def __init__(self, message):
        super(PayoutPayload, self).__init__()
        self.message = message

    def to_pack_list(self):
        return [('I', self.message)]

    @classmethod
    def from_unpack_list(cls, message):
        return cls(message)
