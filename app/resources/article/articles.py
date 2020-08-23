from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from datetime import datetime
from models.article import Article
from models.user import User
from app import db
from utils.constants import HOME_PRE_PAGE


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
