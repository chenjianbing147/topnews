from flask_restful import Resource
from flask import g
from flask import request
from sqlalchemy.orm import load_only

from models.article import Channel, UserChannel
from utils.decorators import login_required


class UserChannelResource(Resource):
    method_decorators = {'put':[login_required]}

    def get(self):
        # 获取用户id
        userid = g.userid

        if userid:
            channels = Channel.query.options(load_only(Channel.id, Channel.name)).join(UserChannel, Channel.id==UserChannel.channel_id).\
                filter(UserChannel.user_id==userid, UserChannel.is_deleted==False).order_by(UserChannel.sequence).all()

            # 如果用户是刚登录的新用户, 这时候用户还没添加频道, 频道是空的, 我们就要给他默认的
            if len(channels) == 0:
                channels = Channel.query.options(load_only(Channel.id, Channel.name)).filter(Channel.is_default==True).all()
        else:
            channels = Channel.query.options(load_only(Channel.id, Channel.name)).\
                filter(Channel.is_default == True).all()

        channel_list = [channel.to_dict() for channel in channels]

        # 小细节, 第一个都是推荐两个字
        channel_list.insert(0, {'id':0, 'name':'推荐'})

        return {'channels':channel_list}


    def put(self):
        """该接口需要登录"""
        channel_id = request.json.get('id')
        channels = request.json.get('channels')


        pass
