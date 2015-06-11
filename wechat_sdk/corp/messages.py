# -*- coding: utf-8 -*-

from wechat_sdk.exceptions import ParseError

MESSAGE_TYPES = {}


def handle_for_type(type):
    def register(f):
        MESSAGE_TYPES[type] = f
        return f

    return register


class CorpMessage(object):
    def __init__(self, message):
        self.id = int(message.pop('MsgId', 0))
        self.target = message.pop('ToUserName', None)
        self.source = message.pop('FromUserName', None)
        self.time = int(message.pop('CreateTime', 0))
        self.agent = int(message.pop('AgentID', 0))
        self.__dict__.update(message)


@handle_for_type('text')
class TextMessage(CorpMessage):
    def __init__(self, message):
        self.content = message.pop('Content', '')
        super(TextMessage, self).__init__(message)


class UnknownMessage(CorpMessage):
    def __init__(self, message):
        self.type = 'unknown'
        super(UnknownMessage, self).__init__(message)
