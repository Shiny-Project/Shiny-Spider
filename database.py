from log import Log 
import meta,config
import json
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
	id = Column(Integer, primary_key=True)
	event_id = Column(String)
	api_id = Column(String)
	data = Column(String)
	timestamp = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

#创建API表的ORM映射
class API(Base):
	__tablename__ = 'api'
	id = Column(Integer, primary_key=True);
	api_id = Column(String);
	spidername = Column(String);
	info = Column(String);
	triggercount = Column(Integer);

#创建Job表的ORM映射
class Job(Base):
	__tablename__ = 'job'
	id = Column(Integer, primary_key=True)
	api_id = Column(String)
	timestamp = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))


#初始化 连接数据库
engine = create_engine('mysql+pymysql://' + config.DATABASE_USER + ':' + config.DATABASE_PASSWORD + '@localhost' + '/' + config.DATABASE_NAME)
DBSession = sessionmaker(bind=engine)
session = DBSession()

def getDataByEventID(event_id):
	"""根据Eventid查询数据"""
	try:
		response = session.query(Data).filter(Data.event_id == event_id).one();
		session.close()
		return response
	except Exception as e:
		Logger.error('无法从数据库获得数据 [ 事件ID = ' + event_id + ' ]');

def getDataByID(dataid):
	"""根据id查询数据"""
	try:
		response = session.query(Data).filter(Data.id == dataid).one();
		session.close()
		return response
	except Exception as e:
		Logger.error('无法从数据库获得数据 [ 数据ID = ' + dataid + ' ]')

def getDataByAPIID(api_id):
	"""根据API ID查询数据 时间倒序"""
	try:
		response = session.query(Data).filter(Data.api_id == api_id).order_by(Data.timestamp).all();
		session.close()
		return response;
	except Exception as e:
		Logger.error('无法从数据库获得数据 [ API ID = ' + api_id + ' ]')

def getSpiderName(api_id):
	"""获取API ID对应的爬虫名"""
	try:
		response = session.query(API).filter(API.api_id == api_id).one();
		session.close()
		return response.spidername
	except:
		Logger.error('无法从数据库获得数据 [ API ID = ' + api_id + ' ]')

def addEvent(event_id,api_id,data):
	"""新增一个事件"""
	try:
		new_event = Data(event_id = event_id, api_id = api_id, data = data);
		Logger.info('创建事件 [ 事件ID = ' + event_id + ' ]')
		session.add(new_event);
		session.commit();
		session.close();
	except Exception as e:
		Logger.error('无法写入数据库 [ 事件 ID = ' + event_id + ' ]')


def addJob(api_id,params = dict()):
	"""新增一个任务"""
	JSONEncoder = json.JSONEncoder();
	try:
		new_job = Job(api_id = api_id, params = JSONEncoder.encode(params))
		Logger.info('创建任务 [ API ID = ' + api_id + ' ]' )
		session.add(new_job)
		session.commit()
		session.close()
	except Exception as e:
		Logger.error('无法写入数据库 [ API ID = ' + api_id + ' ]')

def getJobInfo(job_id):
	"""根据Id查询任务"""
	try:
		response = session.query(Job).filter(Job.id == job_id).one()
		session.close()
		return response
	except Exception as e:
		Logger.error('无法从数据库获得数据 ' + '[ 任务ID = ' + job_id + ' ]')

def getRecentJobs():
	"""查询未完成的任务"""
	try:
		response = session.query(Job).all()
		session.close()
		return response
	except Exception as e:
		Logger.error('无法从数据库获得数据' + str(e))

def deleteJob(job_id):
	"""删除已经完成的任务"""
	try:
		response = session.query(Job).filter(Job.id == job_id).delete()
		session.commit()
		session.close()
	except Exception as e:
		Logger.error('无法删除数据')