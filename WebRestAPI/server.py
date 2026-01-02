from WebRestAPI.requests import HTTPRequest
from WebRestAPI.configurate import APIConfiguration
from WebRestAPI.exception_code import (
    InvalidIPversionError, InvalidProtocolError,
    InvalidUrlError
)
from WebRestAPI.log.log import Log
from WebRestAPI.response import HTTPResponse

import socket
import asyncio


class APIServer:
    def __init__(self, cfg: APIConfiguration):
        self.cfg: APIConfiguration = cfg
        self._socket = None
        self._url: dict = {}

    async def run(self):
        self._socket = socket.socket(
            family=self._is_valid_ip_version(),
            type=self._is_valid_protocol(),
            proto=self.cfg.protocol_number,
            fileno=self.cfg.fileno
        )
        self._load_urls()

        self._socket.bind((self.cfg.host, self.cfg.port))
        self._socket.listen(self.cfg.queue)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.setblocking(False)

        if self.cfg.debug:
            Log.debug(f"Server started on {self.cfg.host}:{self.cfg.port}")

        try:
            loop = asyncio.get_event_loop()

            while True:
                try:
                    client_socket, addr = await loop.sock_accept(self._socket)
                    if self.cfg.debug:
                        Log.debug(f"New connection from: {addr}")
                    asyncio.create_task(self.handle_client(client_socket, addr))
                except Exception as e:
                    if self.cfg.debug:
                        Log.error(f"Error accepting connection: {e}")
                    continue
        except KeyboardInterrupt:
            if self.cfg.debug:
                Log.debug("Server stopped by user")
        finally:
            self._socket.close()

    async def handle_client(self, client_socket, addr):
        try:
            loop = asyncio.get_event_loop()
            request_data = b''
            while True:
                try:
                    chunk = await loop.sock_recv(client_socket, 4096)
                    if not chunk:
                        break

                    request_data += chunk
                    if b'\r\n\r\n' in request_data:
                        headers_end = request_data.find(b'\r\n\r\n')
                        headers_part = request_data[:headers_end]
                        content_length = 0
                        headers_text = headers_part.decode('utf-8', errors='ignore')
                        for line in headers_text.split('\r\n'):
                            if line.lower().startswith('content-length:'):
                                try:
                                    content_length = int(line.split(':')[1].strip())
                                except:
                                    pass
                        body_start = headers_end + 4
                        if len(request_data) - body_start >= content_length:
                            break
                        else:
                            continue

                except ConnectionResetError:
                    break
                except asyncio.TimeoutError:
                    break
            if not request_data:
                client_socket.close()
                return
            if self.cfg.debug:
                Log.debug(f"Full request from {addr} ({len(request_data)} bytes)")
                Log.debug(f"Request start: {request_data[:200]}...")

            try:
                request = HTTPRequest(request_data)
                req = request.request_json
                if not req or 'method' not in req or 'path' not in req:
                    if self.cfg.debug:
                        Log.error(f"Invalid request from {addr}")
                    response = self._create_error_response(400, "Bad Request")
                else:
                    method = req.get("method", "").upper()
                    path = req.get("path", "")
                    if path == "/favicon.ico":
                        response = self._create_favicon_response()
                    else:
                        url_key = f"{method} {path}"
                        if self.cfg.debug:
                            Log.debug(f"Parsed request: {url_key}")
                        if url_key in self._url:
                            handler = self._url[url_key]
                            if asyncio.iscoroutinefunction(handler):
                                handler_result = await handler()
                            else:
                                handler_result = handler()
                            response = self._process_handler_result(handler_result)
                        else:
                            if self.cfg.debug:
                                Log.debug(f"Route not found: {url_key}")
                            response = self._create_error_response(404, f"Route {path} not found")
                await loop.sock_sendall(client_socket, response)
                headers_text = request_data.decode('utf-8', errors='ignore')
                connection_close = True

                for line in headers_text.split('\r\n'):
                    if line.lower().startswith('connection:'):
                        if 'keep-alive' in line.lower():
                            connection_close = False
                        break

                if connection_close:
                    client_socket.close()
                else:
                    client_socket.close()

            except Exception as e:
                if self.cfg.debug:
                    Log.error(f"Error processing request from {addr}: {e}")
                    import traceback
                    traceback.print_exc()
                error_response = self._create_error_response(500, "Internal Server Error")
                await loop.sock_sendall(client_socket, error_response)
                client_socket.close()

        except Exception as e:
            if self.cfg.debug:
                Log.error(f"Error with client {addr}: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass

    def _create_error_response(self, status_code: int, message: str = ""):
        status_phrases = {
            200: "OK",
            201: "Created",
            400: "Bad Request",
            404: "Not Found",
            500: "Internal Server Error",
        }

        status_text = status_phrases.get(status_code, "Unknown")
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{status_code} {status_text}</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                h1 {{ color: #333; }}
            </style>
        </head>
        <body>
            <div class="error">{status_code} {status_text}</div>
            <h1>{message}</h1>
            <p>WebRestAPI Server</p>
        </body>
        </html>
        """

        return HTTPResponse.build_response({
            'status_code': status_code,
            'status_text': status_text,
            'html': html_content
        })

    def _create_favicon_response(self):
        empty_favicon = (
            b'\x00\x00\x01\x00\x01\x00\x01\x01\x00\x00\x01\x00\x18\x00'
            b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        )

        return HTTPResponse.build_response({
            'status_code': 200,
            'status_text': 'OK',
            'headers': {
                'Content-Type': 'image/x-icon',
                'Content-Length': str(len(empty_favicon))
            },
            'body': empty_favicon
        })

    def _process_handler_result(self, result):
        if isinstance(result, bytes):
            return result
        elif isinstance(result, str):
            try:
                return result.encode('utf-8')
            except:
                return HTTPResponse.build_response({
                    'status_code': 200,
                    'status_text': 'OK',
                    'text': result
                })
        elif isinstance(result, dict):
            return HTTPResponse.build_response(result)
        else:
            return HTTPResponse.build_response({
                'status_code': 200,
                'status_text': 'OK',
                'text': str(result)
            })

    def _load_urls(self) -> None:
        if not self.cfg.routes:
            if self.cfg.debug:
                Log.debug("No routes configured")
            return

        for rout in self.cfg.routes:
            urls_dict = rout.get_urls()
            if not isinstance(urls_dict, dict):
                raise TypeError(f"Expected dict from get_urls(), got {type(urls_dict)}")
            for url_pattern, handler_func in urls_dict.items():
                if not isinstance(url_pattern, str):
                    raise TypeError(f"URL pattern must be string, got {type(url_pattern)}")
                parts = url_pattern.split(" ")
                if len(parts) < 2:
                    raise InvalidUrlError(f"Invalid URL format: {url_pattern}")

                if not callable(handler_func):
                    raise TypeError(f"Handler must be callable, got {type(handler_func)}")
                self._url[url_pattern] = handler_func

        if self.cfg.debug:
            Log.debug(f"Loaded {len(self._url)} URLs: {list(self._url.keys())}")

    def _is_valid_ip_version(self):
        if self.cfg.IPv == "IPv4":
            family = socket.AF_INET
        elif self.cfg.IPv == "IPv6":
            family = socket.AF_INET6
        elif self.cfg.IPv == "LOCALE":
            family = socket.AF_UNIX
        else:
            raise InvalidIPversionError()

        if self.cfg.debug:
            Log.debug(f"The selected internet protocol version is - {self.cfg.IPv}")

        return family

    def _is_valid_protocol(self):
        if self.cfg.protocol == "TCP":
            type_ = socket.SOCK_STREAM
        elif self.cfg.protocol == "UDP":
            type_ = socket.SOCK_DGRAM
        else:
            raise InvalidProtocolError()

        if self.cfg.debug:
            Log.debug(f"The selected data transfer protocol is - {self.cfg.protocol}")

        return type_