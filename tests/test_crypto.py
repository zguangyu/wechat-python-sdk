# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals
import unittest
import xmltodict

from wechat_sdk.crypto import WechatCrypto, WechatCorpCrypto


class CryptoTestCase(unittest.TestCase):
    """Crypto测试类"""

    token = '123456'
    encoding_aes_key = 'kWxPEV2UEDyxWpmPdKC3F4dgPDmOvfKX1HGnEUDS1aR'
    corp_id = 'wx49f0ab532d5d035a'

    def test_check_signature_should_ok(self):
        msg_signature = 'dd6b9c95b495b3f7e2901bfbc76c664930ffdb96'
        timestamp = '1411443780'
        nonce = '437374425'
        echostr = '4ByGGj+sVCYcvGeQYhaKIk1o0pQRNbRjxybjTGblXrBaXlTXe,Oo1+bXFXDQQb1o6co6Yh9Bv41n7hOchLF6p+Q=='  # NOQA

        crypto = WechatCorpCrypto(self.token, self.encoding_aes_key, self.corp_id)
        resp_echostr = crypto.check_signature(
            msg_signature=msg_signature,
            timestamp=timestamp,
            nonce=nonce,
            echostr=echostr,
        )

    def test_check_signature_should_fail(self):
        from wechat_sdk.crypto.exceptions import ValidateSignatureError

        signature = 'dd6b9c95b495b3f7e2901bfbc76c664930ffdb96'
        timestamp = '1411443780'
        nonce = '437374424'
        echo_str = '4ByGGj+sVCYcvGeQYhaKIk1o0pQRNbRjxybjTGblXrBaXlTXeOo1+bXFXDQQb1o6co6Yh9Bv41n7hOchLF6p+Q=='  # NOQA

        crypto = WechatCorpCrypto(self.token, self.encoding_aes_key, self.corp_id)
        self.assertRaises(
            ValidateSignatureError,
            crypto.check_signature,
            signature, timestamp, nonce, echo_str
        )
