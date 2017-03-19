# Shiny 控制台日志输出

import time, requests, json, threading
from core import config

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
        self.API = config.GRAYLOG_API

    def debug(self, text):
        """创建调试信息"""
        threading.Thread(target=self.send_log, args=(6, text))
        print('[DEBUG] [' + str(time.strftime(self.TIMEFORMAT, time.localtime())) + '] ' + text)

    def info(self, text):
        """创建提示信息"""
        threading.Thread(target=self.send_log, args=(5, text))
        print(bcolors.OKGREEN + '[INFO] [' + str(time.strftime(self.TIMEFORMAT, time.localtime())) + '] ' + text + bcolors.ENDC)

    def warning(self, text):
        """创建警告信息"""
        threading.Thread(target=self.send_log, args=(4, text))
        print(bcolors.WARNING + '[WARN] [' + str(time.strftime(self.TIMEFORMAT, time.localtime())) + '] ' + text + bcolors.ENDC)

    def error(self, text):
        """创建错误信息"""
        threading.Thread(target=self.send_log, args=(3, text))
        print(bcolors.FAIL + '[ERROR] [' + str(time.strftime(self.TIMEFORMAT, time.localtime())) + '] ' + text + bcolors.ENDC)
    
    def critical(self, text):
        """创建致命错误信息"""
        threading.Thread(target=self.send_log, args=(2, text))
        print(bcolors.FAIL + '[ERROR] [' + str(time.strftime(self.TIMEFORMAT, time.localtime())) + '] ' + text + bcolors.ENDC)

    def send_log(self, level, text):
        data = {
            "level": level,
            "short_message": text,
            "host": "Shiny-JP-Tokyo-1"
        }
        headers = {
            'User-Agent': 'Shiny/0.1 (https://github.com/Shiny-Project/Shiny-README)'
        }

        try:
            response = requests.post(self.API, data=json.dumps(data), headers=headers)
        except Exception as e:
            print(bcolors.FAIL + '在上报错误信息时出现错误: 无法连接到日志服务器' + text + bcolors.ENDC)

if __name__ == '__main__':
    pass
