import random

from flask_restful import Resource

from app import redis_client
from utils.constants import SMS_CODE_EXPIRE


class SMSCodeResource(Resource):
    """获取短信验证码"""
    def get(self, mobile):
        # 生成短信验证码
        rand_num = '%06d' % random.randint(0, 999999)

        # 保存验证码(redis)
        key = 'app:code:{}'.format(mobile)
        redis_client.set(key, rand_num, ex=SMS_CODE_EXPIRE)

        # 发送短信, 第三方短信平台 celry
        print('短信验证码: "mobile": {}, "code": {}'.format(mobile, rand_num))

        # 返回结果
        return {'mobile': mobile}

