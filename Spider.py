import sys,time,hashlib
import Main,config,database
from log import Log
import json
from urllib import request
from bs4 import BeautifulSoup
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import DateTime, TIMESTAMP

class Spider():
	"""抓取和处理数据"""
	def __init__(self):
		self.Logger = Log();

	def getPage(self,url):
		try:
			self.Logger.debug(u'试图抓取页面[' + url + ']')
			req = request.Request(url)
			req.add_header('User-Agent','Mirai/0.1 (https://github.com/Last-Order/Mirai-spider)')
			response = request.urlopen(req);
			self.Logger.debug(u'抓取页面[' + url + ']成功')
			return response.read();
		except Exception as e:
			self.Logger.error('抓取页面[' + url + ']错误:' +  str(e));

	def generateEventID(self,data):
		m = hashlib.md5();
		event = (str(data) + str(time.ctime())).encode('utf-8');
		m.update(event);
		return m.hexdigest();

	def createEvent(self,data):
		event_id = self.generateEventID(data);
		api_id = self.api_id;
		return database.addEvent(event_id,api_id,json.JSONEncoder().encode(data));


if __name__ == '__main__':
	pass;
		