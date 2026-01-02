import os
from WebRestAPI.log import Log
from WebRestAPI.requests import HTTPRequest
from WebRestAPI.response import HTTPResponse
from WebRestAPI.routes import Router
from WebRestAPI.server import APIServer
from WebRestAPI.configurate import APIConfiguration

__version__ = "0.0.1"

__favicon_path__ = os.path.join(os.path.dirname(__file__), "favicon.png")
if not os.path.exists(__favicon_path__):
    Log.error(f"Warning: Favicon file not found at {__favicon_path__}")


__all__ = [
    "APIServer",
    "Router",
    "APIConfiguration",
    "__favicon_path__",
    "HTTPRequest",
    "HTTPResponse"
]