class HTTPRequest:
    def __init__(self, raw_request: bytes):
        self.raw = raw_request
        self.method = None
        self.path = None
        self.http_version = None
        self.headers = {}
        self.body = b''
        self.request_json = self._parse_request(raw_request)

    def _parse_request(self, raw_request: bytes) -> dict:
        try:
            if not raw_request:
                return {}
            header_end = raw_request.find(b'\r\n\r\n')
            if header_end == -1:
                return {}

            headers_part = raw_request[:header_end]
            body_part = raw_request[header_end + 4:]
            lines = headers_part.split(b'\r\n')
            if not lines:
                return {}
            request_line = lines[0].decode('utf-8', errors='ignore').strip()
            request_parts = request_line.split()

            if len(request_parts) >= 3:
                self.method = request_parts[0]
                self.path = request_parts[1]
                self.http_version = request_parts[2]
            elif len(request_parts) == 2:
                self.method = request_parts[0]
                self.path = request_parts[1]
                self.http_version = "HTTP/1.0"
            else:
                return {}
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue

                line_str = line.decode('utf-8', errors='ignore')
                if ': ' in line_str:
                    key, value = line_str.split(': ', 1)
                    self.headers[key.strip().lower()] = value.strip()
            self.body = body_part
            query_params = {}
            if '?' in self.path:
                path_parts = self.path.split('?', 1)
                self.path = path_parts[0]
                if len(path_parts) > 1:
                    query_string = path_parts[1]
                    params = query_string.split('&')
                    for param in params:
                        if '=' in param:
                            key, val = param.split('=', 1)
                            query_params[key] = val

            return {
                'method': self.method,
                'path': self.path,
                'http_version': self.http_version,
                'headers': self.headers,
                'body': self.body.decode('utf-8', errors='ignore'),
                'query_params': query_params
            }

        except Exception as e:
            print(f"Parse error: {e}")
            import traceback
            traceback.print_exc()
            return {}