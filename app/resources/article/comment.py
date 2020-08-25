from flask_restful import Resource
from flask_restful.inputs import regex
from flask_restful.reqparse import RequestParser

from app import db
from models.article import Comment, Article
from utils.decorators import login_required


class CommentResource(Resource):
    method_decorators = [login_required]

    def post(self):
        """发布评论"""

        # 获取参数
        userid =g.userid
        parser = RequestParser()
        parser.add_argument('target', required=True, location='json', type=int)
        parser.add_argument('content', required=True, location='json', type=regex(r'.+'))
        args = parser.parse_args()
        target = args.target
        content = args.content

        # 新增评论数据
        comment = Comment(article_id=target, user_id=userid, content=content, parent_id=0)
        db.session.add(comment)

        # 让文章评论数量+1
        Article.query.filter(Article.id==target).update({'comment_count':Article.comment_count+1})
        db.session.commit()

        return {'target':target, 'com_id':comment.id}
