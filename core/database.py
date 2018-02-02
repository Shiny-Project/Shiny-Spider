# Shiny 数据库通讯

import datetime, hashlib, time
import json

import core.config as config
from core import utils
from core.log import Log

from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import TIMESTAMP

import Shiny

# Shiny SDK
shiny = Shiny.Shiny(config.API_KEY, config.API_SECRET_KEY)

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
    analysed = Column(Integer)
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

class Keyword(Base):
    __tablename__ = 'keyword'
    id = Column(Integer, primary_key=True)
    keyword = Column(String)
    createdAt = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updatedAt = Column(TIMESTAMP)

class KeywordScore(Base):
    __tablename__ = 'keywordscore'
    id = Column(Integer, primary_key=True)
    keyword = Column(String)
    score = Column(Float)
    event = Column(Integer)
    createdAt = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updatedAt = Column(TIMESTAMP)

def create_event(level, data, name, hash):
    """记录数据"""
    if not hash:
        m = hashlib.md5()
        event = json.dumps(data).encode('utf-8')
        m.update(event)
        hash = m.hexdigest()

    try:
        try:
            shiny.add(name, level, data, hash=hash)
            Logger.info('[ Spider = ' + name + ' ] 新的数据已经记录 [ Hash = ' + hash + ' ]')
        except Shiny.ShinyError as e:
            Logger.error('无法向Shiny提交数据:' + str(e))

    except Exception as e:
        Logger.error('无法记录数据' + str(e))

class Database():
    session = None
    def __init__(self):
        # 初始化 连接数据库
        engine = create_engine(
            'mysql+pymysql://' + config.DATABASE_USER + ':' + config.DATABASE_PASSWORD + '@localhost' + '/' + config.DATABASE_NAME + '?charset=utf8', echo=config.ENABLE_DATABASE_CONSOLE)
        DBSession = sessionmaker(bind=engine, autoflush=True)
        self.session = DBSession()


    def get_spider_info(self, spider_name):
        """根据Spider的名字获取Spider的路径"""
        try:
            response = self.session.query(Spider).filter(Spider.name == spider_name).one()
            self.session.commit()
            return response.path, response.trigger_time, response.info
        except Exception as e:
            Logger.error('无法从数据库取得数据' + str(e))

    def get_job_list(self):
        """获得全部 Spider 列表"""
        try:
            response = shiny.get_jobs()
            return response["data"]
        except Exception as e:
            Logger.error('无法获得 Spider 列表' + str(e))
    
    def report_job_status(self, job_id, status):
        """ 报告任务状态 """
        try:
            response = shiny.report(job_id, status)
            Logger.debug("回报任务状态 [ ID=" + str(job_id) + " = " + status + " ]")
            return response["data"]
        except Exception as e:
            Logger.error('回报任务状态失败' + str(e))