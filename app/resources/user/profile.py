from flask_restful import Resource
from flask import g
from utils.decorators import login_required
from models.user import User

class CurrentUserResource(Resource):
    # 进行访问限制
    method_decorators = {'get':[login_required]}

    def get(self):
        """获取用户信息"""

        #　获取用户主键
        userid = g.userid

        # 查询用户数据
        user = User.query.get(userid)

        return user.to_dict()


# class UserPhotoResource(Resource):
#     method_decorators = [login_required]
#
#     def patch(self):
        # 获取参数

        # 读取上传的二进制数据

        # 上传到七牛云

        # 更新用户数据中的头像字段

        # 返回头像的URL
