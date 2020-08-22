import sys, os

from flask import Flask

from utils.middlewares import get_userinfo

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR + '/common')

from app.settings.config import config_dict
from utils.constants import EXTRA_ENV_COINFIG
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from flask_migrate import Migrate


# 创建sqlalchemy组件对象
db = SQLAlchemy()
# 创建redis客户端
redis_client = None  # type: StrictRedis


def register_bp(app:Flask):
    """注册蓝图"""

    # 建议使用局部导入, 在组件初始化完成以后再关联视图文件
    # 局部导入, 避免组件没有初始化完成, 因为视图里面可能会用到组件
    from app.resources.user import user_bp
    app.register_blueprint(user_bp)


def register_extensions(app:Flask):
    """组件初始化"""
    # sqlalchemy组件初始化
    db.init_app(app)

    # redis组件初始化
    global redis_client
    redis_client = StrictRedis(host=app.config['REDIS_HOST'], port=app.config['REDIS_PORT'], decode_responses=True)
    # decode_response自动把bytes变为原始类型

    # 添加转换器
    from utils.converters import register_converters
    register_converters(app)

    # 数据组件初始化
    Migrate(app, db)
    # 导入模型文件, 让项目可以识别模型类
    from models import user

    app.before_request(get_userinfo)


def create_flask_app(type):
    """创建flask应用"""

    # 创建Flask应用
    app = Flask(__name__)

    # 取出配置的子类
    config_class = config_dict[type]

    # 先加载默认配置
    app.config.from_object(config_class)

    # 再加载额外配置
    app.config.from_envvar(EXTRA_ENV_COINFIG, silent=True)

    return app


def create_app(type):
    """创建应用, 并进行组件初始化"""

    # 创建应用
    flask_app = create_flask_app(type)

    # 组件初始化
    register_extensions(flask_app)

    # 注册蓝图
    register_bp(flask_app)

    return flask_app
