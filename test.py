"""
查看文件类型: 一般通过比对文件的头部字节来完成
"""

import imghdr  # 该模块中提供了一个函数what(), 可以校验文件是否为图片类型

with open('../66.jpg', 'rb') as f:
    # 方式1: 传递 文件路径/文件对象
    try:
        type = imghdr.what(f)  # 如果为图片, 则返回图片类型, 不是图片, 则返回None
        print(type)
    except:
        print(58)

    # 方式二: 设置第二个参数, 文件的二进制数据
    # data_bytes = f.read()
    # type = imghdr.what(None, data_bytes)
    # print(type)
