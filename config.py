# coding = utf-8
import os

DEBUG = True

SECRET_KEY = os.urandom(24)
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

# mysql配置
DIALECT = "mysql"
DRIVER = "pymysql"
USERNAME = "root"
PASSWORD = "root"
HOST = "localhost"
PORT = "3306"
DATABASE = "new_shop"

SQLALCHEMY_DATABASE_URI = "{}+{}://{}:{}@{}:{}/{}?charset=utf8".format(DIALECT, DRIVER, USERNAME, PASSWORD, HOST, PORT,
                                                                       DATABASE)
SQLALCHEMY_TRACK_MODIFICATIONS = False

# qq邮箱配置

MAIL_SERVER = 'smtp.qq.com'
MAIL_PROT = 25
MAIL_USE_TLS = True
MAIL_USE_SSL = False
MAIL_USERNAME = "自己的邮箱"
MAIL_DEFAULT_SENDER = "自己的邮箱"
MAIL_PASSWORD = "自己的SMTP密码"
MAIL_DEBUG = True

# redis配置
REDIS_HOST = "localhost"
REDIS_PORT = 6379

