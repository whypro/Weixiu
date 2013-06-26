# -*- coding: utf-8 -*-
from sqlalchemy import create_engin


from sqlalchemy.databases import mysql
mysql_engine = create_engine('mysql://root:whypro@localhost:3306/weixiu?charset=utf8',encoding = "utf-8",echo =True)   
#mysql_engine.connect()    
metadata = MetaData()
#创建users表
users_table = Table('xxx', metadata,
    Column('id', Integer, primary_key=True),
    Column('username', String(20), nullable = False),
    Column('fullname', String(20), nullable = False),
    Column('password', String(20), nullable = False),
    mysql_engine='InnoDB'
)
#mysql_engine='InnoDB' 或者 mysql_engine='MyISAM' 表类型
metadata.create_all(mysql_engine)


from app import db

ROLE_USER = 0
ROLE_ADMIN = 1

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    nickname = db.Column(db.String(64), index = True, unique = True)
    email = db.Column(db.String(120), index = True, unique = True)
    role = db.Column(db.SmallInteger, default = ROLE_USER)

    def __repr__(self):
        return '<User %r>' % (self.nickname)
