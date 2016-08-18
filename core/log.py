import time


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'


class Log():
    """Log module for Mirai"""

    def __init__(self):
        self.TIMEFORMAT = "%Y-%m-%d %X"

    def debug(self, text):
        """创建调试信息"""
        print('[DEBUG] [' + str(time.strftime(self.TIMEFORMAT, time.localtime())) + '] ' + text)

    def info(self, text):
        """创建提示信息"""
        print(bcolors.OKGREEN + '[INFO] [' + str(time.strftime(self.TIMEFORMAT, time.localtime())) + '] ' + text + bcolors.ENDC)

    def warning(self, text):
        """创建警告信息"""
        print(bcolors.WARNING + '[WARN] [' + str(time.strftime(self.TIMEFORMAT, time.localtime())) + '] ' + text + bcolors.ENDC)

    def error(self, text):
        """创建错误信息"""
        print(bcolors.FAIL + '[ERROR] [' + str(time.strftime(self.TIMEFORMAT, time.localtime())) + '] ' + text + bcolors.ENDC)


if __name__ == '__main__':
    pass
