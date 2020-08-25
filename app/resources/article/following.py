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

    def get(self):
        userid = g.userid
        parser = RequestParser()
        parser.add_argument('page', location='args', default=1, type=int)
        parser.add_argument('per_page', location='args', default=2, type=int)
        args = parser.parse_args()
        page = args.page
        page_size = args.per_page

        # error_out用于设置页码越界是否报错, 默认为True
        data = User.query.options(load_only(User.id, User.name, User.fans_count, User.profile_photo)). \
            join(Relation, User.id == Relation.author_id).filter(Relation.relation == 1, Relation.user_id == userid). \
            order_by(Relation.update_time.desc()).paginate(page, page_size, error_out=True)

        author_list = []
        # 方法一
        # for page_author in data.items:
        #     each_other_rel = Relation.query.loads(Relation.id).filter(Relation.user_id == page_author.id,
        #                                                               Relation.author_id == userid,
        #                                                               Relation.relation == Relation.RELATION.FOLLOW).first()
        #     author_list.append({
        #         'id':page_author.id,
        #         'name':page_author.name,
        #         'photo':page_author.profile_photo,
        #         'fans_count':page_author.fans_count,
        #         'mutual_follow': True if each_other_rel else False
        #     })

        # 方法二
        fans_list = Relation.query.options(load_only(Relation.user_id)).filter(Relation.author_id == userid, Relation.relation==Relation.RELATION.FOLLOW).all()
        for item in data.items:
            author_dict = {
                'id': item.id,
                'name': item.name,
                'photo': item.profile_photo,
                'fans_count': item.fans_count,
                'mutual_follow': False
            }

            # 如果该作者也关注了当前用户, 则为互相关注
            for fans in fans_list:
                if item.id == fans.user_id:
                    author_dict['mutual_follow'] = True
                    break

            author_list.append(author_dict)
        return {'total_count':data.total,
                'page':page,
                'per_page':page_size,
                'results':author_list}


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

        return {'message':'OK'}








