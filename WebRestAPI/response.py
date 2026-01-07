import json
import mimetypes
import os
from pathlib import Path
from typing import Union, Dict, Any, Optional
import WebRestAPI
from WebRestAPI.files.files import File, FileTypes


class HTTPResponse:
    def __init__(self, content=None, status_code: int = 200,
                 headers: Dict[str, str] = None, media_type: str = None):
        self.content = content
        self.status_code = status_code
        self.headers = headers or {}
        self.media_type = media_type

        if media_type and 'Content-Type' not in self.headers:
            self.headers['Content-Type'] = media_type

    def build(self) -> bytes:
        if isinstance(self.content, dict):
            body = json.dumps(self.content, ensure_ascii=False).encode('utf-8')
            if 'Content-Type' not in self.headers:
                self.headers['Content-Type'] = 'application/json'
        elif isinstance(self.content, str):
            body = self.content.encode('utf-8')
            if 'Content-Type' not in self.headers:
                self.headers['Content-Type'] = 'text/html; charset=utf-8'
        elif isinstance(self.content, bytes):
            body = self.content
        elif self.content is None:
            body = b''
        else:
            body = str(self.content).encode('utf-8')
            if 'Content-Type' not in self.headers:
                self.headers['Content-Type'] = 'text/plain'

        if 'Content-Length' not in self.headers:
            self.headers['Content-Length'] = str(len(body))

        if 'Server' not in self.headers:
            self.headers['Server'] = f'WebRestAPI/v{WebRestAPI.__version__}'

        if 'Connection' not in self.headers:
            self.headers['Connection'] = 'close'

        status_phrases = {
            200: "OK",
            201: "Created",
            400: "Bad Request",
            404: "Not Found",
            500: "Internal Server Error"
        }
        status_text = status_phrases.get(self.status_code, "Unknown")

        lines = [f"HTTP/1.1 {self.status_code} {status_text}"]
        for k, v in self.headers.items():
            lines.append(f"{k}: {v}")
        lines.append('\r\n')

        response_str = '\r\n'.join(lines)
        return response_str.encode('utf-8') + body

    @staticmethod
    async def FileResponseAsync(file_path: str, filename: str = None,
                                headers: Dict[str, str] = None,
                                download: bool = False,
                                file_type: Optional[FileTypes] = None) -> 'HTTPResponse':
        if headers is None:
            headers = {}

        if not os.path.exists(file_path):
            return HTTPResponse.HTMLResponse(
                "<h1>404 Not Found</h1><p>File not found</p>",
                status_code=404
            )

        if file_type is None:
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type:
                headers['Content-Type'] = mime_type
            else:
                headers['Content-Type'] = 'application/octet-stream'
        else:
            headers['Content-Type'] = file_type.mime_type

        if download:
            if not filename:
                filename = os.path.basename(file_path)
            headers['Content-Disposition'] = f'attachment; filename="{filename}"'

        content = await File.read(file_path, "rb")
        headers['Content-Length'] = str(len(content))

        return HTTPResponse(
            content=content,
            status_code=200,
            headers=headers
        )

    @staticmethod
    def FileResponse(file_path: str, filename: str = None,
                     headers: Dict[str, str] = None,
                     download: bool = False) -> 'HTTPResponse':
        import asyncio
        return asyncio.run(HTTPResponse.FileResponseAsync(file_path, filename, headers, download))

    @staticmethod
    def JSONResponse(content, status_code: int = 200, headers: Dict[str, str] = None):
        if headers is None:
            headers = {}

        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'

        return HTTPResponse(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type='application/json'
        )

    @staticmethod
    def HTMLResponse(content, status_code: int = 200, headers: Dict[str, str] = None):
        if headers is None:
            headers = {}

        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'text/html; charset=utf-8'

        return HTTPResponse(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type='text/html'
        )

    @staticmethod
    def PlainTextResponse(content, status_code: int = 200, headers: Dict[str, str] = None):
        if headers is None:
            headers = {}

        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'text/plain; charset=utf-8'

        return HTTPResponse(
            content=content,
            status_code=status_code,
            headers=headers,
            media_type='text/plain'
        )