from pyipv8.ipv8.deprecated.payload import Payload


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
    format_list = ['raw']

    def __init__(self, message):
        self.message = message

    def to_pack_list(self):
        return [('raw', self.message)]

    @classmethod
    def from_unpack_list(cls, message):
        return cls(message)

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
