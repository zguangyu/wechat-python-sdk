# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals
import unittest
import six
import time


class MessagesTestCase(unittest.TestCase):
    """消息类测试"""

    def test_base_message(self):
        from wechat_sdk.messages import WechatMessage

        timestamp = int(time.time())
        message = WechatMessage({
            'MsgId': '214111234',
            'ToUserName': 'doraemonext',
            'FromUserName': 'fromusername',
            'CreateTime': timestamp,
        })

        self.assertEqual(message.id, 214111234)
        self.assertEqual(message.target, 'doraemonext')
        self.assertEqual(message.source, 'fromusername')
        self.assertEqual(message.time, timestamp)

    def test_text_message(self):
        from wechat_sdk.messages import TextMessage

        message = TextMessage({
            'Content': 'This is a test message',
        })

        self.assertEqual(message.content, 'This is a test message')

    def test_image_message(self):
        from wechat_sdk.messages import ImageMessage

        message = ImageMessage({
            'PicUrl': 'http://www.baidu.com/logo.gif',
            'MediaId': '12341341324',
        })

        self.assertEqual(message.picurl, 'http://www.baidu.com/logo.gif')
        self.assertEqual(message.media_id, '12341341324')

    def test_video_message(self):
        from wechat_sdk.messages import VideoMessage

        message = VideoMessage({
            'MediaId': '234234234',
            'ThumbMediaId': '12314444',
        })

        self.assertEqual(message.media_id, '234234234')
        self.assertEqual(message.thumb_media_id, '12314444')

    def test_short_video_message(self):
        from wechat_sdk.messages import ShortVideoMessage

        message = ShortVideoMessage({
            'MediaId': '123413412',
            'ThumbMediaId': '12341111',
        })

        self.assertEqual(message.media_id, '123413412')
        self.assertEqual(message.thumb_media_id, '12341111')

    def test_location_message(self):
        from wechat_sdk.messages import LocationMessage

        message = LocationMessage({
            'Location_X': '23.2111',
            'Location_Y': '11.111',
            'Scale': 2,
            'Label': 'label test',
        })

        self.assertEqual(message.location, (23.2111, 11.111))
        self.assertEqual(message.scale, 2)
        self.assertEqual(message.label, 'label test')

    def test_link_message(self):
        from wechat_sdk.messages import LinkMessage

        message = LinkMessage({
            'Title': '你好这里是链接',
            'Description': '描述',
            'Url': 'http://www.baidu.com',
        })

        self.assertEqual(message.title, '你好这里是链接')
        self.assertEqual(message.description, '描述')
        self.assertEqual(message.url, 'http://www.baidu.com')

    def test_event_subscribe_no_ticket_message(self):
        from wechat_sdk.messages import EventMessage

        message = EventMessage({
            'Event': 'subscribe',
        })

        self.assertEqual(message.type, 'subscribe')

    def test_event_subscribe_ticket_message(self):
        from wechat_sdk.messages import EventMessage

        message = EventMessage({
            'Event': 'subscribe',
            'EventKey': 'event_key',
            'Ticket': 'ticket',
        })

        self.assertEqual(message.type, 'subscribe')
        self.assertEqual(message.key, 'event_key')
        self.assertEqual(message.ticket, 'ticket')
