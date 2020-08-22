from flask_restful import Resource
from flask import g
from flask_restful.reqparse import RequestParser

from utils.decorators import login_required
from models.user import User
from utils.img_storage import upload_file
from utils.parser import image_file as image_type
from app import db


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


class UserPhotoResource(Resource):
    method_decorators = [login_required]

    def patch(self):
        # 获取参数
        parser = RequestParser()
        parser.add_argument('photo', required=True, location='files', type=image_type)
        args = parser.parse_args()
        image = args.photo

        # 读取上传的二进制数据
        img_bytes = image.read()

        # 上传到七牛云
        try:
            avatar_url = upload_file(img_bytes)
        except BaseException as e:
            return {'message': 'upload error: %s' % e, 'data': None}, 500

        # 更新用户数据中的头像字段
        User.query.filter(User.id==g.userid).update({'profile_photo': avatar_url})
        db.session.commit()

        # 返回头像的URL
        return {'photo_url': avatar_url}
