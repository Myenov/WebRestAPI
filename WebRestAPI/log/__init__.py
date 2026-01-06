from WebRestAPI.log.log import APIlog,error_l,log_l,debug_l

class FuncLog:
    info= APIlog.log
    log= APIlog.log
    information = APIlog.log
    debug = APIlog.debug
    bug = APIlog.debug
    err= APIlog.error
    error = APIlog.error
    errors = APIlog.error

__all__ = [
    "APIlog",
    "FuncLog",
    "error_l",
    "log_l",
    "debug_l",
]