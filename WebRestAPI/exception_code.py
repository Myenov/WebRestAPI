class InvalidIPversionError(Exception):
    def __init__(self, message="Error due to invalid IP version. Valid versions are IPv4, IPv6!"):
        self.message = message
        super().__init__(self.message)

class InvalidProtocolError(Exception):
    def __init__(self, message="Invalid protocol error. Valid protocols are UDP / TCP."):
        self.message = message
        super().__init__(self.message)

class InvalidUrlError(Exception):
    def __init__(self, message="Invalid URL in methods."):
        self.message = message
        super().__init__(self.message)