from flask import Blueprint
from flask_restful import Api
from common.utils.output import output_json
from utils.constants import BASE_URL_PRIFIX
from app.resources.user.passport import *
from app.resources.user.profile import *

# 1.创建蓝图对象

user_bp = Blueprint('user', __name__, url_prefix=BASE_URL_PRIFIX)

# 2.创建组件对象
user_api = Api(user_bp)

user_api.representation('application/json')(output_json)

# 3.注册类视图
user_api.add_resource(SMSCodeResource, '/sms/codes/<mob:mobile>', endpoint='smscode')
user_api.add_resource(LoginResource, '/authorizations')
user_api.add_resource(CurrentUserResource, '/user')



