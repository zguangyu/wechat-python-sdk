# -*- coding: utf-8 -*-

from wechat_sdk.exceptions import WechatAPIException, WechatSDKException


class CorpSignatureError(WechatSDKException):
    """微信企业号开启应用的回调模式校验异常"""
    pass
