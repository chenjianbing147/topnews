from sqlalchemy.orm import load_only

from app import redis_cluster
from cache.constants import UserCacheTTL, UserFollowCacheTTL
from models.user import User, Relation


class UserCache:

    def __init__(self, userid):
        self.userid = userid
        self.key = "user:{}:basic".format(userid)


    def get(self):

        # 先从缓存里面取数据
        data = redis_cluster.hgetall(self.key)
        if data:  # 如果有缓存, 还不能直接返回
            # 还要判断一下是不是缓存穿透的
            if data.get('kk'):
                return None
            else:
                return data
        else:  # 如果没有缓存, 从数据库查
            user = User.qeury.options(load_only(User.id)).filter(User.id==self.userid).first()
            if user:  # 如果数据库有, 返回数据并且回填
                user_data = user.to_dict()
                redis_cluster.hmset(self.key, user_data)
                redis_cluster.expire(self.key, UserCacheTTL.get_val())
                return user_data

            else:  # 如果没有该数据, 防止缓存穿透给一个空值
                redis_cluster.hset(self.key, {'kk':1})
                redis_cluster.expire(self.key, )
                return None


    def clear(self):
        redis_cluster.delete(self.key)


class BaseFollowCache:
    """关注基类"""
    def __init__(self, userid):
        self.userid = userid  # 用户主键

    def get(self, page, per_page):
        """
        获取关注列表, 分页获取

        :param page: 页码
        :param per_page: 每页条数
        :return: 指定页的数据  列表形式 [用户id, ...]  / []
        """

        # 从Redis中查询缓存数据
        is_key_exist = redis_cluster.exists(self.key)

        # 计算开始索引和结束索引

        # 开始索引 = (页码 - 1) * 每页条数
        start_index = (page - 1) * per_page
        # 结束索引 = 开始索引 + 每页条数 - 1
        end_index = start_index + per_page - 1

        if is_key_exist:  # 如果缓存中有, 从缓存中查询数据

            # zrevrange取出的一定是列表(没有数据就是空列表)  ['3', '4', '5']
            print('从缓存中获取数据')
            data = redis_cluster.zrevrange(self.key, start_index, end_index)  # 根据分数(关注时间)倒序取值
            return [int(item_id) for item_id in data]

        else:  # 如果缓存中没有, 到数据库中进行查询

            # 缓存中如果没有数据, 其实有两种情况:  数据库没有该数据 / 数据库中有, 但是缓存过期
            user = UserCache(self.userid).get()

            # 判断数据库中是否有数据(当前用户是否关注过作者)
            if user and user[self.count_key]:   # 用户有关注过作者, 查询数据库

                # 当前用户的关注列表 (取出的字段: 作者id, 关注时间)  关注时间倒序排序
                followings = self.db_query()

                # 将数据回填到redis中
                following_list = []

                for item in followings:
                    # 获取属性  getattr(对象, 字符串形式的属性名)
                    data_id = getattr(item, self.attr_key)
                    # 将数据添加到关注缓存集合中
                    redis_cluster.zadd(self.key, data_id, item.update_time.timestamp())
                    # 将作者id添加到列表中(构建返回数据)
                    following_list.append(data_id)


                # 给缓存集合设置过期时间
                print('查询数据库并回填数据')
                redis_cluster.expire(self.key, UserFollowCacheTTL.get_val())

                # 返回结果     元素数量为5, 最大索引4    最大索引 = 元素数量 - 1
                if start_index <= len(following_list) - 1:  # 如果开始索引存在
                    try:
                        return following_list[start_index:end_index+1]
                    except:
                        return following_list[start_index:]

                else:
                    return []

            else:  # 用户没有关注过任何作者, 返回空列表
                return []


# user:<用户id>:followings  zset  [{value: 用户id, score: 关注时间}, {}, {}]
class UserFollowingCache(BaseFollowCache):
    """用户关注列表缓存类"""

    count_key = 'follow_count'
    attr_key = 'author_id'

    def __init__(self, userid):
        super().__init__(userid)
        self.key = "user:{}:following".format(userid)  # redis的键

    def db_query(self):
        # 当前用户的关注列表 (取出的字段: 作者id, 关注时间)  关注时间倒序排序
        return Relation.query.options(load_only(Relation.author_id, Relation.update_time)). \
            filter(Relation.user_id == self.userid, Relation.relation == Relation.RELATION.FOLLOW). \
            order_by(Relation.update_time.desc()).all()  # 直接从数据库中将所有数据取出, 只缓存分页可能导致查询错误

    def update(self, author_id, timestamp=None, is_follow=True):
        """关注/取消关注"""

        is_key_exist = redis_cluster.exists(self.key)
        if not is_key_exist:  # 如果没有缓存, 则不需要更新缓存数据
            return

        if is_follow:  # 关注用户

            redis_cluster.zadd(self.key, author_id, timestamp)

        else:  # 取消关注
            redis_cluster.zrem(self.key, author_id)


# user:<用户id>:fans  zset  [{value: 用户id, score: 被关注时间}, {}, {}]
class UserFansCache(BaseFollowCache):
    """用户粉丝列表缓存类"""

    count_key = 'fans_count'
    attr_key = 'user_id'

    def __init__(self, userid):
        super().__init__(userid)
        self.key = "user:{}:fans".format(userid)  # redis的键

    def db_query(self):
        # 当前用户的粉丝列表 (取出的字段: userid, 关注时间) 关注时间倒序排序
        return Relation.query.options(load_only(Relation.user_id, Relation.update_time)).\
            filter(Relation.author_id == self.userid, Relation.relation == Relation.RELATION.FOLLOW).\
            order_by(Relation.update_time.desc()).all()


    def has_fans(self, fans_id):
        """判断传入的id是否是当前用户的粉丝"""

        # 先判断是否有缓存
        is_key_exist = redis_cluster.exists(self.key)
        if not is_key_exist: # 如果没有缓存, 先生成缓存
           items = self.get(1, 1)
           if len(items) == 0: # 用过该用户没有粉丝:
                return False

        # 判断id是否为当前用户的粉丝
        score = redis_cluster.zscore(self.key, fans_id)
        return True if score else False
