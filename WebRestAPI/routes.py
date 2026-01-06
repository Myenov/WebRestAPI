import re
import inspect
import functools

from WebRestAPI import HTTPResponse


class Router:
    def __init__(self, prefix: str = "/"):
        self._prefix: str = prefix.rstrip('/')
        self._routes: dict = {}
        self._path_patterns: list = []

    def _build_full_path(self, url: str) -> str:
        url = url.lstrip('/')
        if self._prefix and self._prefix != "/":
            if url:
                return f"{self._prefix}/{url}"
            else:
                return self._prefix
        else:
            if url:
                return f"/{url}"
            else:
                return "/"

    def _parse_path_pattern(self, path: str):
        pattern = re.sub(r'\{(\w+)\}', r'(?P<\1>[^/]+)', path)
        return re.compile(f'^{pattern}$')

    def _create_handler_wrapper(self, func, method: str, path: str):
        sig = inspect.signature(func)
        param_names = list(sig.parameters.keys())

        @functools.wraps(func)
        async def wrapper(request):
            kwargs = {}
            request_data = getattr(request, 'request_json', {})

            query_params = request_data.get('query_params', {})
            json_body = request_data.get('json_body', {})
            form_data = request_data.get('form_data', {})
            path_params = request_data.get('path_params', {})

            all_params = {}
            if query_params:
                all_params.update(query_params)
            if json_body:
                all_params.update(json_body)
            if form_data:
                all_params.update(form_data)
            if path_params:
                all_params.update(path_params)

            for param_name in param_names:
                if param_name == 'request':
                    kwargs['request'] = request
                    continue

                if param_name in all_params:
                    param_value = all_params[param_name]
                elif param_name in sig.parameters:
                    param = sig.parameters[param_name]
                    if param.default != inspect.Parameter.empty:
                        param_value = param.default
                    else:
                        continue
                else:
                    continue

                if param_name in func.__annotations__:
                    annotation = func.__annotations__[param_name]
                    try:
                        if annotation == int:
                            param_value = int(param_value)
                        elif annotation == float:
                            param_value = float(param_value)
                        elif annotation == bool:
                            if isinstance(param_value, str):
                                param_value = param_value.lower() in ['true', '1', 'yes', 'on']
                            else:
                                param_value = bool(param_value)
                    except:
                        pass

                kwargs[param_name] = param_value

            result = await func(**kwargs)
            return result

        return wrapper

    def get(self, url: str):
        def decorator(func):
            full_path = self._build_full_path(url)
            wrapper = self._create_handler_wrapper(func, "GET", full_path)

            if '{' in full_path:
                self._path_patterns.append({
                    'pattern': self._parse_path_pattern(full_path),
                    'handler': wrapper,
                    'original': func,
                    'method': 'GET',
                    'path': full_path
                })
            else:
                route_key = f"GET {full_path}"
                self._routes[route_key] = {
                    'handler': wrapper,
                    'original': func,
                    'method': 'GET',
                    'path': full_path
                }
            return wrapper

        return decorator

    def post(self, url: str):
        def decorator(func):
            full_path = self._build_full_path(url)
            wrapper = self._create_handler_wrapper(func, "POST", full_path)

            if '{' in full_path:
                self._path_patterns.append({
                    'pattern': self._parse_path_pattern(full_path),
                    'handler': wrapper,
                    'original': func,
                    'method': 'POST',
                    'path': full_path
                })
            else:
                route_key = f"POST {full_path}"
                self._routes[route_key] = {
                    'handler': wrapper,
                    'original': func,
                    'method': 'POST',
                    'path': full_path
                }
            return wrapper

        return decorator

    def delete(self, url: str):
        def decorator(func):
            full_path = self._build_full_path(url)
            wrapper = self._create_handler_wrapper(func, "DELETE", full_path)

            if '{' in full_path:
                self._path_patterns.append({
                    'pattern': self._parse_path_pattern(full_path),
                    'handler': wrapper,
                    'original': func,
                    'method': 'DELETE',
                    'path': full_path
                })
            else:
                route_key = f"DELETE {full_path}"
                self._routes[route_key] = {
                    'handler': wrapper,
                    'original': func,
                    'method': 'DELETE',
                    'path': full_path
                }
            return wrapper

        return decorator

    def put(self, url: str):
        def decorator(func):
            full_path = self._build_full_path(url)
            wrapper = self._create_handler_wrapper(func, "PUT", full_path)

            if '{' in full_path:
                self._path_patterns.append({
                    'pattern': self._parse_path_pattern(full_path),
                    'handler': wrapper,
                    'original': func,
                    'method': 'PUT',
                    'path': full_path
                })
            else:
                route_key = f"PUT {full_path}"
                self._routes[route_key] = {
                    'handler': wrapper,
                    'original': func,
                    'method': 'PUT',
                    'path': full_path
                }
            return wrapper

        return decorator

    def patch(self, url: str):
        def decorator(func):
            full_path = self._build_full_path(url)
            wrapper = self._create_handler_wrapper(func, "PATCH", full_path)

            if '{' in full_path:
                self._path_patterns.append({
                    'pattern': self._parse_path_pattern(full_path),
                    'handler': wrapper,
                    'original': func,
                    'method': 'PATCH',
                    'path': full_path
                })
            else:
                route_key = f"PATCH {full_path}"
                self._routes[route_key] = {
                    'handler': wrapper,
                    'original': func,
                    'method': 'PATCH',
                    'path': full_path
                }
            return wrapper

        return decorator

    def get_urls(self) -> dict:
        return self._routes

    def get_path_patterns(self) -> list:
        return self._path_patterns