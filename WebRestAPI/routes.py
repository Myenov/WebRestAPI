import functools


class Router:
    def __init__(self, prefix: str = "/"):
        self._prefix: str = prefix.rstrip('')
        self._urls: dict = {}

    def _build_url(self, method: str, url: str) -> str:
        url = url.lstrip('/')
        full_path = f"{self._prefix}/{url}" if url else self._prefix
        full_path = full_path.replace('//', '/')
        return f"{method.upper()} {full_path}"

    def post(self, url: str):
        def decorator(func):
            self._urls[self._build_url("POST", url)] = func
            return func

        return decorator

    def get(self, url: str):
        def decorator(func):
            self._urls[self._build_url("GET", url)] = func
            return func

        return decorator

    def delete(self, url: str):
        def decorator(func):
            self._urls[self._build_url("DELETE", url)] = func
            return func

        return decorator

    def patch(self, url: str):
        def decorator(func):
            self._urls[self._build_url("PATCH", url)] = func
            return func

        return decorator

    def put(self, url: str):
        def decorator(func):
            self._urls[self._build_url("PUT", url)] = func
            return func

        return decorator

    def get_urls(self) -> dict:
        return self._urls