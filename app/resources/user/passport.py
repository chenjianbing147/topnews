import random
from datetime import datetime, timedelta

from flask import current_app
from flask_restful import Resource
from flask_restful.inputs import regex
from flask_restful.reqparse import RequestParser
from sqlalchemy.orm import load_only

from app import redis_client, db
from models.user import User
from utils.constants import SMS_CODE_EXPIRE
from utils.parser import mobile as mobile_type
from utils.jwt_util import generate_jwt, verify_jwt


class SMSCodeResource(Resource):
    """获取短信验证码"""
    def get(self, mobile):
        # 生成短信验证码
        rand_num = '%06d' % random.randint(0, 999999)

        # 保存验证码(redis)
        key = 'app:code:{}'.format(mobile)
        redis_client.set(key, 123456, ex=SMS_CODE_EXPIRE)

        # 发送短信, 第三方短信平台 celry
        print('短信验证码: "mobile": {}, "code": {}'.format(mobile, rand_num))

        # 返回结果
        return {'mobile': mobile}


class LoginResource(Resource):

    def post(self):
        """注册登录"""
        # 获取参数
        parser = RequestParser()
        parser.add_argument('mobile', required=True, location='json', type=mobile_type)
        parser.add_argument('code', required=True, location='json', type=regex(r'\d{6}'))
        args = parser.parse_args()
        mobile = args.mobile
        code = args.code

        # 检验验证码
        key = 'app:code:{}'.format(mobile)
        real_code = redis_client.get(key)

        if not real_code or real_code != code:
            return {"message":"Invalid code", "data":None}, 400

        # 删除验证码
        # redis_client.delete(key)

        # 验证成功, 查询数据库
        user = User.query.options(load_only(User.id)).filter(User.mobile==mobile).first()

        if user:
            user.last_login = datetime.now()

        else:
            user = User(mobile=mobile, name=mobile, last_login=datetime.now())
            db.session.add(user)

        db.session.commit()

        # 生成jwt
        token = generate_jwt({'userid':user.id}, expiry=datetime.utcnow() + timedelta(days=current_app.config['JWT_EXPIRE_DAYS']))

        # 返回响应
        return {"token":token}, 200
