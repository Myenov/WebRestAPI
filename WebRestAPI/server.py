from pathlib import Path
from WebRestAPI.requests import HTTPRequest
from WebRestAPI.configurate import APIConfiguration
from WebRestAPI.response import HTTPResponse
from WebRestAPI.log.log import APIlog
from WebRestAPI.files.files import File, FileTypes

import socket
import asyncio
import sys
import time


class APIServer:
    def __init__(self, cfg: APIConfiguration):
        self.cfg = cfg
        self._socket = None
        self._routes = {}
        self._path_routes = []
        self._running = False

    async def run(self):
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.setblocking(self.cfg.setblocking)
            self._socket.bind((self.cfg.host, self.cfg.port))
            self._socket.listen(self.cfg.queue)

            APIlog.log(f"Server bound to {self.cfg.host}:{self.cfg.port}")

        except OSError as e:
            APIlog.error(f"Error binding to {self.cfg.host}:{self.cfg.port}: {e}")
            return

        self._load_routes()
        APIlog.log(f"Server started on http://{self.cfg.host}:{self.cfg.port}")
        self._running = True

        try:
            while self._running:
                try:
                    if self.cfg.setblocking:
                        client_socket, addr = self._socket.accept()
                    else:
                        try:
                            client_socket, addr = self._socket.accept()
                        except BlockingIOError:
                            await asyncio.sleep(0.01)
                            continue

                    client_socket.settimeout(self.cfg.client_timeout)
                    client_socket.setblocking(False)
                    asyncio.create_task(self._handle_client(client_socket, addr))

                except socket.timeout:
                    continue
                except OSError as e:
                    if e.errno == socket.EBADF:
                        break
                    await asyncio.sleep(0.1)
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    APIlog.error(f"Accept error: {e}")
                    await asyncio.sleep(0.1)

        except KeyboardInterrupt:
            APIlog.log("Server stopped by user")
        finally:
            self._running = False
            if self._socket:
                self._socket.close()

    async def _handle_client(self, client_socket, addr):
        try:
            loop = asyncio.get_event_loop()
            request_data = b''
            start_time = time.time()

            while time.time() - start_time < self.cfg.client_timeout:
                try:
                    chunk = await loop.sock_recv(client_socket, self.cfg.read_request_byte_size)
                    if not chunk:
                        break
                    request_data += chunk
                    if b'\r\n\r\n' in request_data:
                        content_length = self._get_content_length(request_data)
                        body_start = request_data.find(b'\r\n\r\n') + 4
                        if len(request_data) >= body_start + content_length:
                            break
                except BlockingIOError:
                    if request_data:
                        break
                    await asyncio.sleep(0.001)
                except socket.timeout:
                    break
                except Exception as e:
                    break

            if not request_data:
                client_socket.close()
                return

            APIlog.debug(f"Received {len(request_data)} bytes from {addr}")
            response_data = await self._process_request(request_data)

            if response_data:
                try:
                    total_sent = 0
                    while total_sent < len(response_data):
                        sent = client_socket.send(response_data[total_sent:])
                        if sent == 0:
                            break
                        total_sent += sent
                    APIlog.debug(f"Sent {total_sent} bytes to {addr}")
                except Exception as e:
                    APIlog.error(f"Send error to {addr}: {e}")

        except Exception as e:
            APIlog.error(f"Client error: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass

    def _get_content_length(self, request_data: bytes) -> int:
        try:
            headers_part = request_data.split(b'\r\n\r\n')[0]
            lines = headers_part.split(b'\r\n')
            for line in lines:
                if line.lower().startswith(b'content-length:'):
                    return int(line.split(b':')[1].strip())
        except:
            pass
        return 0

    async def _process_request(self, request_data):
        try:
            request = HTTPRequest(request_data)
            req = request.request_json

            if not req:
                return HTTPResponse.PlainTextResponse("Bad Request", status_code=400).build()

            method = req.get("method", "").upper()
            path = req.get("path", "")

            APIlog.debug(f"Processing {method} {path}")

            if not self.cfg.user_favicon and path == "/favicon.ico":
                return await self._handle_favicon()

            route_key = f"{method} {path}"
            route_info = None
            path_params = {}

            if route_key in self._routes:
                route_info = self._routes[route_key]
            else:
                for pattern_info in self._path_routes:
                    if pattern_info['method'] == method:
                        match = pattern_info['pattern'].match(path)
                        if match:
                            route_info = pattern_info
                            path_params = match.groupdict()
                            req['path_params'] = path_params
                            break

            if not route_info:
                return HTTPResponse.HTMLResponse(
                    f"<h1>404 Not Found</h1><p>Route {path} not found</p>",
                    status_code=404
                ).build()

            handler = route_info['handler']
            response = await handler(request)

            if isinstance(response, HTTPResponse):
                return response.build()
            elif isinstance(response, dict):
                return HTTPResponse.JSONResponse(response).build()
            elif isinstance(response, str):
                return HTTPResponse.HTMLResponse(response).build()
            else:
                return HTTPResponse.JSONResponse({"result": response}).build()

        except Exception as e:
            APIlog.error(f"Process error: {e}")
            import traceback
            traceback.print_exc()
            return HTTPResponse.JSONResponse(
                {"error": "Internal Server Error"},
                status_code=500
            ).build()

    async def _handle_favicon(self):
        favicon_path = Path(__file__).resolve().parent / "favicon.ico"

        try:
            favicon_data = await File.read(str(favicon_path), "rb")
        except:
            favicon_data = b''

        response = HTTPResponse(
            content=favicon_data,
            status_code=200,
            headers={
                'Content-Type': 'image/x-icon',
                'Cache-Control': 'public, max-age=86400'
            }
        )
        return response.build()

    def _load_routes(self):
        if not self.cfg.routes:
            return

        for router in self.cfg.routes:
            routes_dict = router.get_urls()
            self._routes.update(routes_dict)

            path_patterns = router.get_path_patterns()
            self._path_routes.extend(path_patterns)

        APIlog.log(f"Loaded {len(self._routes)} route(s) and {len(self._path_routes)} path route(s)")

        if self.cfg.debug:
            APIlog.debug("Available routes:")
            for route in sorted(self._routes.keys()):
                APIlog.debug(f"  • {route}")
            for pattern in self._path_routes:
                APIlog.debug(f"  • {pattern['method']} {pattern['path']}")