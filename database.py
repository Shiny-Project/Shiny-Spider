import hashlib

from log import Log
import meta, config
import json
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import DateTime, TIMESTAMP

# 创建ORM基类
Base = declarative_base()

# 创建日志类
Logger = Log()


# 定义Data表的ORM映射
class Data(Base):
    __tablename__ = 'data'
    id = Column(Integer, primary_key=True)
    data = Column(Text)
    level = Column(Integer)
    hash = Column(String)
    publisher = Column(String)  # 其实是Spider名
    createdAt = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))  # Sails自动维护
    updatedAt = Column(TIMESTAMP)  # Sails自动维护 下同


# 定义API表的ORM映射
class Spider(Base):
    __tablename__ = 'spider'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    path = Column(String)
    info = Column(String)
    trigger_count = Column(Integer)  # 调用次数统计
    trigger_time = Column(Integer)  # 上次调用时间
    createdAt = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updatedAt = Column(TIMESTAMP)


# 定义Job表的ORM映射
class Job(Base):
    __tablename__ = 'job'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    info = Column(Text)
    createdAt = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updatedAt = Column(TIMESTAMP)


# 初始化 连接数据库
engine = create_engine(
    'mysql+pymysql://' + config.DATABASE_USER + ':' + config.DATABASE_PASSWORD + '@localhost' + '/' + config.DATABASE_NAME)
DBSession = sessionmaker(bind=engine)
session = DBSession()


# ------------------------REBUILD---------------------------------------

def get_spider_path(spider_name):
    try:
        response = session.query(Spider).filter(Spider.name == spider_name).one()
        return response.path
    except Exception as e:
        Logger.error('无法从数据库取得数据' + str(e))


def create_event(level, data, name):
    m = hashlib.md5()
    event = (str(data)).encode('utf-8')
    m.update(event)
    hash = m.hexdigest()

    try:
        response = session.query(Data).filter(Data.hash == hash).all()
        if not response:
            # 数据不重复 继续记录
            new_event = Data(data=data, level=level, publisher=name, hash=hash)
            session.add(new_event)
            session.commit()
            session.close()
            Logger.info('[ Spider = ' + name + ' ] 新的数据已经记录 [ Hash = ' + hash + ' ]')
        else:
            Logger.warning('数据已经被记录过 [ Hash = ' + hash + ' ]')

    except Exception as e:
        Logger.error('无法记录数据' + str(e))

#
#
#
#
# # -----------------------------------------------------------------------
# def getDataByEventID(event_id):
#     """根据Eventid查询数据"""
#     try:
#         response = session.query(Data).filter(Data.event_id == event_id).one()
#         session.close()
#         return response
#     except Exception as e:
#         Logger.error('无法从数据库获得数据 [ 事件ID = ' + event_id + ' ]')
#
#
# def getDataByID(dataid):
#     """根据id查询数据"""
#     try:
#         response = session.query(Data).filter(Data.id == dataid).one()
#         session.close()
#         return response
#     except Exception as e:
#         Logger.error('无法从数据库获得数据 [ 数据ID = ' + dataid + ' ]')
#
#
# def getDataByAPIID(api_id):
#     """根据API ID查询数据 时间倒序"""
#     try:
#         response = session.query(Data).filter(Data.api_id == api_id).order_by(Data.timestamp).all()
#         session.close()
#         return response
#     except Exception as e:
#         Logger.error('无法从数据库获得数据 [ API ID = ' + api_id + ' ]')
#
#
# def getSpiderName(api_id):
#     """获取API ID对应的爬虫名"""
#     try:
#         response = session.query(API).filter(API.api_id == api_id).one()
#         session.close()
#         return response.spidername
#     except:
#         Logger.error('无法从数据库获得数据 [ API ID = ' + api_id + ' ]')
#
#
# def addEvent(event_id, api_id, data):
#     """新增一个事件"""
#     try:
#         new_event = Data(event_id=event_id, api_id=api_id, data=data)
#         Logger.info('创建事件 [ 事件ID = ' + event_id + ' ]')
#         session.add(new_event)
#         session.commit()
#         session.close()
#     except Exception as e:
#         Logger.error('无法写入数据库 [ 事件 ID = ' + event_id + ' ]')
#
#
# def addJob(api_id, params={}):
#     """新增一个任务"""
#     JSONEncoder = json.JSONEncoder()
#     try:
#         new_job = Job(api_id=api_id, params=JSONEncoder.encode(params))
#         Logger.info('创建任务 [ API ID = ' + api_id + ' ]')
#         session.add(new_job)
#         session.commit()
#         session.close()
#     except Exception as e:
#         Logger.error('无法写入数据库 [ API ID = ' + api_id + ' ]')
#
#
# def getJobInfo(job_id):
#     """根据Id查询任务"""
#     try:
#         response = session.query(Job).filter(Job.id == job_id).one()
#         session.close()
#         return response
#     except Exception as e:
#         Logger.error('无法从数据库获得数据 ' + '[ 任务ID = ' + job_id + ' ]')
#
#
# def getRecentJobs():
#     """查询未完成的任务"""
#     try:
#         response = session.query(Job).all()
#         session.close()
#         return response
#     except Exception as e:
#         Logger.error('无法从数据库获得数据' + str(e))
#
#
# def deleteJob(job_id):
#     """删除已经完成的任务"""
#     try:
#         response = session.query(Job).filter(Job.id == job_id).delete()
#         session.commit()
#         session.close()
#     except Exception as e:
#         Logger.error('无法删除数据')
