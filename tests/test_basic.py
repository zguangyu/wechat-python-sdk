# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
import json
import unittest

import xmltodict
from httmock import urlmatch, HTTMock, response

from wechat_sdk import WechatBasic
from wechat_sdk.exceptions import NeedParamError, ParseError
from wechat_sdk.messages import (
    TextMessage, ImageMessage, VoiceMessage, VideoMessage, ShortVideoMessage, LinkMessage,
    LocationMessage, EventMessage, UnknownMessage
)


TESTS_PATH = os.path.abspath(os.path.dirname(__file__))
FIXTURE_PATH = os.path.join(TESTS_PATH, 'fixtures')


@urlmatch(netloc=r'(.*\.)?api\.weixin\.qq\.com$')
def wechat_api_mock(url, request):
    path = url.path.replace('/cgi-bin/', '').replace('/', '_')
    if path.startswith('_'):
        path = path[1:]
    res_file = os.path.join(FIXTURE_PATH, '%s.json' % path)
    content = {
        'errcode': 99999,
        'errmsg': 'can not find fixture %s' % res_file,
    }
    headers = {
        'Content-Type': 'application/json'
    }
    try:
        with open(res_file, 'rb') as f:
            content = json.loads(f.read().decode('utf-8'))
    except (IOError, ValueError) as e:
        print(e)
    return response(200, content, headers, request=request)


class WechatBasicTestCase(unittest.TestCase):
    token = 'test_token'
    appid = 'wxn5rg4orc9ajgq0yb'
    appsecret = 'y5tjcmn76i4mrsdcyebxzkdv0h1qjefk'

    fixtures_access_token = 'HoVFaIslbrofqJgkR0Svcx2d4za0RJKa3H6A_NjzhBbm96Wtg_a3ifUYQvOfJmV76QTcCpNubcsnOLmDopu2hjWfFeQSCE4c8QrsxwE_N3w'
    fixtures_jsapi_ticket = 'bxLdikRXVbTPdHSM05e5u5sUoXNKd8-41ZO3MhKoyN5OfkWITDGgnr2fwJ0m9E8NYzWKVZvdVtaUgWvsdshFKA'

    test_message = """<xml>
<ToUserName><![CDATA[toUser]]></ToUserName>
<FromUserName><![CDATA[fromUser]]></FromUserName>
<CreateTime>1348831860</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[测试信息]]></Content>
<MsgId>1234567890123456</MsgId>
</xml>"""

    def test_check_signature(self):
        signature = '41f929117dd6231a953f632cfb3be174b8e3ef08'
        timestamp = '1434295379'
        nonce = 'ueivlkyhvdng46da0qxr52qzcjabjmo7'

        # 测试无 Token 初始化
        wechat = WechatBasic()
        with self.assertRaises(NeedParamError):
            wechat.check_signature(signature=signature, timestamp=timestamp, nonce=nonce)

        # 测试有 Token 初始化
        wechat = WechatBasic(token=self.token)
        self.assertTrue(wechat.check_signature(signature=signature, timestamp=timestamp, nonce=nonce))
        self.assertFalse(wechat.check_signature(signature=signature, timestamp=timestamp+'2', nonce=nonce))

    def test_grant_token(self):
        # 测试无 appid 和 appsecret 初始化
        wechat = WechatBasic()
        with self.assertRaises(NeedParamError):
            wechat.grant_token()

        # 测试有 appid 和 appsecret 初始化（覆盖已有 access_token，默认override=True即覆盖）
        wechat = WechatBasic(appid=self.appid, appsecret=self.appsecret)
        with HTTMock(wechat_api_mock):
            resp = wechat.grant_token()
            self.assertEqual(resp['access_token'], self.fixtures_access_token)
            self.assertEqual(resp['expires_in'], 7200)
            self.assertEqual(wechat._WechatBasic__access_token, self.fixtures_access_token)

        # 测试有 appid 和 appsecret 初始化（不覆盖已有 access_token）
        wechat = WechatBasic(appid=self.appid, appsecret=self.appsecret)
        with HTTMock(wechat_api_mock):
            resp = wechat.grant_token(override=False)
            self.assertEqual(resp['access_token'], self.fixtures_access_token)
            self.assertEqual(resp['expires_in'], 7200)
            self.assertEqual(wechat._WechatBasic__access_token, None)

    def test_grant_jsapi_ticket(self):
        # 测试无 appid 和 appsecret 初始化
        wechat = WechatBasic()
        with self.assertRaises(NeedParamError):
            wechat.grant_jsapi_ticket()

        # 测试有 appid 和 appsecret 初始化（覆盖已有 jsapi_ticket，默认override=True即覆盖）
        wechat = WechatBasic(appid=self.appid, appsecret=self.appsecret)
        with HTTMock(wechat_api_mock):
            resp = wechat.grant_jsapi_ticket()
            self.assertEqual(resp['errcode'], 0)
            self.assertEqual(resp['errmsg'], 'ok')
            self.assertEqual(resp['ticket'], self.fixtures_jsapi_ticket)
            self.assertEqual(resp['expires_in'], 7200)
            self.assertEqual(wechat._WechatBasic__jsapi_ticket, self.fixtures_jsapi_ticket)

        # 测试有 appid 和 appsecret 初始化（不覆盖已有 access_token）
        wechat = WechatBasic(appid=self.appid, appsecret=self.appsecret)
        with HTTMock(wechat_api_mock):
            resp = wechat.grant_jsapi_ticket(override=False)
            self.assertEqual(resp['errcode'], 0)
            self.assertEqual(resp['errmsg'], 'ok')
            self.assertEqual(resp['ticket'], self.fixtures_jsapi_ticket)
            self.assertEqual(resp['expires_in'], 7200)
            self.assertEqual(wechat._WechatBasic__jsapi_ticket, None)

    def test_access_token(self):
        # 测试无 appid 和 appsecret 初始化
        wechat = WechatBasic()
        with self.assertRaises(NeedParamError):
            print(wechat.access_token)

        # 测试有 appid 和 appsecret 初始化
        wechat = WechatBasic(appid=self.appid, appsecret=self.appsecret)
        with HTTMock(wechat_api_mock):
            access_token = wechat.access_token
            self.assertEqual(access_token, self.fixtures_access_token)

    def test_jsapi_ticket(self):
        # 测试无 appid 和 appsecret 初始化
        wechat = WechatBasic()
        with self.assertRaises(NeedParamError):
            print(wechat.jsapi_ticket)

        # 测试有 appid 和 appsecret 初始化
        wechat = WechatBasic(appid=self.appid, appsecret=self.appsecret)
        with HTTMock(wechat_api_mock):
            jsapi_ticket = wechat.jsapi_ticket
            self.assertEqual(jsapi_ticket, self.fixtures_jsapi_ticket)

    def test_generate_jsapi_signature(self):
        noncestr = 'Wm3WZYTPz0wzccnW'
        jsapi_ticket = 'sM4AOVdWfPE4DxkXGEs8VMCPGGVi4C3VM0P37wVUCFvkVAy_90u5h9nbSlYy3-Sl-HhTdfl2fzFy1AOcHKP7qg'  # NOQA
        timestamp = 1414587457
        url = 'http://mp.weixin.qq.com?params=value'

        # 测试无 appid 和 appsecret 初始化
        wechat = WechatBasic()
        with self.assertRaises(NeedParamError):
            wechat.generate_jsapi_signature(timestamp=timestamp, noncestr=noncestr, url=url)

        # 测试有 appid 和 appsecret 初始化
        wechat = WechatBasic(appid=self.appid, appsecret=self.appsecret)
        with HTTMock(wechat_api_mock):
            signature = wechat.generate_jsapi_signature(timestamp=timestamp, noncestr=noncestr, url=url, jsapi_ticket=jsapi_ticket)
            self.assertEqual(signature, '0f9de62fce790f9a083d5c99e95740ceb90c27ed')

    def test_parse_data_bad_message(self):
        bad_message = 'xml>a2341'
        wechat = WechatBasic()
        with self.assertRaises(ParseError):
            wechat.parse_data(data=bad_message)

    def test_parse_data_text_message(self):
        message = """<xml>
<ToUserName><![CDATA[toUser]]></ToUserName>
<FromUserName><![CDATA[fromUser]]></FromUserName>
<CreateTime>1348831860</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[this is a test]]></Content>
<MsgId>1234567890123456</MsgId>
</xml>"""

        wechat = WechatBasic()
        wechat.parse_data(data=message)
        message = wechat.message

        self.assertIsInstance(message, TextMessage)
        self.assertEqual(message.id, 1234567890123456)
        self.assertEqual(message.target, 'toUser')
        self.assertEqual(message.source, 'fromUser')
        self.assertEqual(message.time, 1348831860)
        self.assertEqual(message.type, 'text')
        self.assertEqual(message.content, 'this is a test')

    def test_parse_data_image_message(self):
        message = """<xml>
<ToUserName><![CDATA[toUser]]></ToUserName>
<FromUserName><![CDATA[fromUser]]></FromUserName>
<CreateTime>1348831860</CreateTime>
<MsgType><![CDATA[image]]></MsgType>
<PicUrl><![CDATA[this is a url]]></PicUrl>
<MediaId><![CDATA[media_id]]></MediaId>
<MsgId>1234567890123456</MsgId>
</xml>"""

        wechat = WechatBasic()
        wechat.parse_data(data=message)
        message = wechat.message

        self.assertIsInstance(message, ImageMessage)
        self.assertEqual(message.id, 1234567890123456)
        self.assertEqual(message.target, 'toUser')
        self.assertEqual(message.source, 'fromUser')
        self.assertEqual(message.time, 1348831860)
        self.assertEqual(message.type, 'image')
        self.assertEqual(message.media_id, 'media_id')

    def test_parse_data_voice_message(self):
        message = """<xml>
<ToUserName><![CDATA[toUser]]></ToUserName>
<FromUserName><![CDATA[fromUser]]></FromUserName>
<CreateTime>1357290913</CreateTime>
<MsgType><![CDATA[voice]]></MsgType>
<MediaId><![CDATA[media_id]]></MediaId>
<Format><![CDATA[Format]]></Format>
<MsgId>1234567890123456</MsgId>
</xml>"""

        wechat = WechatBasic()
        wechat.parse_data(data=message)
        message = wechat.message

        self.assertIsInstance(message, VoiceMessage)
        self.assertEqual(message.id, 1234567890123456)
        self.assertEqual(message.target, 'toUser')
        self.assertEqual(message.source, 'fromUser')
        self.assertEqual(message.time, 1357290913)
        self.assertEqual(message.type, 'voice')
        self.assertEqual(message.media_id, 'media_id')
        self.assertEqual(message.format, 'Format')
        self.assertIsNone(message.recognition)

    def test_parse_data_voice_recognition(self):
        message = """<xml>
<ToUserName><![CDATA[toUser]]></ToUserName>
<FromUserName><![CDATA[fromUser]]></FromUserName>
<CreateTime>1357290913</CreateTime>
<MsgType><![CDATA[voice]]></MsgType>
<MediaId><![CDATA[media_id]]></MediaId>
<Format><![CDATA[Format]]></Format>
<Recognition><![CDATA[腾讯微信团队]]></Recognition>
<MsgId>1234567890123456</MsgId>
</xml>"""

        wechat = WechatBasic()
        wechat.parse_data(data=message)
        message = wechat.message

        self.assertIsInstance(message, VoiceMessage)
        self.assertEqual(message.id, 1234567890123456)
        self.assertEqual(message.target, 'toUser')
        self.assertEqual(message.source, 'fromUser')
        self.assertEqual(message.time, 1357290913)
        self.assertEqual(message.type, 'voice')
        self.assertEqual(message.media_id, 'media_id')
        self.assertEqual(message.format, 'Format')
        self.assertEqual(message.recognition, '腾讯微信团队')

    def test_parse_data_video_message(self):
        message = """<xml>
<ToUserName><![CDATA[toUser]]></ToUserName>
<FromUserName><![CDATA[fromUser]]></FromUserName>
<CreateTime>1357290913</CreateTime>
<MsgType><![CDATA[video]]></MsgType>
<MediaId><![CDATA[media_id]]></MediaId>
<ThumbMediaId><![CDATA[thumb_media_id]]></ThumbMediaId>
<MsgId>1234567890123456</MsgId>
</xml>"""

        wechat = WechatBasic()
        wechat.parse_data(data=message)
        message = wechat.message

        self.assertIsInstance(message, VideoMessage)
        self.assertEqual(message.id, 1234567890123456)
        self.assertEqual(message.target, 'toUser')
        self.assertEqual(message.source, 'fromUser')
        self.assertEqual(message.time, 1357290913)
        self.assertEqual(message.type, 'video')
        self.assertEqual(message.media_id, 'media_id')
        self.assertEqual(message.thumb_media_id, 'thumb_media_id')

    def test_parse_data_short_video_message(self):
        message = """<xml>
<ToUserName><![CDATA[toUser]]></ToUserName>
<FromUserName><![CDATA[fromUser]]></FromUserName>
<CreateTime>1357290913</CreateTime>
<MsgType><![CDATA[shortvideo]]></MsgType>
<MediaId><![CDATA[media_id]]></MediaId>
<ThumbMediaId><![CDATA[thumb_media_id]]></ThumbMediaId>
<MsgId>1234567890123456</MsgId>
</xml>"""

        wechat = WechatBasic()
        wechat.parse_data(data=message)
        message = wechat.message

        self.assertIsInstance(message, ShortVideoMessage)
        self.assertEqual(message.id, 1234567890123456)
        self.assertEqual(message.target, 'toUser')
        self.assertEqual(message.source, 'fromUser')
        self.assertEqual(message.time, 1357290913)
        self.assertEqual(message.type, 'shortvideo')
        self.assertEqual(message.media_id, 'media_id')
        self.assertEqual(message.thumb_media_id, 'thumb_media_id')

    def test_parse_data_location_message(self):
        message = """<xml>
<ToUserName><![CDATA[toUser]]></ToUserName>
<FromUserName><![CDATA[fromUser]]></FromUserName>
<CreateTime>1351776360</CreateTime>
<MsgType><![CDATA[location]]></MsgType>
<Location_X>23.134521</Location_X>
<Location_Y>113.358803</Location_Y>
<Scale>20</Scale>
<Label><![CDATA[位置信息]]></Label>
<MsgId>1234567890123456</MsgId>
</xml>"""

        wechat = WechatBasic()
        wechat.parse_data(data=message)
        message = wechat.message

        self.assertIsInstance(message, LocationMessage)
        self.assertEqual(message.id, 1234567890123456)
        self.assertEqual(message.target, 'toUser')
        self.assertEqual(message.source, 'fromUser')
        self.assertEqual(message.time, 1351776360)
        self.assertEqual(message.type, 'location')
        self.assertEqual(message.location, (23.134521, 113.358803))
        self.assertEqual(message.scale, 20)
        self.assertEqual(message.label, '位置信息')

    def test_parse_data_link_message(self):
        message = """<xml>
<ToUserName><![CDATA[toUser]]></ToUserName>
<FromUserName><![CDATA[fromUser]]></FromUserName>
<CreateTime>1351776360</CreateTime>
<MsgType><![CDATA[link]]></MsgType>
<Title><![CDATA[公众平台官网链接]]></Title>
<Description><![CDATA[公众平台官网链接]]></Description>
<Url><![CDATA[url]]></Url>
<MsgId>1234567890123456</MsgId>
</xml>"""

        wechat = WechatBasic()
        wechat.parse_data(data=message)
        message = wechat.message

        self.assertIsInstance(message, LinkMessage)
        self.assertEqual(message.id, 1234567890123456)
        self.assertEqual(message.target, 'toUser')
        self.assertEqual(message.source, 'fromUser')
        self.assertEqual(message.time, 1351776360)
        self.assertEqual(message.type, 'link')
        self.assertEqual(message.title, '公众平台官网链接')
        self.assertEqual(message.description, '公众平台官网链接')
        self.assertEqual(message.url, 'url')

    def test_parse_data_subscribe_event(self):
        message = """<xml>
<ToUserName><![CDATA[toUser]]></ToUserName>
<FromUserName><![CDATA[FromUser]]></FromUserName>
<CreateTime>123456789</CreateTime>
<MsgType><![CDATA[event]]></MsgType>
<Event><![CDATA[subscribe]]></Event>
</xml>"""

        wechat = WechatBasic()
        wechat.parse_data(data=message)
        message = wechat.message

        self.assertIsInstance(message, EventMessage)
        self.assertEqual(message.type, 'subscribe')
        self.assertEqual(message.target, 'toUser')
        self.assertEqual(message.source, 'FromUser')
        self.assertEqual(message.time, 123456789)
        self.assertIsNone(message.ticket)
        self.assertIsNone(message.key)

    def test_parse_data_unsubscribe_event(self):
        message = """<xml>
<ToUserName><![CDATA[toUser]]></ToUserName>
<FromUserName><![CDATA[FromUser]]></FromUserName>
<CreateTime>123456789</CreateTime>
<MsgType><![CDATA[event]]></MsgType>
<Event><![CDATA[unsubscribe]]></Event>
</xml>"""

        wechat = WechatBasic()
        wechat.parse_data(data=message)
        message = wechat.message

        self.assertIsInstance(message, EventMessage)
        self.assertEqual(message.type, 'unsubscribe')
        self.assertEqual(message.target, 'toUser')
        self.assertEqual(message.source, 'FromUser')
        self.assertEqual(message.time, 123456789)

    def test_parse_data_subscribe_qrscene_event(self):
        message = """<xml>
<ToUserName><![CDATA[toUser]]></ToUserName>
<FromUserName><![CDATA[FromUser]]></FromUserName>
<CreateTime>123456789</CreateTime>
<MsgType><![CDATA[event]]></MsgType>
<Event><![CDATA[subscribe]]></Event>
<EventKey><![CDATA[qrscene_123123]]></EventKey>
<Ticket><![CDATA[TICKET]]></Ticket>
</xml>"""

        wechat = WechatBasic()
        wechat.parse_data(data=message)
        message = wechat.message

        self.assertIsInstance(message, EventMessage)
        self.assertEqual(message.type, 'subscribe')
        self.assertEqual(message.target, 'toUser')
        self.assertEqual(message.source, 'FromUser')
        self.assertEqual(message.time, 123456789)
        self.assertEqual(message.key, 'qrscene_123123')
        self.assertEqual(message.ticket, 'TICKET')

    def test_parse_data_scan_event(self):
        message = """<xml>
<ToUserName><![CDATA[toUser]]></ToUserName>
<FromUserName><![CDATA[FromUser]]></FromUserName>
<CreateTime>123456789</CreateTime>
<MsgType><![CDATA[event]]></MsgType>
<Event><![CDATA[SCAN]]></Event>
<EventKey><![CDATA[SCENE_VALUE]]></EventKey>
<Ticket><![CDATA[TICKET]]></Ticket>
</xml>"""

        wechat = WechatBasic()
        wechat.parse_data(data=message)
        message = wechat.message

        self.assertIsInstance(message, EventMessage)
        self.assertEqual(message.type, 'scan')
        self.assertEqual(message.target, 'toUser')
        self.assertEqual(message.source, 'FromUser')
        self.assertEqual(message.time, 123456789)
        self.assertEqual(message.key, 'SCENE_VALUE')
        self.assertEqual(message.ticket, 'TICKET')

    def test_parse_data_location_event(self):
        message = """<xml>
<ToUserName><![CDATA[toUser]]></ToUserName>
<FromUserName><![CDATA[fromUser]]></FromUserName>
<CreateTime>123456789</CreateTime>
<MsgType><![CDATA[event]]></MsgType>
<Event><![CDATA[LOCATION]]></Event>
<Latitude>23.137466</Latitude>
<Longitude>113.352425</Longitude>
<Precision>119.385040</Precision>
</xml>"""

        wechat = WechatBasic()
        wechat.parse_data(data=message)
        message = wechat.message

        self.assertIsInstance(message, EventMessage)
        self.assertEqual(message.type, 'location')
        self.assertEqual(message.target, 'toUser')
        self.assertEqual(message.source, 'fromUser')
        self.assertEqual(message.time, 123456789)
        self.assertEqual(message.latitude, 23.137466)
        self.assertEqual(message.longitude, 113.352425)
        self.assertEqual(message.precision, 119.385040)

    def test_parse_data_click_event(self):
        message = """<xml>
<ToUserName><![CDATA[toUser]]></ToUserName>
<FromUserName><![CDATA[FromUser]]></FromUserName>
<CreateTime>123456789</CreateTime>
<MsgType><![CDATA[event]]></MsgType>
<Event><![CDATA[CLICK]]></Event>
<EventKey><![CDATA[EVENTKEY]]></EventKey>
</xml>"""

        wechat = WechatBasic()
        wechat.parse_data(data=message)
        message = wechat.message

        self.assertIsInstance(message, EventMessage)
        self.assertEqual(message.type, 'click')
        self.assertEqual(message.target, 'toUser')
        self.assertEqual(message.source, 'FromUser')
        self.assertEqual(message.time, 123456789)
        self.assertEqual(message.key, 'EVENTKEY')

    def test_parse_data_view_event(self):
        message = """<xml>
<ToUserName><![CDATA[toUser]]></ToUserName>
<FromUserName><![CDATA[FromUser]]></FromUserName>
<CreateTime>123456789</CreateTime>
<MsgType><![CDATA[event]]></MsgType>
<Event><![CDATA[VIEW]]></Event>
<EventKey><![CDATA[www.qq.com]]></EventKey>
</xml>"""

        wechat = WechatBasic()
        wechat.parse_data(data=message)
        message = wechat.message

        self.assertIsInstance(message, EventMessage)
        self.assertEqual(message.type, 'view')
        self.assertEqual(message.target, 'toUser')
        self.assertEqual(message.source, 'FromUser')
        self.assertEqual(message.time, 123456789)
        self.assertEqual(message.key, 'www.qq.com')

    def test_response_text(self):
        wechat = WechatBasic()
        wechat.parse_data(data=self.test_message)

        response_xml_1 = wechat.response_text('test message')
        response_xml_2 = wechat.response_text('测试文本')
        response_xml_3 = wechat.response_text(u'测试文本')
        response_xml_4 = wechat.response_text('<h1>你好</h1>')
        response_xml_5 = wechat.response_text('<h1>你好</h1>', escape=True)
        response_1 = xmltodict.parse(response_xml_1)
        response_2 = xmltodict.parse(response_xml_2)
        response_3 = xmltodict.parse(response_xml_3)
        response_4 = xmltodict.parse(response_xml_4)
        response_5 = xmltodict.parse(response_xml_5)

        self.assertEqual(response_1['xml']['ToUserName'], 'fromUser')
        self.assertEqual(response_1['xml']['FromUserName'], 'toUser')
        self.assertEqual(response_1['xml']['MsgType'], 'text')

        self.assertEqual(response_1['xml']['Content'], 'test message')
        self.assertEqual(response_2['xml']['Content'], '测试文本')
        self.assertEqual(response_3['xml']['Content'], '测试文本')
        self.assertEqual(response_4['xml']['Content'], '<h1>你好</h1>')
        self.assertEqual(response_5['xml']['Content'], '&lt;h1&gt;你好&lt;/h1&gt;')

    def test_response_image(self):
        wechat = WechatBasic()
        wechat.parse_data(data=self.test_message)

        resp_xml = wechat.response_image(media_id='xurkvi9gl')
        resp = xmltodict.parse(resp_xml)

        self.assertEqual(resp['xml']['ToUserName'], 'fromUser')
        self.assertEqual(resp['xml']['FromUserName'], 'toUser')
        self.assertEqual(resp['xml']['MsgType'], 'image')
        self.assertEqual(resp['xml']['Image']['MediaId'], 'xurkvi9gl')

    def test_response_voice(self):
        wechat = WechatBasic()
        wechat.parse_data(data=self.test_message)

        resp_xml = wechat.response_voice(media_id='xurkvi9gl')
        resp = xmltodict.parse(resp_xml)

        self.assertEqual(resp['xml']['ToUserName'], 'fromUser')
        self.assertEqual(resp['xml']['FromUserName'], 'toUser')
        self.assertEqual(resp['xml']['MsgType'], 'voice')
        self.assertEqual(resp['xml']['Voice']['MediaId'], 'xurkvi9gl')

    def test_response_video(self):
        wechat = WechatBasic()
        wechat.parse_data(data=self.test_message)

        resp_xml = wechat.response_video(
            media_id='xurkvi9gl',
            title='测试视频',
            description='测试描述',
        )
        resp = xmltodict.parse(resp_xml)

        self.assertEqual(resp['xml']['ToUserName'], 'fromUser')
        self.assertEqual(resp['xml']['FromUserName'], 'toUser')
        self.assertEqual(resp['xml']['MsgType'], 'video')
        self.assertEqual(resp['xml']['Video']['MediaId'], 'xurkvi9gl')
        self.assertEqual(resp['xml']['Video']['Title'], '测试视频')
        self.assertEqual(resp['xml']['Video']['Description'], '测试描述')

    def test_response_music(self):
        wechat = WechatBasic()
        wechat.parse_data(data=self.test_message)

        resp_xml = wechat.response_music(
            music_url='http://mp3.baidu.com',
            title='测试音乐',
            description='测试描述',
            hq_music_url='http://baidu.com/',
        )
        resp = xmltodict.parse(resp_xml)

        self.assertEqual(resp['xml']['ToUserName'], 'fromUser')
        self.assertEqual(resp['xml']['FromUserName'], 'toUser')
        self.assertEqual(resp['xml']['MsgType'], 'music')
        self.assertEqual(resp['xml']['Music']['Title'], '测试音乐')
        self.assertEqual(resp['xml']['Music']['Description'], '测试描述')
        self.assertEqual(resp['xml']['Music']['MusicUrl'], 'http://mp3.baidu.com')
        self.assertEqual(resp['xml']['Music']['HQMusicUrl'], 'http://baidu.com/')

    def test_response_news(self):
        wechat = WechatBasic()
        wechat.parse_data(data=self.test_message)

        resp_xml = wechat.response_news(articles=[
            {
                'title': '第一条新闻标题',
                'description': '第一条新闻描述，这条新闻没有预览图',
                'url': 'http://www.google.com.hk/',
            }, {
                'title': '第二条新闻标题, 这条新闻无描述',
                'picurl': 'http://doraemonext.oss-cn-hangzhou.aliyuncs.com/test/wechat-test.jpg',
                'url': 'http://www.github.com/',
            }, {
                'title': '第三条新闻标题',
                'description': '第三条新闻描述',
                'picurl': 'http://doraemonext.oss-cn-hangzhou.aliyuncs.com/test/wechat-test.jpg',
                'url': 'http://www.v2ex.com/',
            }
        ])
        resp = xmltodict.parse(resp_xml)

        self.assertEqual(resp['xml']['ToUserName'], 'fromUser')
        self.assertEqual(resp['xml']['FromUserName'], 'toUser')
        self.assertEqual(resp['xml']['MsgType'], 'news')
        self.assertEqual(resp['xml']['ArticleCount'], '3')

        self.assertEqual(resp['xml']['Articles']['item'][0]['Title'], '第一条新闻标题')
        self.assertEqual(resp['xml']['Articles']['item'][0]['Description'], '第一条新闻描述，这条新闻没有预览图')
        self.assertEqual(resp['xml']['Articles']['item'][0]['Url'], 'http://www.google.com.hk/')
        self.assertIsNone(resp['xml']['Articles']['item'][0]['PicUrl'])

        self.assertEqual(resp['xml']['Articles']['item'][1]['Title'], '第二条新闻标题, 这条新闻无描述')
        self.assertIsNone(resp['xml']['Articles']['item'][1]['Description'])
        self.assertEqual(resp['xml']['Articles']['item'][1]['Url'], 'http://www.github.com/')
        self.assertEqual(resp['xml']['Articles']['item'][1]['PicUrl'], 'http://doraemonext.oss-cn-hangzhou.aliyuncs.com/test/wechat-test.jpg')

        self.assertEqual(resp['xml']['Articles']['item'][2]['Title'], '第三条新闻标题')
        self.assertEqual(resp['xml']['Articles']['item'][2]['Description'], '第三条新闻描述')
        self.assertEqual(resp['xml']['Articles']['item'][2]['Url'], 'http://www.v2ex.com/')
        self.assertEqual(resp['xml']['Articles']['item'][2]['PicUrl'], 'http://doraemonext.oss-cn-hangzhou.aliyuncs.com/test/wechat-test.jpg')