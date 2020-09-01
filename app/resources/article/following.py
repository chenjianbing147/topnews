from datetime import datetime

from flask import g
from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from sqlalchemy.orm import load_only

from app import db
from cache.user import UserFollowCache, UserCache
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

        # 获取当前时间
        update_time = datetime.now()

        # 查询作者和用户是否存在关系
        rel_obj = Relation.query.options(load_only(Relation.id)).\
            filter(Relation.user_id==userid, Relation.author_id==author_id).first()

        if rel_obj: # 如果存在
            rel_obj.relation = Relation.RELATION.FOLLOW
            rel_obj.update_time = update_time

        else:   # 如果不存在
            relation = Relation(user_id=userid, author_id=author_id, relation=Relation.RELATION.FOLLOW)
            db.session.add(relation)

        # 用户的关注数量+1
        User.query.filter(User.id==userid).update({'following_count':User.following_count+1})
        # 作者粉丝数量+1
        User.query.filter(User.id==author_id).update({'fans_count': User.fans_count+1 })

        db.session.commit()

        """更新缓存"""
        UserFollowCache(userid).update(author_id, update_time.timestamp(), is_follow=True)

        return {'target':author_id}

    def get(self):
        userid = g.userid
        parser = RequestParser()
        parser.add_argument('page', location='args', default=1, type=int)
        parser.add_argument('per_page', location='args', default=2, type=int)
        args = parser.parse_args()
        page = args.page
        page_size = args.per_page

        """查询数据, 当前用户的关注列表"""
        following_list = UserFollowCache(userid).get(page, page_size)
        author_list = []
        for author_id in following_list:
            author_cache = UserCache(author_id).get()
            author_list.append({
                'id':author_cache.get('id'),
                'name':author_cache.get('name'),
                'photo':author_cache.get('photo'),
                'fans_count':author_cache.get('fans_count'),
                'mutual_follow':author_cache.get('mutual_follow'),
            })

        # 获取用户关注数量
        user = UserCache(userid).get()

        # 返回数据
        return {'results': author_list, 'per_page': per_page, 'page': page, 'total_count': user['follow_count']}



class UnFollowUserResource(Resource):
    method_decorators = [login_required]

    def delete(self, target):
        # 接受参数
        userid = g.userid

        Relation.query.filter(Relation.user_id==userid, Relation.author_id==target).\
            update({'relation':Relation.RELATION.DELETE, 'update_time':datetime.now()})

        User.query.filter(User.id==userid).update({'following_count': User.following_count-1})
        User.query.filter(User.id==target).update({'fans_count':User.fans_count-1})
        # 提交事务
        db.session.commit()

        """更新缓存"""
        UserFollowCache(userid).update(target, is_follow=False)

        return {'message':'OK'}








