# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals
import unittest
import six
import time
import xmltodict

from wechat_sdk.messages import WechatMessage
from wechat_sdk.utils import to_binary, to_text


class ReplyTestCase(unittest.TestCase):
    """回复类测试"""

    def setUp(self):
        self.message = WechatMessage({
            'MsgId': '214111234',
            'ToUserName': 'doraemonext',
            'FromUserName': 'fromusername',
            'CreateTime': int(time.time()),
        })

    def _common_reply_validation(self, resp_dict):
        self.assertEqual(resp_dict['ToUserName'], self.message.source)
        self.assertEqual(resp_dict['FromUserName'], self.message.target)
        self.assertEqual(resp_dict['CreateTime'], to_text(self.message.time))

    def test_base_reply_class(self):
        from wechat_sdk.reply import WechatReply

        reply = WechatReply(message=self.message)

        self.assertEqual(reply._args['source'], self.message.target)
        self.assertEqual(reply._args['target'], self.message.source)
        self.assertEqual(reply._args['time'], self.message.time)

    def test_text_reply(self):
        from wechat_sdk.reply import TextReply

        xml = TextReply(message=self.message, content='你好').render()
        resp_dict = xmltodict.parse(xml)['xml']

        self._common_reply_validation(resp_dict)
        self.assertEqual(resp_dict['MsgType'], 'text')
        self.assertEqual(resp_dict['Content'], '你好')

    def test_image_reply(self):
        from wechat_sdk.reply import ImageReply

        xml = ImageReply(message=self.message, media_id='1341234').render()
        resp_dict = xmltodict.parse(xml)['xml']

        self._common_reply_validation(resp_dict)
        self.assertEqual(resp_dict['MsgType'], 'image')
        self.assertEqual(resp_dict['Image']['MediaId'], '1341234')

    def test_voice_reply(self):
        from wechat_sdk.reply import VoiceReply

        xml = VoiceReply(message=self.message, media_id='111111').render()
        resp_dict = xmltodict.parse(xml)['xml']

        self._common_reply_validation(resp_dict)
        self.assertEqual(resp_dict['MsgType'], 'voice')
        self.assertEqual(resp_dict['Voice']['MediaId'], '111111')

    def test_video_reply(self):
        from wechat_sdk.reply import VideoReply

        xml = VideoReply(
            message=self.message,
            media_id='1223333',
            title='title',
            description='description',
        ).render()
        resp_dict = xmltodict.parse(xml)['xml']

        self._common_reply_validation(resp_dict)
        self.assertEqual(resp_dict['MsgType'], 'video')
        self.assertEqual(resp_dict['Video']['MediaId'], '1223333')
        self.assertEqual(resp_dict['Video']['Title'], 'title')
        self.assertEqual(resp_dict['Video']['Description'], 'description')

    def test_music_reply_without_thumb(self):
        from wechat_sdk.reply import MusicReply

        xml = MusicReply(
            message=self.message,
            title='title',
            description='description',
            music_url='http://mp3.baidu.com/',
            hq_music_url='http://mp4.baidu.com/',
        ).render()
        resp_dict = xmltodict.parse(xml)['xml']

        self._common_reply_validation(resp_dict)
        self.assertEqual(resp_dict['MsgType'], 'music')
        self.assertEqual(resp_dict['Music']['Title'], 'title')
        self.assertEqual(resp_dict['Music']['Description'], 'description')
        self.assertEqual(resp_dict['Music']['MusicUrl'], 'http://mp3.baidu.com/')
        self.assertEqual(resp_dict['Music']['HQMusicUrl'], 'http://mp4.baidu.com/')
        self.assertNotIn('ThumbMediaId', resp_dict['Music'])

    def test_music_reply_with_thumb(self):
        from wechat_sdk.reply import MusicReply

        xml = MusicReply(
            message=self.message,
            title='title',
            description='description',
            music_url='http://mp3.baidu.com/',
            hq_music_url='http://mp4.baidu.com/',
            thumb_media_id='1234134',
        ).render()
        resp_dict = xmltodict.parse(xml)['xml']

        self._common_reply_validation(resp_dict)
        self.assertEqual(resp_dict['MsgType'], 'music')
        self.assertEqual(resp_dict['Music']['Title'], 'title')
        self.assertEqual(resp_dict['Music']['Description'], 'description')
        self.assertEqual(resp_dict['Music']['MusicUrl'], 'http://mp3.baidu.com/')
        self.assertEqual(resp_dict['Music']['HQMusicUrl'], 'http://mp4.baidu.com/')
        self.assertEqual(resp_dict['Music']['ThumbMediaId'], '1234134')

    def test_article_reply(self):
        from wechat_sdk.reply import Article, ArticleReply

        articles = ArticleReply(message=self.message)
        articles.add_article(Article(
            title='title 1',
            description='description 1',
            picurl='picurl 1',
            url='url 1',
        ))
        articles.add_article(Article(
            title='title 2',
            description='description 2',
            picurl='picurl 2',
            url='url 2',
        ))
        articles.add_article(Article(
            title='title 3',
            description='description 3',
            picurl='picurl 3',
            url='url 3',
        ))
        xml = articles.render()
        resp_dict = xmltodict.parse(xml)['xml']

        self._common_reply_validation(resp_dict)
        self.assertEqual(resp_dict['MsgType'], 'news')
        self.assertEqual(resp_dict['ArticleCount'], to_text(3))

        self.assertEqual(resp_dict['Articles']['item'][0]['Title'], 'title 1')
        self.assertEqual(resp_dict['Articles']['item'][0]['Description'], 'description 1')
        self.assertEqual(resp_dict['Articles']['item'][0]['PicUrl'], 'picurl 1')
        self.assertEqual(resp_dict['Articles']['item'][0]['Url'], 'url 1')

        self.assertEqual(resp_dict['Articles']['item'][1]['Title'], 'title 2')
        self.assertEqual(resp_dict['Articles']['item'][1]['Description'], 'description 2')
        self.assertEqual(resp_dict['Articles']['item'][1]['PicUrl'], 'picurl 2')
        self.assertEqual(resp_dict['Articles']['item'][1]['Url'], 'url 2')

        self.assertEqual(resp_dict['Articles']['item'][2]['Title'], 'title 3')
        self.assertEqual(resp_dict['Articles']['item'][2]['Description'], 'description 3')
        self.assertEqual(resp_dict['Articles']['item'][2]['PicUrl'], 'picurl 3')
        self.assertEqual(resp_dict['Articles']['item'][2]['Url'], 'url 3')
