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
    format_list = ['4s', '4s', 'raw']

    def __init__(self, proto_id, seq_id, message):
        self.proto_id = proto_id
        self.seq_id = seq_id
        self.message = message

    def to_pack_list(self):
        data = [('4s', self.proto_id),
                ('4s', self.seq_id),
                ('raw', self.message)]
        return data

    @classmethod
    def from_unpack_list(cls, proto_id, seq_id, message):
        return cls(proto_id, seq_id, message)


class Message(Payload):
    format_list = ['4s', '4s', 'raw']

    def __init__(self, proto_id, seq_id, message):
        self.proto_id = proto_id
        self.seq_id = seq_id
        self.message = message

    def to_pack_list(self):
        data = [('4s', self.proto_id),
                ('4s', self.seq_id),
                ('raw', self.message)]
        return data

    @classmethod
    def from_unpack_list(cls, proto_id, seq_id, message):
        return cls(proto_id, seq_id, message)


class ACKPayload(Payload):
    format_list = ['4s', '4s']

    def __init__(self, proto_id, seq_id):
        self.proto_id = proto_id
        self.seq_id = seq_id

    def to_pack_list(self):
        data = [('4s', self.proto_id),
                ('4s', self.seq_id)]
        return data

    @classmethod
    def from_unpack_list(cls, proto_id, seq_id):
        return cls(proto_id, seq_id)


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
