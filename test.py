from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import DateTime, TIMESTAMP

#创建ORM基类
Base = declarative_base()

#创建Data表的ORM映射
class Data(Base):
	__tablename__ = 'data'
	id = Column(Integer, primary_key=True);
	event_id = Column(String);
	api_id = Column(String);
	data = Column(String);
	timestamp = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))

#初始化 连接数据库
engine = create_engine('mysql+mysqlconnector://root:@localhost:3306/Mirai')
DBSession = sessionmaker(bind=engine)
session = DBSession()

#查询
res = session.query(Data).all();
for line in res:
	print(line.data);

#插表
new_data = Data(event_id='1111',api_id='1111',data='11111');
session.add(new_data);
session.commit()
session.close()