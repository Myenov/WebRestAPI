import asyncio
import sys
import enum
from pathlib import Path
from WebRestAPI.log.log import APIlog


class FileTypes(enum.Enum):
    HTML = ("text/html", "html")
    CSS = ("text/css" , "css")
    JS = ("application/javascript" , "js")
    JPEG = ("image/jpeg" , "jpeg")
    PNG = ("image/png" , "png")
    GIF = ("image/gif" , "gif")
    MP4 = ("video/mp4" , "mp4")
    WEBM = ("video/webm" , "webm")
    PDF = ("application/pdf" , "pdf")
    AUDIO = ("audio/mp3", "mp3")
    JSON = ("application/json" , "json")

    @property
    def mime_type(self):
        if isinstance(self.value, tuple):
            return self.value[0]
        return self.value

    @property
    def extension(self):
        if isinstance(self.value, tuple):
            return self.value[1]
        return None

class GetPathDirectory:
    def __init__(self):
        if getattr(sys, 'frozen', False):
            self.directory = Path(sys.executable).parent.__str__()
        else:
            self.directory = Path(sys.argv[0]).resolve().parent.__str__()

    def __str__(self):
        return self.directory

class FilePath:
    def __init__(self, debug: bool = False):
        self._list_path: dict[str , str] = {}
        self.debug = debug

    async def add_path(self, filename: str, path: str = GetPathDirectory().directory) -> dict[str , str]:
        self._list_path[filename] = path + "\\" + filename
        util_dict = {filename: self._list_path[filename]}
        if self.debug:
            APIlog.debug(f"New FilePath! Path = {util_dict.__str__()}")
        return util_dict

    def __str__(self) -> str:
        return self._list_path.__str__()

    def __dict__(self) -> dict[str , str]:
        return self._list_path


class StaticFilePath:
    def __init__(self, directory: str = GetPathDirectory().directory + "\\static", debug: bool = False):
        self.path = directory
        if debug:
            APIlog.debug(f"New static path. {self.path=}")

    def __str__(self):
        return self.path

class TemplateFilePath:
    def __init__(self, directory: str = GetPathDirectory().directory + "\\template", debug: bool = False):
        self.path =  directory
        if debug:
            APIlog.debug(f"New static path. {self.path=}")

    def __str__(self):
        return self.path

class File:
    def __init__(self, filepath: str , types: FileTypes , to_thread: bool = True):
        self.filepath = filepath
        self.types = types
        self._to_thread = to_thread


    @staticmethod
    async def read(path: str , flag: str = "r"):
        def read_sync(path_file: str):
            with open(file = path_file , mode = flag) as f:
                return f.read()
        loop = asyncio.get_running_loop()
        content = await loop.run_in_executor(
            None,
            read_sync,
            path
        )
        return content


