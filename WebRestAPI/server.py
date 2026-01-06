from WebRestAPI.requests import HTTPRequest
from WebRestAPI.configurate import APIConfiguration
from WebRestAPI.response import HTTPResponse
from WebRestAPI.log.log import APIlog

import socket
import asyncio
import sys


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
            self._socket.bind((self.cfg.host, self.cfg.port))
            self._socket.listen(self.cfg.queue)

            APIlog.log(f"Socket bound to {self.cfg.host}:{self.cfg.port}")

        except OSError as e:
            APIlog.error(f"Error binding to {self.cfg.host}:{self.cfg.port}: {e}")
            return

        self._load_routes()

        APIlog.log(f"Server started on http://{self.cfg.host}:{self.cfg.port}")

        if sys.platform == "win32":
            await self._run_windows()
        else:
            await self._run_unix()

    async def _run_windows(self):
        self._running = True
        self._socket.setblocking(False)

        while self._running:
            try:
                client_socket, addr = self._socket.accept()
                client_socket.setblocking(False)
                asyncio.create_task(self._handle_client(client_socket, addr))
            except BlockingIOError:
                await asyncio.sleep(0.01)
            except KeyboardInterrupt:
                break
            except Exception as e:
                APIlog.error(f"Accept error: {e}")
                await asyncio.sleep(0.1)

        self._running = False
        if self._socket:
            self._socket.close()

    async def _run_unix(self):
        self._socket.setblocking(False)
        self._running = True
        loop = asyncio.get_event_loop()

        while self._running:
            try:
                client_socket, addr = await loop.sock_accept(self._socket)
                client_socket.setblocking(False)
                asyncio.create_task(self._handle_client(client_socket, addr))
            except BlockingIOError:
                await asyncio.sleep(0.01)
            except KeyboardInterrupt:
                break
            except Exception as e:
                APIlog.error(f"Accept error: {e}")
                await asyncio.sleep(0.1)

        self._running = False
        if self._socket:
            self._socket.close()

    async def _handle_client(self, client_socket, addr):
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
                        break
                except BlockingIOError:
                    if request_data:
                        break
                    await asyncio.sleep(0.001)
                    continue
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

    async def _process_request(self, request_data):
        try:
            request = HTTPRequest(request_data)
            req = request.request_json

            if not req:
                return HTTPResponse.PlainTextResponse("Bad Request", status_code=400).build()

            method = req.get("method", "").upper()
            path = req.get("path", "")

            APIlog.debug(f"Processing {method} {path}")

            if path == "/favicon.ico":
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
        favicon_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x02\x00\x00\x00\x90\x91h6\x00\x00\x00\x19IDATx\x9cc\xf8\xcf\x00\x05\x8c\x0c\x0c\x0c\x8c\x8c\x8c\x0c\x0c\x0c\x0c\x0c\x0c\x8c\x0c\x18\x00\x00\x00\xff\xff\x03\x00\xb4\x9f\x05\xf6\x00\x00\x00\x00IEND\xaeB`\x82'

        response = HTTPResponse(
            content=favicon_data,
            status_code=200,
            headers={
                'Content-Type': 'image/png',
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