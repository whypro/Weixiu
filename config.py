# -*- coding:utf-8 -*-
import os

if 'SERVER_SOFTWARE' in os.environ:
    # 生产服务器配置
    from bae.core import const
    # 数据库配置
    DB_HOST = const.MYSQL_HOST
    DB_DATABASE = 'RTBLqowGxNpCGjMISBLt'
    DB_USERNAME = const.MYSQL_USER
    DB_PASSWORD = const.MYSQL_PASS
    DB_CHARSET = 'utf8'
    DB_PORT = int(const.MYSQL_PORT)
else:
    # 测试服务器配置
    # 数据库配置
    DB_HOST = 'localhost'
    DB_DATABASE = 'weixiu'
    DB_USERNAME = 'root'
    DB_PASSWORD = 'whypro'
    DB_CHARSET = 'utf8'
    DB_PORT = 3306

#
DEBUG = True
SECRET_KEY = 'development key'
