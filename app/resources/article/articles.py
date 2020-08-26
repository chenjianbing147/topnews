from flask import g
from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from datetime import datetime

from sqlalchemy.orm import load_only

from models.article import Article, ArticleContent, Collection, Attitude
from models.user import User, Relation
from app import db
from utils.constants import HOME_PRE_PAGE
from utils.decorators import login_required


class ArticleListResource(Resource):

    def get(self):
        # 接受参数
        parser = RequestParser()
        parser.add_argument('channel_id', required=True, location='args', type=int)
        parser.add_argument('timestamp', required=True, location='args', type=int)
        args = parser.parse_args()
        channel_id = args.channel_id
        timestamp = args.timestamp

        # 如果为推荐频道, 先返回空的
        if channel_id == 0:
            return {'nothing'}

        # 因为数据库里是日期时间类型, 我们要先把时间戳转换为时间日期类型
        timestamp = datetime.fromtimestamp(timestamp * 0.001)  # 这里要转为以秒为单位的时间戳

        # 返回的要用到两张表的数据, 我们要用原生的
        # 关联的条件 文章频道id=频道id,  查询的条件 审核通过, 创建时间小于传过来的时间戳, 淦, 还有排序我都忘记了, 真是个臭傻逼, 淦, 还要分页
        data = db.session.query(Article.id, Article.title, Article.user_id, Article.ctime,
                                User.name, Article.comment_count, Article.cover).join(
                                User, Article.user_id==User.id).filter(Article.channel_id==channel_id,
                                Article.ctime<timestamp, Article.status==Article.STATUS.APPROVED).\
                                order_by(Article.ctime.desc()).limit(HOME_PRE_PAGE).all()

        # 构造文章数据序列化返回, 这里如果data为0的话也就不会做循环了, 淦, 这个我都忘记了,
        resp = [{
            'art_id': item.id,
            'title':item.title,
            'aut_id':item.user_id,
            'pubdate':item.ctime.isoformat(),
            'aut_name':item.name,
            'comm_count':item.comment_count,
            'cover':item.cover
            }
            for item in data]


        # 构造pre_timestamp, 将日期对象转为时间戳
        per_timestamp = int(data[-1].ctime.timestamp() * 1000) if data else 0

        return {'results': resp, 'pre_timestamp': per_timestamp}


class ArticleDetailResource(Resource):

    def get(self, article_id):
        """获取文章详情"""

        # 查询文章数据
        # 文章表, 用户表, 文章内容表
        data = db.session.query(Article.id, Article.title,Article.ctime, Article.user_id,
            User.name, User.profile_photo, ArticleContent.content).\
            join(User, Article.user_id==User.id).\
            join(ArticleContent, Article.id==ArticleContent.article_id).\
            filter(Article.id==article_id).first()

        # 序列化
        to_dict = {
            'art_id': data.id,
            'title': data.title,
            'pubdate': data.ctime.isoformat(),
            'aut_id': data.user_id,
            'aut_name': data.name,
            'aut_photo': data.profile_photo,
            'content': data.content,
            'is_followed': False,
            'attitude': -1,
            'is_collected': False
        }

        """查询关系数据"""
        # 获取用户信息
        userid = g.userid

        if userid:  # 判断用户是否登录
            # 关注情况  用户->作者
            rel_obj = Relation.query.options(load_only(Relation.id)).\
                filter(Relation.user_id==userid, Relation.author_id==data.user_id, Relation.relation==Relation.RELATION.FOLLOW).first()

            to_dict['is_followed'] = True if rel_obj else False

            # 收藏情况  用户->文章
            col_obj = Collection.query.options(load_only(Collection.id)).filter(Collection.user_id==userid,
                    Collection.article_id==article_id, Collection.is_deleted==False).first(                                                         )

            to_dict['is_collected'] = True if col_obj else False

            # 文章态度  用户->文章
            atti = Attitude.query.options(load_only(Attitude.attitude)).filter(Attitude.user_id==userid, Attitude.article_id==article_id).first()

            to_dict['attitude'] = atti.attitude if atti else -1


        # 返回结果
        return to_dict


