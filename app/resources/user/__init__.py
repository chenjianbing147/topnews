from flask import Blueprint
from flask_restful import Api
from common.utils.output import output_json
from utils.constants import BASE_URL_PRIFIX

# 1.创建蓝图对象
from app.resources.user.passport import SMSCodeResource

user_bp = Blueprint('user', __name__, url_prefix=BASE_URL_PRIFIX)

# 2.创建组件对象
user_api = Api(user_bp)

# 3.注册类视图
user_api.add_resource(SMSCodeResource, '/sms/codes/<mob:mobile>', endpoint='smscode')
user_api.representation('application/json')(output_json)



