from sqlalchemy.orm import load_only

from app import redis_cluster
from models.user import User, Relation
from .constants import UserCacheTTL, UserNotExistTTL, UserFollowCacheTTL


class UserCache:
    """用户基础数据-缓存"""
    def __init__(self, userid):
        self.userid= userid
        self.key = "user:{}:basic".format(self.userid)

    def get(self):
        """获取缓存"""
        # 先从缓存中读取数据
        data = redis_cluster.hgetall(self.key)  # 键不存在返回空字典

        if data:  # 如果有返回数据
            if data.get('null'):  # 是默认值, 返回None
                return None
            else:  # 不是默认值, 返回数据
                return data

        else:  # 如果没有, 从数据库进行查询
            user = User.query.options(load_only(User.id, User.name, User.introduction, User.profile_photo,
        User.article_count, User.following_count, User.fans_count)).filter(User.id==self.userid).first()

            if user:  # 如果数据库有, 回填到缓存中, 并返回数据

                user_dict = user.to_dict()
                redis_cluster.hmset(self.key, user_dict)
                redis_cluster.expire(self.key, UserCacheTTL)

            else:  # 如果数据库没有, 在缓存中设置默认值(防止缓存穿透)
                redis_cluster.hmset(self.key, {'null':1})
                redis_cluster.expire(self.key, UserNotExistTTL)
                return None


    def clear(self):
        """删除缓存"""
        redis_cluster.delete(self.key)


class UserFollowCache:
    """用户关注列表缓存类"""

    def __init__(self, userid):
        self.userid = userid  # 用户主键
        self.key = "user:{}:following".format(userid)  # redis的键

    def get(self, page, per_page):
        """获取缓存列表"""

        # 先判断该键是否存在, 因为光凭查询结果就判断缓存存不存在不行,
        # 因为有可能索引有问题, 导致缓存存在, 去查数据库
        is_key_exist = redis_cluster.exists(self.key)

        # 根据页码和每条页数构建 开始索引 和结束索引
        start_index = (page - 1) * per_page
        end_index = start_index + per_page - 1

        if is_key_exist: # 如果缓存中有数据

            data = redis_cluster.zrevrange(self.key, start_index, end_index)
            return list(map(int, data))

        else:  # 如果缓存中没有
            # 缓存中没有, 就要去查数据库, 这里要考虑到可能用户表中都没有该用户关注的记录
            # 从而导致缓存穿透, 而要看数据库有没有用户关注的记录, 可以通过用户的关注数量判断
            user = UserCache(self.userid).get()
            if user and int(user['follow_count']):  # 如果该用户id确实存在而且确实有关注数量
                followings = Relation.query.options(load_only(Relation.author_id, Relation.update_time)). \
                    filter(Relation.user_id == self.userid, Relation.relation == Relation.RELATION.FOLLOW). \
                    order_by(Relation.update_time.desc()).all()  # 直接查询出所有数据并缓存, 只缓存分页数据可能导致查询错误

                # 如果有, 则应该回填数据, 并返回数据
                following_list = []
                for item in followings:
                    redis_cluster.zadd(self.key, item.author_id, item.update_time.timestamp())
                    following_list.append(item.author_id)

                # 设置过期时间
                redis_cluster.expire(self.key, UserFollowCacheTTL.get_val())

                return following_list[start_index:end_index+1]  # 取出分页数据

            else:  # 判断该用户没有关注数量, 直接返回空列表(通过判断关注数量, 避免了缓存穿透)
                return []

    def update(self, author_id, timestamp=None, is_follow=True):
        """关注/取消关注"""
        is_key_exist = redis_cluster.exists(self.key)
        if not is_key_exist:  # 如果没有缓存, 则不需要更新缓存数据
            return

        if is_follow:  # 关注用户
            redis_cluster.zadd(self.key, author_id, timestamp)

        else:  # 取消关注
            redis_cluster.zrem(self.key, author_id)




