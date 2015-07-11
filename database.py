from log import Log 
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import DateTime, TIMESTAMP

#创建ORM基类
Base = declarative_base()
#创建日志类
Logger = Log();

#创建Data表的ORM映射
class Data(Base):
	__tablename__ = 'data'
	id = Column(Integer, primary_key=True);
	event_id = Column(String);
	api_id = Column(String);
	data = Column(String);
	timestamp = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

#创建API表的ORM映射
class API(Base):
	__tablename__ = 'api'
	id = Column(Integer, primary_key=True);
	api_id = Column(String);
	spidername = Column(String);
	info = Column(String);
	triggercount = Column(Integer);


#初始化 连接数据库
engine = create_engine('mysql+mysqlconnector://root:@localhost:3306/Mirai')
DBSession = sessionmaker(bind=engine)
session = DBSession()

def getDataByEventID(event_id):
	"""根据Eventid查询数据"""
	try:
		response = session.query(Data).filter(Data.event_id == event_id).one();
		session.close()
		return response
	except Exception as e:
		Logger.error('无法从数据库获得数据 [' + event_id + ']');

def getDataByID(dataid):
	"""根据id查询数据"""
	try:
		response = session.query(Data).filter(Data.id == dataid).one();\
		session.close()
		return response
	except Exception as e:
		Logger.error('无法从数据库获得数据 [' + dataid + ']')

def getDataByAPIID(api_id):
	"""根据API ID查询数据 时间倒序"""
	try:
		response = session.query(Data).filter(Data.api_id == api_id).order_by(Data.timestamp).all();
		session.close()
		return response;
	except Exception as e:
		Logger.error('无法从数据库获得数据 [' + api_id + ']')

def getSpiderName(api_id):
	try:
		response = session.query(API).filter(API.api_id == api_id).one();
		session.close()
		return response.spidername
	except:
		Logger.error('无法从数据库获得数据 [' + api_id + ']')

def addEvent(event_id,api_id,data):
	"""新增一个事件"""
	try:
		new_event = Data(event_id = event_id,api_id = api_id,data = data);
		Logger.info('创建事件 [' + event_id + ']')
		session.add(new_event);
		session.commit();
		session.close();
	except Exception as e:
		Logger.error('无法写入数据库 [' + event_id + ']')