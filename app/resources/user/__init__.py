from flask import Blueprint
from flask_restful import Api
from common.utils.output import output_json

# 1.创建蓝图对象
from app.resources.user.passport import SMSCodeResource

user_bp = Blueprint('user', __name__)

# 2.创建组件对象
user_api = Api(user_bp)

# 3.注册类视图
user_api.add_resource(SMSCodeResource, '/sms/code', endpoint='smscode')
user_api.representation('application/json')(output_json)



