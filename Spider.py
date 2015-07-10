import sys
import Main,config,pymysql.cursors
from log import Log
import requests,json
from bs4 import BeautifulSoup
class Spider():
	"""抓取和处理数据"""
	def __init__(self):
		connection = pymysql.connect(host = 'localhost', user = config.DATABASE_USER, passwd = config.DATABASE_PASSWORD, db = config.DATABASE_NAME)
		self.Logger = Log(connection);

	def getPage(self,url):
		headers = {'User-Agent' : 'Mirai/0.1 (http://moesound.org/)'}
		try:
			response = requests.get(url, headers = headers);
			self.Logger.debug(u'试图抓取页面[' + url + ']')
			print(response.text);
		except:
			pass;

if __name__ == '__main__':
	pass;
		