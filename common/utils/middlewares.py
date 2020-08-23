from flask import request, g

from utils.jwt_util import verify_jwt


def get_userinfo():
    """获取用户信息"""

    # 从请求头中获取令牌
    token = request.headers.get('Authorization')

    g.userid = None  # 先定义userid, 这里不定义的话走装饰器时就会报g没有userid这个属性错误

    if token:
        data = verify_jwt(token)
        if data:
            g.userid = data.get('userid')
