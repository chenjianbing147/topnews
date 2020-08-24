from datetime import datetime

from flask import g
from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from sqlalchemy.orm import load_only

from app import db
from models.user import Relation, User
from utils.decorators import login_required


class FollowUserResource(Resource):
    method_decorators = [login_required]

    def post(self):

        # 获取参数
        userid = g.userid
        parser = RequestParser()
        parser.add_argument('target', required=True, location='json', type=int)
        args = parser.parse_args()
        author_id = args.target

        # 查询作者和用户是否存在关系
        rel_obj = Relation.query.options(load_only(Relation.id)).\
            filter(Relation.user_id==userid, Relation.author_id==author_id).first()

        if rel_obj: # 如果存在
            rel_obj.relation = Relation.RELATION.FOLLOW
            rel_obj.update_time = datetime.now()

        else:   # 如果不存在
            relation = Relation(user_id=userid, author_id=author_id, relation=Relation.RELATION.FOLLOW)
            db.session.add(relation)

        # 用户的关注数量+1
        User.query.filter(User.id==userid).update({'following_count':User.following_count+1})
        # 作者粉丝数量+1
        User.query.filter(User.id==author_id).update({'fans_count': User.fans_count+1 })

        db.session.commit()

        return {'target':author_id}
