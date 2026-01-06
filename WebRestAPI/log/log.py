from datetime import datetime

from WebRestAPI.template_string.template import Template

error_l: list[int] = [31, 40, 1]
log_l: list[int] = [37, 40, 1]
debug_l: list[int] = [33, 40, 1]




class APIlog:
    @staticmethod
    def BasicConfig(error: list[int] | None = None,
                    log: list[int] | None = None,
                    debug: list[int] | None = None):
        global error_l, log_l, debug_l
        if error is not None:
            error_l = error
        if log_l is not None:
            log_l = log
        if debug_l is not None:
            debug_l = debug

    @staticmethod
    def error(text: str):
        now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        print(Template("$CODE $TIME <= $text").connect(
            {"CODE": "\033[" + str(error_l[2]) + ";" + str(error_l[0]) + ";" + str(error_l[1]) + "m", "TIME": now,
             "text": text}
        ))

    @staticmethod
    def log(text: str):
        now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        print(Template("$CODE $TIME <= $text").connect(
            {"CODE": "\033[" + str(log_l[2]) + ";" + str(log_l[0]) + ";" + str(log_l[1]) + "m",
             "TIME": now, "text": text}
        ))

    @staticmethod
    def debug(text: str):
        now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        print(Template("$CODE[DEBUG] $TIME <= $text").connect(
            {"CODE": "\033[" + str(debug_l[2]) + ";" + str(debug_l[0]) + ";" + str(debug_l[1]) + "m",
             "TIME": now, "text": text}
        ))
