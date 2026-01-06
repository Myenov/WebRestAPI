import os
from WebRestAPI.requests import HTTPRequest
from WebRestAPI.response import HTTPResponse
from WebRestAPI.routes import Router
from WebRestAPI.server import APIServer
from WebRestAPI.configurate import APIConfiguration
from WebRestAPI.log import APIlog , FuncLog

__version__ = "0.0.2"


JSONResponse = HTTPResponse.JSONResponse
HTMLResponse = HTTPResponse.HTMLResponse

__all__ = [
    #API
    "APIServer","Router","APIConfiguration",

    #variable
    "__version__",

    #Request
    "HTTPRequest",

    #Response
    "HTTPResponse","JSONResponse","HTMLResponse",

    #log
    "APIlog","FuncLog",
]