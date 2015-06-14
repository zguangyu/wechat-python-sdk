# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
import json
import unittest

import xmltodict
from httmock import urlmatch, HTTMock, response

from wechat_sdk import WechatBasic
from wechat_sdk.exceptions import NeedParamError, ParseError
from wechat_sdk.messages import TextMessage, ImageMessage, VoiceMessage, VideoMessage, ShortVideoMessage, LinkMessage, LocationMessage, UnknownMessage


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

    def test_parse_data_text_message(self):
        # 测试错误消息解析
        bad_message = 'xml>a2341'
        wechat = WechatBasic()
        with self.assertRaises(ParseError):
            wechat.parse_data(data=bad_message)

        # 测试正确消息解析
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
