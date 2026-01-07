import json
import urllib.parse
import re
from typing import Dict, Any, Optional


class HTTPRequest:
    def __init__(self, raw_request: bytes):
        self.raw = raw_request
        self.method = None
        self.path = None
        self.http_version = None
        self.headers = {}
        self.body = b''
        self.json_body = None
        self.form_data = {}
        self.files = {}
        self.query_params = {}
        self.path_params = {}
        self.request_json = self._parse_request(raw_request)

    def _parse_request(self, raw_request: bytes) -> Dict[str, Any]:
        try:
            if not raw_request:
                return {}

            header_end = raw_request.find(b'\r\n\r\n')
            if header_end == -1:
                return {}

            headers_part = raw_request[:header_end]
            self.body = raw_request[header_end + 4:]

            lines = headers_part.split(b'\r\n')
            if not lines:
                return {}

            request_line = lines[0].decode('utf-8', errors='ignore').strip()
            request_parts = request_line.split()

            if len(request_parts) >= 3:
                self.method = request_parts[0]
                self.path = request_parts[1]
                self.http_version = request_parts[2]
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

            if '?' in self.path:
                path_parts = self.path.split('?', 1)
                self.path = path_parts[0]
                if len(path_parts) > 1:
                    query_string = path_parts[1]
                    self.query_params = self._parse_query_string(query_string)

            if self.body:
                content_type = self.headers.get('content-type', '')
                if 'application/json' in content_type:
                    try:
                        body_text = self.body.decode('utf-8')
                        if body_text.strip():
                            self.json_body = json.loads(body_text)
                    except:
                        self.json_body = None
                elif 'application/x-www-form-urlencoded' in content_type:
                    try:
                        body_text = self.body.decode('utf-8')
                        self.form_data = self._parse_query_string(body_text)
                    except:
                        self.form_data = {}
                elif 'multipart/form-data' in content_type:
                    self._parse_multipart_form_data(content_type)

            return {
                'method': self.method,
                'path': self.path,
                'http_version': self.http_version,
                'headers': self.headers,
                'body': self.body.decode('utf-8', errors='ignore'),
                'json_body': self.json_body,
                'form_data': self.form_data,
                'files': self.files,
                'query_params': self.query_params,
                'path_params': self.path_params
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {}

    def _parse_query_string(self, query_string: str) -> Dict[str, str]:
        params = {}
        try:
            pairs = query_string.split('&')
            for pair in pairs:
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    key = urllib.parse.unquote(key)
                    value = urllib.parse.unquote(value)
                    params[key] = value
        except:
            pass
        return params

    def _parse_multipart_form_data(self, content_type: str):
        boundary_match = re.search(r'boundary=(.+)', content_type)
        if not boundary_match:
            return

        boundary = boundary_match.group(1).encode()
        parts = self.body.split(b'--' + boundary)

        for part in parts:
            if not part or part == b'--\r\n':
                continue

            headers_end = part.find(b'\r\n\r\n')
            if headers_end == -1:
                continue

            headers_part = part[:headers_end]
            content = part[headers_end + 4:-2]

            headers = {}
            for line in headers_part.split(b'\r\n'):
                line_str = line.decode('utf-8', errors='ignore')
                if ': ' in line_str:
                    key, value = line_str.split(': ', 1)
                    headers[key.lower()] = value

            content_disposition = headers.get('content-disposition', '')
            name_match = re.search(r'name="([^"]+)"', content_disposition)
            filename_match = re.search(r'filename="([^"]+)"', content_disposition)

            if name_match:
                name = name_match.group(1)
                if filename_match:
                    filename = filename_match.group(1)
                    self.files[name] = {
                        'filename': filename,
                        'content': content,
                        'content_type': headers.get('content-type', 'application/octet-stream'),
                        'size': len(content)
                    }
                else:
                    self.form_data[name] = content.decode('utf-8', errors='ignore')