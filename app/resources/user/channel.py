from flask_restful import Resource
from flask import g
from flask import request
from sqlalchemy.orm import load_only

from app import db
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
        channels = request.json.get('channels')

        # 将现有的用户频道列表全部删除
        UserChannel.query.filter(UserChannel.user_id==g.userid).\
            update({'is_deleted':True})

        # 更新数据
        for channel in channels:
            # 查询频道数据
            user_channel = UserChannel.query.options(load_only(UserChannel.id)).\
                filter(UserChannel.user_id==g.userid, UserChannel.channel_id==channel['id']).first()
            if user_channel:
                # 虽然user_channel没有这个属性, 但是能添加属性
                # 如果频道在用户频道中, 修改记录 sequence is_delete
                user_channel.sequence = channel['seq']
                user_channel.is_delete = False

            else:
                # 如果频道没有在用户频道中, 添加记录 user_id channel_id sequence
                user_channel = UserChannel(user_id=g.userid, channel_id=channel['id'], sequence=channel['seq'])
                db.session.add(user_channel)

        # 提交事物
        db.session.commit()

        return {'channels':channels}

