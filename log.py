import time;
class Log():
    """Log module for Mirai"""
    def __init__(self):
        self.TIMEFORMAT = "%Y-%m-%d %X"


    def debug(self,text):
        """创建调试信息"""
        print('[DEBUG] [' +  str(time.strftime(self.TIMEFORMAT, time.localtime())) + '] ' + text);

    def info(self,text):
        """创建提示信息"""
        print('[INFO] [' +  str(time.strftime(self.TIMEFORMAT, time.localtime())) + '] ' + text);

    def warning(self,text):
        """创建警告信息"""
        print('[WARN] [' +  str(time.strftime(self.TIMEFORMAT, time.localtime())) + '] ' + text);

    def error(self,text):
        """创建错误信息"""
        print('[ERROR] [' +  str(time.strftime(self.TIMEFORMAT, time.localtime())) + '] ' + text);


if __name__ == '__main__':
    pass