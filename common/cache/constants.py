import random

# 方式1: 使用常量封装过期时间
# 缺点: 要求常量必须局部导入
# UserCacheTTL = 2 * 60 * 60 + random.randint(0, 500)


# 方法2: 使用函数封装过期时间的计算公式


# 方式3: 面向对象封装用户过期时间
# class UserCacheTTL:
#     """用户过期时间类"""
#     TTL = 60 * 60 * 2  # 过期时间基数
#     MAX_DELTA = 600  # 最大随机值
#
#     @classmethod
#     def get_val(cls):
#         return cls.TTL + cls.MAX_DELTA


class BaseCacheTTL:
    TTL = 60 * 60 * 2  # 过期时间基数
    MAX_DELTA = 600  # 最大随机数

    @classmethod
    def get_val(cls):
        return cls.TTL + random.randint(0, cls.MAX_DELTA)


class UserCacheTTL(BaseCacheTTL):
    """用户缓存过期时间类"""
    pass


class UserNotExistTTL(BaseCacheTTL):
    """用户不存在过期时间类"""
    TTL = 60 * 10  # 过期时间
    MAX_DELTA = 60  # 最大随机值


class UserFollowCacheTTL(BaseCacheTTL):
    pass


