# -*- coding:utf-8 -*-
import os

if 'SERVER_SOFTWARE' in os.environ:
    # ��������������
    from bae.core import const
    # ���ݿ�����
    DB_HOST = const.MYSQL_HOST
    DB_DATABASE = 'RTBLqowGxNpCGjMISBLt'
    DB_USERNAME = const.MYSQL_USER
    DB_PASSWORD = const.MYSQL_PASS
    DB_CHARSET = 'utf8'
    DB_PORT = int(const.MYSQL_PORT)
else:
    # ���Է���������
    # ���ݿ�����
    DB_HOST = 'localhost'
    DB_DATABASE = 'weixiu'
    DB_USERNAME = 'root'
    DB_PASSWORD = 'whypro'
    DB_CHARSET = 'utf8'
    DB_PORT = 3306

#
DEBUG = True
SECRET_KEY = 'development key'
