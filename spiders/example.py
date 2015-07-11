#Common Header
import sys,time;
sys.path.append('..');
from spider import Spider
from bs4 import BeautifulSoup
from bs4 import UnicodeDammit
from urllib import request
class ExampleSpider(Spider):
	"""Spider描述"""
	api_id = '000000001';#声明API ID
	def __init__(self):
		super(ExampleSpider, self).__init__()
	
	def main(self):
		url = 'http://www.wz121.com/WeatherForecast/ThreeHourForecast.htm';
		#url = 'http://www.baidu.com/'
		response = self.getPage(url);
		html = BeautifulSoup(response,"html.parser",from_encoding="utf-8");
		node = html.find(attrs={"id":'ctl00_ContentBody_newsContent'});
		data = dict(forecast=node.text);
		result = self.createEvent(data);



if __name__ == '__main__':
	a = ExampleSpider();
	a.main();