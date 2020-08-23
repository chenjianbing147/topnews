from qiniu import Auth, put_data
from flask import current_app

def upload_file(data):
    """
    七牛云上传问价
    :param data: 上传的二进制数据
    :return: 七牛云上的文件名
    """

    AK = current_app.config['QINIU_ACCESS_KEY']
    SK = current_app.config['QINIU_SECRET_KEY']
    # 构建监权对象
    q = Auth(access_key=AK, secret_key=SK)
    # 要上传的空间
    bucket_name = 'hmsh36topnews'

    # 上传后保存的文件名
    key = None  # 如果设置为None, 七牛云会自动给文件起名

    # 生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, key, 3600)

    ret, info = put_data(token, key, data)
    if info.status_code == 200:  # 上传成功
        return current_app.config['QINIU_DOMAIN'] + ret.get('key')

    else:
        raise BaseException(info.error)

