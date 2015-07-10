from logbook import Logger
class Log():
	"""Log module for Mirai"""
	def __init__(self, connection = None):
		self.Logger = Logger('Mirai')

	def debug(self,text):
		"""创建调试信息"""
		self.Logger.debug(text)

	def info(self,text):
		"""创建提示信息"""
		self.Logger.info(text)

	def warning(self,text):
		"""创建警告信息"""
		self.Logger.warn(text)

	def error(self,text):
		"""创建错误信息"""
		self.Logger.error(text)


if __name__ == '__main__':
	pass