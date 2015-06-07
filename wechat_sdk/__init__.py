# -*- coding: utf-8 -*-

__all__ = ['WechatBasic', 'WechatExt']

try:
    from wechat_sdk.basic import WechatBasic
    from wechat_sdk.ext import WechatExt
    from wechat_sdk.corp import WechatCorp
except ImportError:
    pass