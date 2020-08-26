from flask import g
from flask_restful import Resource
from flask_restful.inputs import regex
from flask_restful.reqparse import RequestParser
from sqlalchemy.orm import load_only

from app import db
from models.article import Comment, Article
from models.user import User
from utils.decorators import login_required


class CommentResource(Resource):
    method_decorators = {'post':[login_required]}

    def post(self):
        """发布评论"""

        # 获取参数
        userid =g.userid
        parser = RequestParser()
        parser.add_argument('target', required=True, location='json', type=int)
        parser.add_argument('content', required=True, location='json', type=regex(r'.+'))
        parser.add_argument('parent_id', required=False, location='json', type=int)
        args = parser.parse_args()
        target = args.target
        content = args.content
        parent_id = args.parent_id

        # 新增回复数据
        if parent_id:
            comment = Comment(article_id=target, user_id=userid, content=content, parent_id=parent_id)
            db.session.add(comment)

            Comment.query.filter(parent_id==Comment.id).update({'reply_count':Comment.reply_count +1 })

        # 新增评论数据
        else:
            comment = Comment(article_id=target, user_id=userid, content=content, parent_id=0)
            db.session.add(comment)
            # 让文章评论数量+1
            Article.query.filter(Article.id == target).update({'comment_count': Article.comment_count + 1})

        db.session.commit()

        return {'target':target, 'com_id':comment.id, 'parent_id':args.parent_id}


    def get(self):
        """获取评论列表"""
        # 获取参数
        parser = RequestParser()
        parser.add_argument('source', required=True, location='args', type=int)
        parser.add_argument('offset', default=0, location='args', type=int)
        parser.add_argument('limit', default=10, location='args',type=int)
        parser.add_argument('type', required=True, location='args',type=regex(r'[ac]'))
        args = parser.parse_args()
        source = args.source
        offset = args.offset
        limit = args.limit
        source_type = args.type

        if source_type == 'a':  # 获取评论列表
            # 查询文章的评论列表　需求:分页
            comments = db.session.query(Comment.id, Comment.user_id, User.name, User.profile_photo,
                                        Comment.ctime, Comment.content, Comment.reply_count, Comment.like_count). \
                join(User, Comment.user_id == User.id).filter(Comment.article_id == source, Comment.id > offset, Comment.parent_id==0).\
                order_by(Comment.id).limit(limit).all()

            # 查询评论总数
            total_count = Comment.query.options(load_only(Comment.id)).filter(Comment.article_id == source, Comment.parent_id==0).count()

            # 所有评论中的最后一条评论
            end_comment = db.session.query(Comment.id).filter(Comment.article_id == source, Comment.parent_id==0).order_by(
                Comment.id.desc()).first()

        else:   # 获取回复列表
            comments = db.session.query(Comment.id, Comment.user_id, User.name, User.profile_photo,
                                        Comment.ctime, Comment.content, Comment.reply_count, Comment.like_count). \
                join(User, Comment.user_id == User.id).filter(Comment.id > offset, Comment.parent_id==source). \
                order_by(Comment.id).limit(limit).all()

            # 获取回复总数
            total_count = Comment.query.options(load_only(Comment.id)).filter(Comment.parent_id==source).count()

            # 所有回复中的最后一条回复
            end_comment = db.session.query(Comment.id).filter(Comment.parent_id==source).order_by(Comment.id.desc()).first()

        # 序列化
        comment_list = [{
            "com_id": item.id,
            'aut_id': item.user_id,
            'aut_name': item.name,
            'aut_photo': item.profile_photo,
            'pubdate': item.ctime.isoformat(),
            'content': item.content,
            'reply_count': item.reply_count,
            'like_count': item.like_count
        } for item in comments]


        # 所有评论中最后一条评论的id, 拿这个id和last_id进行比较, 可以告诉前端后台数据库是否还有数据可以取
        end_id = end_comment.id if end_comment else None

        # 获取本次请求最后一条数据的id, 这是为了下一次查询提供条件
        last_id = comments[-1].id if comments else None

        # 返回数据
        return {'results': comment_list, 'total_count': total_count, 'last_id': last_id, 'end_id': end_id}

