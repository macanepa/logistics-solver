import datetime
from .print_manager import *

class Log_Settings:
    display_logs = False

class Log_Manager:
    class Log:
        def __init__(self, text, is_error=False):
            self.time_stamp = datetime.datetime.now()
            self.text = text
            self.is_error = is_error

        def print_log(self):
            if Log_Settings.display_logs:
                text = ("{} => <{}>".format(self.time_stamp,self.text))
                if self.is_error:
                    mcprint(text=text, color=Color.RED)
                else:
                    mcprint(text=text, color=Color.YELLOW)

    def __init__(self, developer_mode=False):
        self.logs = []
        self.developer_mode = developer_mode

    def log(self, text, is_error=False):
        log = self.Log(text, is_error)
        self.logs.append(log)

        if(self.developer_mode):
            log.print_log()

    def print_logs(self):
        for log in self.logs:
            log.print_log()

    def clear_logs(self):
        self.logs.clear()
