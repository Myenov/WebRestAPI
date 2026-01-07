import asyncio
from WebRestAPI import HTTPResponse
from WebRestAPI.files.files import GetPathDirectory, File


class Favicon:
    def __init__(self , favicon_path: str = GetPathDirectory().directory.__str__() + "\\favicon.ico"):
        self.favicon_path = favicon_path
        self.favicon_data = b""
        self.response = None

    async def build(self):
        self.response = HTTPResponse(
            content=bytes(await File.read(self.favicon_path , "rb")),
            status_code=200,
            headers={
                'Content-Type': 'image/png',
                'Cache-Control': 'public, max-age=86400'
            }
        )
        return self.response

    def get_response(self):
        if self.response is not None:
            return self.response
        return None

    def __response__(self):
        return self.response

