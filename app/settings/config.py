class DefaultConfig:
    """默认配置"""

    # mysql配置
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@192.168.19.128:3306/topnews'  # 数据迁移还要用到这个地址

    SQLALCHEMY_BINDS = {  # 主从数据库的URI
        "master": 'mysql://root:mysql@192.168.19.128:3306/hm_topnews',
        "slave1": 'mysql://root:mysql@192.168.19.128:3306/hm_topnews',
        "slave2": 'mysql://root:mysql@192.168.19.128:8306/hm_topnews'
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 是否追踪数据变化
    SQLALCHEMY_ECHO = True  # 是否打印底层执行的SQL

    # redis配置
    REDIS_HOST = '192.168.19.128'  # ip
    REDIS_PORT = 6381  # 端口

    JWT_SECRET = 'TPmi4aLWRbyVq8zu9v82dWYW17/z+UvRnYTt4P6fAXA'  # 秘钥
    JWT_EXPIRE_DAYS = 14  # JWT过期时间

    # 七牛云
    QINIU_ACCESS_KEY = '0MLvFSm_oBokle-vTlnq0vDvCaHX9qmgwyrNwNpY'
    QINIU_SECRET_KEY = 'Lj297mUQuC1OWXTredFGutkqt9Pqf8PlVjjQ3hhN'
    QINIU_BUCKET_NAME = 'hmsh36topnews'
    QINIU_DOMAIN = 'http://qfgqky63o.hn-bkt.clouddn.com/'

    # CORS
    CORS_ORIGINS = ['http://127.0.0.1:5000']  # 限定允许访问的域名, 不设置则全部允许

    # 设置哨兵的ip和端口
    SENTINEL_LIST = [
        ('192.168.105.140', 26380),
        ('192.168.105.140', 26381),
        ('192.168.105.140', 26382),
    ]

    SERVICE_NAME = 'mymaster'  # 哨兵配置的主数据库别名

config_dict = {
    'dev':DefaultConfig
}
