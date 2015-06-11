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
        self.assertIsNone(message.key)
        self.assertIsNone(message.ticket)

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

    def test_event_unsubscribe(self):
        from wechat_sdk.messages import EventMessage

        message = EventMessage({
            'Event': 'unsubscribe',
        })

        self.assertEqual(message.type, 'unsubscribe')

    def test_event_scan_no_ticket_message(self):
        from wechat_sdk.messages import EventMessage

        message = EventMessage({
            'Event': 'scan',
        })

        self.assertEqual(message.type, 'scan')
        self.assertIsNone(message.key)
        self.assertIsNone(message.ticket)

    def test_event_scan_ticket_message(self):
        from wechat_sdk.messages import EventMessage

        message = EventMessage({
            'Event': 'scan',
            'EventKey': 'event_key',
            'Ticket': 'ticket',
        })

        self.assertEqual(message.type, 'scan')
        self.assertEqual(message.key, 'event_key')
        self.assertEqual(message.ticket, 'ticket')

    def test_event_click_message(self):
        from wechat_sdk.messages import EventMessage

        message = EventMessage({
            'Event': 'click',
            'EventKey': '你好'
        })

        self.assertEqual(message.type, 'click')
        self.assertEqual(message.key, '你好')

    def test_event_view_message(self):
        from wechat_sdk.messages import EventMessage

        message = EventMessage({
            'Event': 'view',
            'EventKey': 'http://www.baidu.com',
        })

        self.assertEqual(message.type, 'view')
        self.assertEqual(message.key, 'http://www.baidu.com')

    def test_event_scancode_push_message(self):
        from wechat_sdk.messages import EventMessage

        message = EventMessage({
            'Event': 'scancode_push',
            'EventKey': 'picture'
        })

        self.assertEqual(message.type, 'scancode_push')
        self.assertEqual(message.key, 'picture')

    def test_event_scancode_waitmsg_message(self):
        from wechat_sdk.messages import EventMessage

        message = EventMessage({
            'Event': 'scancode_waitmsg',
            'EventKey': 'waitmsg',
        })

        self.assertEqual(message.type, 'scancode_waitmsg')
        self.assertEqual(message.key, 'waitmsg')

    def test_event_pic_sysphoto_message(self):
        from wechat_sdk.messages import EventMessage

        message = EventMessage({
            'Event': 'pic_sysphoto',
            'EventKey': 'sysphoto',
        })

        self.assertEqual(message.type, 'pic_sysphoto')
        self.assertEqual(message.key, 'sysphoto')

    def test_event_pic_photo_or_album_message(self):
        from wechat_sdk.messages import EventMessage

        message = EventMessage({
            'Event': 'pic_photo_or_album',
            'EventKey': 'album',
        })

        self.assertEqual(message.type, 'pic_photo_or_album')
        self.assertEqual(message.key, 'album')

    def test_event_pic_weixin_message(self):
        from wechat_sdk.messages import EventMessage

        message = EventMessage({
            'Event': 'pic_weixin',
            'EventKey': 'weixin',
        })

        self.assertEqual(message.type, 'pic_weixin')
        self.assertEqual(message.key, 'weixin')

    def test_voice_message(self):
        from wechat_sdk.messages import EventMessage

        message = EventMessage({
            'Event': 'location',
            'Latitude': '2.112',
            'Longitude': '1.222',
            'Precision': '0.2',
        })

        self.assertEqual(message.type, 'location')
        self.assertEqual(message.latitude, 2.112)
        self.assertEqual(message.longitude, 1.222)
        self.assertEqual(message.precision, 0.2)

    def test_unknown_message(self):
        from wechat_sdk.messages import UnknownMessage

        message = UnknownMessage({})

        self.assertEqual(message.type, 'unknown')
