#-*- coding:utf-8 -*-

try:
    import  bae
except:
    # ���Է���������
    # ���ݿ�����
    DB_HOST = 'localhost'
    DB_DATABASE = 'weixiu'
    DB_USERNAME = 'root'
    DB_PASSWORD = 'whypro'
    DB_CHARSET = 'utf8'
    DB_PORT = 3306
else:
    # ��������������
    from bae.core import const
    # ���ݿ�����
    DB_HOST = const.MYSQL_HOST
    DB_DATABASE = 'RTBLqowGxNpCGjMISBLt'
    DB_USERNAME = const.MYSQL_USER
    DB_PASSWORD = const.MYSQL_PASS
    DB_CHARSET = 'utf8'
    DB_PORT = int(const.MYSQL_PORT)

#
DEBUG = True
SECRET_KEY = 'development key'
