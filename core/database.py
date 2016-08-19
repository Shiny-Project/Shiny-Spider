import datetime, hashlib, time
import json

import core.config as config
from core.log import Log

from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import TIMESTAMP



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



def get_spider_info(spider_name):
    """根据Spider的名字获取Spider的路径"""
    try:
        response = session.query(Spider).filter(Spider.name == spider_name).one()
        session.close()
        return response.path, response.trigger_time, response.info
    except Exception as e:
        Logger.error('无法从数据库取得数据' + str(e))


def create_event(level, data, name, socket):
    """记录数据"""
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
            socket.emit('event', json.dumps({
                "spiderName": name,
                "hash": hash,
                "data": data
            }))
            Logger.info('[ Spider = ' + name + ' ] 新的数据已经记录 [ Hash = ' + hash + ' ]')
        else:
            Logger.warning('数据已经被记录过 [ Hash = ' + hash + ' ]')

    except Exception as e:
        Logger.error('无法记录数据' + str(e))


def renew_trigger_time(spider_name):
    """更新Spider的调用次数和最后一次调用的时间"""
    try:
        response = session.query(Spider).filter(Spider.name == spider_name).one()
        response.trigger_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        response.trigger_count += 1
        session.commit()
        session.close()
        Logger.debug('更新 [ Spider = ' + spider_name + ' ] 的调用次数和时间')
    except Exception as e:
        Logger.error('无法更新Spider的调用时间 [ Spider = ' + spider_name + ' ] ')


def get_spider_list():
    try:
        return session.query(Spider).all()
    except Exception as e:
        Logger.error('无法获得 Spider 列表')