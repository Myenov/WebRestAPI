from WebRestAPI.routes import Router

class APIConfiguration:
    def __init__(self,
                 host: str = "localhost", port: int = 8000,queue: int = 15,
                 routes: list['Router'] = [] ,debug: bool = False,
                 IPversion: str = "IPv4" , protocol: str = "TCP",setblocking: bool = True,
                 protocol_number: int = 0, fileno: None = None,client_timeout: int = 30,
                 read_request_byte_size: int = 1024):

        self.host: str = host
        self.port: int = port
        self.routes: list['Router'] | None = routes
        self.read_request_byte_size: int = read_request_byte_size
        self.setblocking: bool = setblocking
        self.client_timeout: int = client_timeout
        self.protocol_number: int = protocol_number
        self.queue: int = queue
        self.IPv: str = IPversion
        self.protocol: str = protocol
        self.debug: bool = debug
        self.fileno = fileno

    def include_router(self, route: 'Router') -> None:
        self.routes.append(route)