# -*- coding: utf-8 -*-

import requests
import time
import json
import cgi
import random
from StringIO import StringIO

from wechat_sdk.base import WechatBase
from wechat_sdk.corp.messages import MESSAGE_TYPES, UnknownMessage
from wechat_sdk.corp.exceptions import CorpSignatureError, CorpStateError, CorpUserManagementError
from wechat_sdk.crypto import WechatCorpCrypto
from wechat_sdk.crypto.exceptions import ValidateSignatureError
from wechat_sdk.exceptions import ParseError, NeedParseError, NeedParamError, OfficialAPIError
from wechat_sdk.lib import XMLStore
from wechat_sdk.corp.reply import TextReply, ImageReply, VideoReply, VoiceReply, ArticleReply, Article
from wechat_sdk.utils import to_binary, to_text, disable_urllib3_warning


class WechatCorp(WechatBase):
    """微信企业号基本功能类"""

    def __init__(self, token, corp_id, secret, encoding_aes_key, agent_id, access_token=None,
                 access_token_expires_at=None, jsapi_ticket=None, jsapi_ticket_expires_at=None, checkssl=False):
        """构造函数

        :param token: Token 值
        :param corp_id: Corp ID
        :param secret: Corp Secret
        :param encoding_aes_key: EncodingAESKey
        :param agent_id: Agent ID (接收应用的ID)
        :param access_token: 直接导入的 access_token 值或 access_token 获取函数
        :param access_token_expires_at: 直接导入的 access_token 的过期日期（仅在 access_token 参数为非函数时使用）
        :param jsapi_ticket: 直接导入的 jsapi_ticket 值或 jsapi_ticket 获取函数
        :param jsapi_ticket_expires_at: 直接导入的 jsapi_ticket 的过期日期（仅在 jsapi_ticket 参数为非函数时使用）
        :param checkssl: 是否检查 SSL, 默认为 False, 可避免 urllib3 的 InsecurePlatformWarning 警告
        """
        if not checkssl:
            disable_urllib3_warning()  # 可解决 InsecurePlatformWarning 警告

        self.__token = token
        self.__corpid = corp_id
        self.__secret = secret
        self.__encoding_aes_key = encoding_aes_key
        self.__agent_id = agent_id
        self.__crypto = WechatCorpCrypto(self.__token, self.__encoding_aes_key, self.__corpid)

        self.__access_token = access_token
        self.__access_token_expires_at = access_token_expires_at
        self.__jsapi_ticket = jsapi_ticket
        self.__jsapi_ticket_expires_at = jsapi_ticket_expires_at

        self.__is_parse = False
        self.__message = None

    def grant_token(self, override=True):
        """
        获取 Access Token
        详情请参考 http://qydev.weixin.qq.com/wiki/index.php?title=%E4%B8%BB%E5%8A%A8%E8%B0%83%E7%94%A8
        :param override: 是否在获取的同时覆盖已有 access_token (默认为True)
        :return: 返回的 JSON 数据包
        :raise HTTPError: 微信api http 请求失败
        """
        self._check_corpid_secret()

        response_json = self._get(
            url="https://qyapi.weixin.qq.com/cgi-bin/gettoken",
            params={
                "corpid": self.__corpid,
                "corpsecret": self.__secret,
            }
        )
        if override:
            self.__access_token = response_json['access_token']
            self.__access_token_expires_at = int(time.time()) + response_json['expires_in']
        return response_json

    def get_access_token(self):
        """
        获取 Access Token 及 Access Token 过期日期, 仅供缓存使用, 如果希望得到原生的 Access Token 请求数据请使用 :func:`grant_token`
        :return: dict 对象, key 包括 `access_token` 及 `access_token_expires_at`
        """
        self._check_corpid_secret()

        return {
            'access_token': self.access_token,
            'access_token_expires_at': self.__access_token_expires_at,
        }

    def url_verify(self, msg_signature, timestamp, nonce, echostr):
        """
        回调URL信息验证
        详情请参考 http://qydev.weixin.qq.com/wiki/index.php?title=%E5%9B%9E%E8%B0%83%E6%A8%A1%E5%BC%8F
        :param msg_signature: 微信加密签名
        :param timestamp: 时间戳
        :param nonce: 随机数
        :param echostr: 加密的随机字符串
        :return: 验证URL成功，将sEchoStr返回给企业号
        """
        self._check_token_encoding_aes_key()

        if not msg_signature or not timestamp or not nonce or not echostr:
            raise CorpSignatureError(
                'Please provide msg_signature, timestamp, nonce and echostr parameter.'
            )
        try:
            return self.__crypto.check_signature(msg_signature, timestamp, nonce, echostr)
        except ValidateSignatureError:
            raise CorpSignatureError("validate signature error")

    def parse_data(self, msg_signature, timestamp, nonce, data):
        """
        解析微信服务器发送过来的数据并保存类中

        1.解析出url上的参数，包括消息体签名(msg_signature)，时间戳(timestamp)以及随机数字串(nonce)
        2.验证消息体签名的正确性。
        3.将post请求的数据进行xml解析，并将<Encrypt>标签的内容进行解密，解密出来的明文即是用户回复消息的明文，明文格式请参考官方文档

        :param data: HTTP Request 的 Body 数据
        :raise ParseError: 解析微信服务器数据错误, 数据不合法
        """
        result = {}
        if type(data) == unicode:
            data = data.encode('utf-8')
        elif type(data) == str:
            pass
        else:
            raise ParseError()

        msg = self.__crypto.decrypt_message(data, msg_signature, timestamp, nonce)
        try:
            xml = XMLStore(xmlstring=msg)
        except Exception:
            raise ParseError()

        result = xml.xml2dict
        result['raw'] = msg
        result['type'] = result.pop('MsgType').lower()

        message_type = MESSAGE_TYPES.get(result['type'], UnknownMessage)
        self.__message = message_type(result)
        self.__is_parse = True

    @property
    def message(self):
        return self.get_message()

    def get_message(self):
        """
        获取解析好的 CorpMessage 对象
        :return: 解析好的 CorpMessage 对象
        """
        self._check_parse()
        return self.__message

    def response_text(self, content, escape=False):
        """
        将文字信息 content 组装为符合微信服务器要求的响应数据
        :param content: 回复文字
        :param escape: 是否转义该文本内容 (默认不转义)
        :return: 符合微信服务器要求的 XML 响应数据
        """
        self._check_parse()

        content = self._transcoding(content)
        if escape:
            content = cgi.escape(content)

        response_xml = TextReply(message=self.__message, content=content).render()
        return self._encrypt_message(response_xml)

    def response_image(self, media_id):
        """
        将 media_id 所代表的图片组装为符合微信服务器要求的响应数据
        :param media_id: 图片的 MediaID
        :return: 符合微信服务器要求的 XML 响应数据
        """
        self._check_parse()

        response_xml = ImageReply(message=self.__message, media_id=media_id).render()
        return self._encrypt_message(response_xml)

    def response_voice(self, media_id):
        """
        将 media_id 所代表的语音组装为符合微信服务器要求的响应数据
        :param media_id: 语音的 MediaID
        :return: 符合微信服务器要求的 XML 响应数据
        """
        self._check_parse()

        response_xml = VoiceReply(message=self.__message, media_id=media_id).render()
        return self._encrypt_message(response_xml)

    def response_video(self, media_id, title=None, description=None):
        """
        将 media_id 所代表的视频组装为符合微信服务器要求的响应数据
        :param media_id: 视频的 MediaID
        :param title: 视频消息的标题
        :param description: 视频消息的描述
        :return: 符合微信服务器要求的 XML 响应数据
        """
        self._check_parse()

        title = self._transcoding(title)
        description = self._transcoding(description)

        response_xml = VideoReply(message=self.__message, media_id=media_id, title=title,
                                  description=description).render()
        return self._encrypt_message(response_xml)

    def response_news(self, articles):
        """
        将新闻信息组装为符合微信服务器要求的响应数据
        :param articles: list 对象, 每个元素为一个 dict 对象, key 包含 `title`, `description`, `picurl`, `url`
        :return: 符合微信服务器要求的 XML 响应数据
        """
        self._check_parse()

        for article in articles:
            if article.get('title'):
                article['title'] = self._transcoding(article['title'])
            if article.get('description'):
                article['description'] = self._transcoding(article['description'])
            if article.get('picurl'):
                article['picurl'] = self._transcoding(article['picurl'])
            if article.get('url'):
                article['url'] = self._transcoding(article['url'])

        news = ArticleReply(message=self.__message)
        for article in articles:
            article = Article(**article)
            news.add_article(article)
        response_xml = news.render()
        return self._encrypt_message(response_xml)

    def create_department(self, name, parentid=1, order=None):
        """
            创建部门
            name    : 部门名称。长度限制为1~64个字符
            parentid: 父亲部门id。根部门id为1
            order   : 在父部门中的次序。从1开始，数字越大排序越靠后
        """
        self._check_corpid_secret()

        data = {
            "name": name,
            "parentid": parentid
        }
        if order is not None:
            data["order"] = order
        response_json = self._post(
            url="https://qyapi.weixin.qq.com/cgi-bin/department/create",
            data=data
        )
        return response_json

    def update_department(self, department_id, **kwargs):
        """
            更新部门
            参数	必须	说明
            access_token	是	调用接口凭证
            id	是	部门id
            name	否	更新的部门名称。长度限制为1~64个字符。修改部门名称时指定该参数
            parentid	否	父亲部门id。根部门id为1
            order	否	在父部门中的次序。从1开始，数字越大排序越靠后
        """
        self._check_corpid_secret()

        data = {"id": department_id}
        data.update(kwargs)
        response_json = self._post(
            url="https://qyapi.weixin.qq.com/cgi-bin/department/update",
            data=data
        )
        return response_json

    def delete_department(self, department_id):
        """
            删除部门
            参数	必须	说明
            access_token	是	调用接口凭证
            id	是	部门id。（注：不能删除根部门；不能删除含有子部门、成员的部门）
        """
        self._check_corpid_secret()

        response_json = self._get(
            url="https://qyapi.weixin.qq.com/cgi-bin/department/delete",
            params={
                'access_token': self.access_token,
                'id': department_id,
            }
        )
        return response_json

    def get_department_list(self):
        """
            获取部门列表
            参数	必须	说明
            access_token	是	调用接口凭证
        """
        self._check_corpid_secret()

        response_json = self._get(
            url="https://qyapi.weixin.qq.com/cgi-bin/department/list",
            params={
                'access_token': self.access_token,
            }
        )
        return response_json

    def create_user(self, data):
        """
            创建用户
            参数	必须	说明
            data为json数据
            access_token	是	调用接口凭证
            userid	是	员工UserID。对应管理端的帐号，企业内必须唯一。长度为1~64个字符
            name	是	成员名称。长度为1~64个字符
            department	是	成员所属部门id列表。注意，每个部门的直属员工上限为1000个
            position	否	职位信息。长度为0~64个字符
            mobile	否	手机号码。企业内必须唯一，mobile/weixinid/email三者不能同时为空
            email	否	邮箱。长度为0~64个字符。企业内必须唯一
            weixinid	否	微信号。企业内必须唯一。（注意：是微信号，不是微信的名字）
            extattr	否	扩展属性。扩展属性需要在WEB管理端创建后才生效，否则忽略未知属性的赋值
        """
        self._check_corpid_secret()

        if data.get("userid") and data.get("name"):
            response_json = self._post(
                url="https://qyapi.weixin.qq.com/cgi-bin/user/create",
                data=data
            )
            return response_json
        else:
            raise CorpUserManagementError("Please provide userid and username parameter in the construction of class.")

    def delete_user(self, userid):
        """
            删除成员
            参数	必须	说明
            access_token	是	调用接口凭证
            userid	是	员工UserID。对应管理端的帐号
        """
        self._check_corpid_secret()

        response_json = self._get(
            url="https://qyapi.weixin.qq.com/cgi-bin/user/delete",
            params={
                'access_token': self.access_token,
                'userid': userid
            }
        )
        return response_json

    def multi_delete_user(self, useridlist):
        """
            批量删除成员
            参数	必须	说明
            access_token	是	调用接口凭证
            useridlist	是	员工UserID列表。对应管理端的帐号
        """
        self._check_corpid_secret()

        data = {
            "useridlist": useridlist
        }
        response_json = self._post(
            url="https://qyapi.weixin.qq.com/cgi-bin/user/batchdelete",
            data=data
        )
        return response_json

    def get_user(self, userid):
        """
            获取成员
            参数	必须	说明
            access_token	是	调用接口凭证
            userid	是	员工UserID。对应管理端的帐号
        """
        self._check_corpid_secret()

        response_json = self._get(
            url="https://qyapi.weixin.qq.com/cgi-bin/user/get",
            params={
                'access_token': self.access_token,
                'userid': userid
            }
        )
        return response_json

    def get_users_in_department(self, department_id, fetch_child=0, status=0):
        """
            获取部门成员
            参数	必须	说明
            access_token	是	调用接口凭证
            department_id	是	获取的部门id
            fetch_child	否	1/0：是否递归获取子部门下面的成员
            status	否	0获取全部员工，1获取已关注成员列表，2获取禁用成员列表，4获取未关注成员列表。status可叠加
        """
        self._check_corpid_secret()

        response_json = self._get(
            url="https://qyapi.weixin.qq.com/cgi-bin/user/simplelist",
            params={
                'access_token': self.access_token,
                'department_id': department_id,
                'fetch_child': fetch_child,
                'status': status
            }
        )
        return response_json

    def get_users_in_department_detail(self, department_id, fetch_child=0, status=0):
        """
            获取部门成员(详情)
            参数	必须	说明
            access_token	是	调用接口凭证
            department_id	是	获取的部门id
            fetch_child	否	1/0：是否递归获取子部门下面的成员
            status	否	0获取全部员工，1获取已关注成员列表，2获取禁用成员列表，4获取未关注成员列表。status可叠加
        """
        self._check_corpid_secret()

        response_json = self._get(
            url="https://qyapi.weixin.qq.com/cgi-bin/user/list",
            params={
                'access_token': self.access_token,
                'department_id': department_id,
                'fetch_child': fetch_child,
                'status': status
            }
        )
        return response_json

    def invite_attention_to_user(self, userid):
        """
            邀请用户关注
            参数	必须	说明
            access_token	是	调用接口凭证
            userid	是	用户的userid
            invite_tips	否	推送到微信上的提示语（只有认证号可以使用）。当使用微信推送时，该字段默认为“请关注XXX企业号”，邮件邀请时，该字段无效。
        """
        self._check_corpid_secret()

        data = {
            "userid": userid
        }
        response_json = self._post(
            url="https://qyapi.weixin.qq.com/cgi-bin/invite/send",
            data=data
        )
        return response_json

    def create_tag(self, tagname):
        """
            创建标签
            参数	必须	说明
            access_token	是	调用接口凭证
            tagname	是	标签名称。长度为1~64个字符，标签不可与其他同组的标签重名，也不可与全局标签重名
        """
        self._check_corpid_secret()

        response_json = self._post(
            url="https://qyapi.weixin.qq.com/cgi-bin/tag/create",
            data={
                "tagname": tagname
            }
        )
        return response_json

    def update_tag(self, tagid, tagname):
        """
            更新标签名字
            参数	必须	说明
            access_token	是	调用接口凭证
            tagid	是	标签ID
            tagname	是	标签名称。长度为1~64个字符，标签不可与其他同组的标签重名，也不可与全局标签重名
        """
        self._check_corpid_secret()

        response_json = self._post(
            url="https://qyapi.weixin.qq.com/cgi-bin/tag/update",
            data={
                "tagid": tagid,
                "tagname": tagname
            }
        )
        return response_json

    def delete_tag(self, tagid):
        """
            删除标签
            参数	必须	说明
            access_token	是	调用接口凭证
            tagid	是	标签ID
        """
        self._check_corpid_secret()

        response_json = self._get(
            url="https://qyapi.weixin.qq.com/cgi-bin/tag/delete",
            params={
                'access_token': self.access_token,
                'tagid': tagid
            }
        )
        return response_json

    def get_user_from_tag(self, tagid):
        """
            获取标签成员
            参数	必须	说明
            access_token	是	调用接口凭证
            tagid	是	标签ID
        """
        self._check_corpid_secret()

        response_json = self._get(
            url="https://qyapi.weixin.qq.com/cgi-bin/tag/get",
            params={
                'access_token': self.access_token,
                'tagid': tagid
            }
        )
        return response_json

    def add_users_to_tag(self, tagid, userlist, partylist):
        """
            增加标签成员
            参数	必须	说明
            access_token	是	调用接口凭证
            tagid	是	标签ID
            userlist	否	企业员工ID列表，注意：userlist、partylist不能同时为空
            partylist	否	企业部门ID列表，注意：userlist、partylist不能同时为空
        """
        self._check_corpid_secret()

        response_json = self._post(
            url="https://qyapi.weixin.qq.com/cgi-bin/tag/addtagusers",
            data={
                "tagid": tagid,
                "userlist": userlist,
                "partylist": partylist
            }
        )
        return response_json

    def delete_user_in_tag(self, tagid, userlist, partylist):
        """
            删除标签成员
            参数	必须	说明
            access_token	是	调用接口凭证
            tagid	是	标签ID
            userlist	否	企业员工ID列表，注意：userlist、partylist不能同时为空
            partylist	否	企业部门ID列表，注意：userlist、partylist不能同时为空
        """
        self._check_corpid_secret()

        response_json = self._post(
            url="https://qyapi.weixin.qq.com/cgi-bin/tag/deltagusers",
            data={
                "tagid": tagid,
                "userlist": userlist,
                "partylist": partylist
            }
        )
        return response_json

    @property
    def get_tag_list(self):
        """
            获取标签列表
            参数	必须	说明
            access_token	是	调用接口凭证
        """
        self._check_corpid_secret()

        response_json = self._get(
            url="https://qyapi.weixin.qq.com/cgi-bin/tag/list",
            params={
                'access_token': self.access_token
            }
        )
        return response_json

    def upload_media(self, media_type, media_file, extension=''):
        """
        上传多媒体文件
        详情请参考 http://qydev.weixin.qq.com/wiki/index.php?title=%E4%B8%8A%E4%BC%A0%E5%AA%92%E4%BD%93%E6%96%87%E4%BB%B6
        :param media_type: 媒体文件类型，分别有图片（image）、语音（voice）、视频（video）和缩略图（thumb）
        :param media_file: 要上传的文件，一个 File object 或 StringIO object
        :param extension: 如果 media_file 传入的为 StringIO object，那么必须传入 extension 显示指明该媒体文件扩展名，如 ``mp3``, ``amr``；如果 media_file 传入的为 File object，那么该参数请留空
        :return: 返回的 JSON 数据包
        :raise HTTPError: 微信api http 请求失败
        """
        self._check_corpid_secret()

        if not isinstance(media_file, file) and not isinstance(media_file, StringIO):
            raise ValueError('Parameter media_file must be file object or StringIO.StringIO object.')
        if isinstance(media_file, StringIO) and extension.lower() not in ['jpg', 'jpeg', 'amr', 'mp3', 'mp4']:
            raise ValueError(
                'Please provide \'extension\' parameters when the type of \'media_file\' is \'StringIO.StringIO\'.')
        if isinstance(media_file, file):
            extension = media_file.name.split('.')[-1]
            if extension.lower() not in ['jpg', 'jpeg', 'amr', 'mp3', 'mp4']:
                raise ValueError('Invalid file type.')

        ext = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'amr': 'audio/amr',
            'mp3': 'audio/mpeg',
            'mp4': 'video/mp4',
        }
        if isinstance(media_file, StringIO):
            filename = 'temp.' + extension
        else:
            filename = media_file.name

        return self._post(
            url='https://qyapi.weixin.qq.com/cgi-bin/media/upload',
            params={
                'access_token': self.access_token,
                'type': media_type,
            },
            files={
                'media': (filename, media_file, ext[extension])
            }
        )

    def download_media(self, media_id):
        """
        下载多媒体文件
        详情请参考 http://qydev.weixin.qq.com/wiki/index.php?title=%E8%8E%B7%E5%8F%96%E5%AA%92%E4%BD%93%E6%96%87%E4%BB%B6
        :param media_id: 媒体文件 ID
        :return: requests 的 Response 实例
        """
        self._check_corpid_secret()

        return requests.get(
            url='https://qyapi.weixin.qq.com/cgi-bin/media/get',
            params={
                'access_token': self.access_token,
                'media_id': media_id,
            },
            stream=True,
        )

    def get_agent(self):
        """
        获取企业号应用
        该API用于获取企业号某个应用的基本信息，包括头像、昵称、帐号类型、认证类型、可见范围等信息
        :param agentid:
        :return:
        """

        self._check_corpid_secret()

        response_json = self._get(
            url='https://qyapi.weixin.qq.com/cgi-bin/agent/get',
            params={
                'access_token': self.access_token,
                'agentid': self.__agent_id,
            }
        )

        return response_json

    def set_agent(self, **kwargs):
        """
        设置企业号应用
        该API用于设置企业应用的选项设置信息，如：地理位置上报等
        :param agentid:
        :return:
        """
        self._check_corpid_secret()

        data = {
            "agentid": self.__agent_id
        }
        data.update(kwargs)
        response_json = self._post(
            url="https://qyapi.weixin.qq.com/cgi-bin/agent/set",
            data=data
        )
        return response_json

    def send_text_message(self, content, touser=None, toparty=None, totag=None, safe=0):
        """
        发送文本消息
        详情请参考 http://qydev.weixin.qq.com/wiki/index.php?title=%E6%B6%88%E6%81%AF%E7%B1%BB%E5%9E%8B%E5%8F%8A%E6%95%B0%E6%8D%AE%E6%A0%BC%E5%BC%8F
        :param touser=None, toparty=None, totag=None 为发送对象
        :param content: 消息正文
        :return: 返回的 JSON 数据包
        :raise HTTPError: 微信api http 请求失败
        """
        self._check_corpid_secret()

        send_collection = self._send_collection(touser, toparty, totag)

        data = {
            "msgtype": "text",
            "agentid": self.__agent_id,
            "text": {
                "content": content
            },
            "safe": safe
        }

        data.update(send_collection)

        response_json = self._post(
            url='https://qyapi.weixin.qq.com/cgi-bin/message/send',
            data=data
        )
        return response_json

    def send_image_message(self, media_id, touser=None, toparty=None, totag=None, safe=0):
        """
        """
        self._check_corpid_secret()

        send_collection = self._send_collection(touser, toparty, totag)

        data = {
            "msgtype": "image",
            "agentid": self.__agent_id,
            "image": {
                "media_id": media_id
            },
            "safe": safe
        }

        data.update(send_collection)

        response_json = self._post(
            url='https://qyapi.weixin.qq.com/cgi-bin/message/send',
            data=data
        )
        return response_json

    def send_voice_message(self, media_id, touser=None, toparty=None, totag=None, safe=0):
        """
        """
        self._check_corpid_secret()

        send_collection = self._send_collection(touser, toparty, totag)

        data = {
            "msgtype": "voice",
            "agentid": self.__agent_id,
            "voice": {
                "media_id": media_id
            },
            "safe": safe
        }

        data.update(send_collection)

        response_json = self._post(
            url='https://qyapi.weixin.qq.com/cgi-bin/message/send',
            data=data
        )
        return response_json

    def send_video_message(self, media_id, title, description, touser=None, toparty=None, totag=None, safe=0):
        """
        """
        self._check_corpid_secret()
        send_collection = self._send_collection(touser, toparty, totag)

        data = {
            "msgtype": "video",
            "agentid": self.__agent_id,
            "video": {
                "media_id": media_id,
                "title": title,
                "description": description
            },
            "safe": safe
        }

        data.update(send_collection)

        response_json = self._post(
            url='https://qyapi.weixin.qq.com/cgi-bin/message/send',
            data=data
        )
        return response_json

    def send_file_message(self, media_id, touser=None, toparty=None, totag=None, safe=0):
        """
        """
        self._check_corpid_secret()
        send_collection = self._send_collection(touser, toparty, totag)

        data = {
            "msgtype": "file",
            "agentid": self.__agent_id,
            "file": {
                "media_id": media_id
            },
            "safe": safe
        }

        data.update(send_collection)

        response_json = self._post(
            url='https://qyapi.weixin.qq.com/cgi-bin/message/send',
            data=data
        )
        return response_json

    def send_news_message(self, articles, touser=None, toparty=None, totag=None, safe=0):
        """
        发送图文消息
        """
        self._check_corpid_secret()

        articles_data = []
        for article in articles:
            article = Article(**article)
            articles_data.append({
                'title': article.title,
                'description': article.description,
                'url': article.url,
                'picurl': article.picurl,
            })

        send_collection = self._send_collection(touser, toparty, totag)

        data = {
            "msgtype": "news",
            "agentid": self.__agent_id,
            "news": {
                "articles": articles_data
            },
            "safe": safe
        }

        data.update(send_collection)

        response_json = self._post(
            url='https://qyapi.weixin.qq.com/cgi-bin/message/send',
            data=data
        )
        return response_json

    def send_mpnews_message(self, articles, touser=None, toparty=None, totag=None, safe=0):
        """
        "articles":[
           {
               "title": "Title",
               "thumb_media_id": "id",
               "author": "Author",
               "content_source_url": "URL",
               "content": "Content",
               "digest": "Digest description",
               "show_cover_pic": "0"
           },
           {
               "title": "Title",
               "thumb_media_id": "id",
               "author": "Author",
               "content_source_url": "URL",
               "content": "Content",
               "digest": "Digest description",
               "show_cover_pic": "0"
           }
        ]
        """
        self._check_corpid_secret()

        send_collection = self._send_collection(touser, toparty, totag)

        data = {
            "msgtype": "mpnews",
            "agentid": self.__agent_id,
            "mpnews": {
                "articles": articles
            },
            "safe": safe
        }

        data.update(send_collection)

        response_json = self._post(
            url='https://qyapi.weixin.qq.com/cgi-bin/message/send',
            data=data
        )
        return response_json

    def _send_collection(self, touser, toparty, totag):
        data = {}
        if touser is None:
            to_user = "@all"
        else:
            to_user = '|'.join(touser)
        data["touser"] = to_user

        if toparty is not None:
            data["toparty"] = toparty

        if totag is not None:
            data["totag"] = totag

        return data

    @property
    def crypto(self):
        """返回加密类 (WechatCropyto)"""
        return self.__crypto

    def _encrypt_message(self, response_xml):
        """
        返回加密的xml信息，格式
        <xml>
            <Encrypt><![CDATA[     ]]></Encrypt>
            <MsgSignature><![CDATA[      ]]></MsgSignature>
            <TimeStamp>1433678396</TimeStamp>
            <Nonce><![CDATA[1372623149]]></Nonce>
        </xml>
        :param response_xml: 需要加密的xml数据
        :return:
        """
        timestamp = to_binary(int(time.time()))
        nonce = "".join(map(lambda x: to_binary(random.randint(1, 9)), range(16)))
        encrypted_message = self.__crypto.encrypt_message(response_xml.encode("utf-8"), nonce, timestamp)
        return encrypted_message

    @property
    def access_token(self):
        self._check_corpid_secret()

        if self.__access_token:
            now = time.time()
            if self.__access_token_expires_at - now > 60:
                return self.__access_token
        self.grant_token()
        return self.__access_token

    def _check_corpid_secret(self):
        """
        检查 CorpID, Corp Secret 是否存在
        :raises NeedParamError: Token 参数没有在初始化的时候提供
        """
        if not self.__corpid or not self.__secret:
            raise NeedParamError('Please provide corp_id and secret parameters in the construction of class.')

    def _check_token_encoding_aes_key(self):
        """
        检查 Token, EncodingAESKey 是否存在
        :raise NeedParamError: token 或 encoding_aes_key 参数没有在初始化的时候提供
        """
        if not self.__token or not self.__encoding_aes_key:
            raise NeedParamError('Please provide token and encoding_aes_key parameter in the construction of class.')

    def _check_parse(self):
        """
        检查是否成功解析微信服务器传来的数据
        :raises NeedParseError: 需要解析微信服务器传来的数据
        """
        if not self.__is_parse:
            raise NeedParseError()

    def _check_official_error(self, json_data):
        """
        检测微信公众平台返回值中是否包含错误的返回码
        :raises OfficialAPIError: 如果返回码提示有错误，抛出异常；否则返回 True
        """
        if "errcode" in json_data and json_data["errcode"] != 0:
            raise OfficialAPIError(errcode=json_data["errcode"], errmsg=json_data["errmsg"])

    def _request(self, method, url, **kwargs):
        """
        向微信服务器发送请求
        :param method: 请求方法
        :param url: 请求地址
        :param kwargs: 附加数据
        :return: 微信服务器响应的 json 数据
        :raise HTTPError: 微信api http 请求失败
        """
        if "params" not in kwargs:
            kwargs["params"] = {
                "access_token": self.access_token,
            }
        if isinstance(kwargs.get("data", ""), dict):
            body = json.dumps(kwargs["data"], ensure_ascii=False)
            body = body.encode('utf8')
            kwargs["data"] = body

        r = requests.request(
            method=method,
            url=url,
            **kwargs
        )
        r.raise_for_status()
        response_json = r.json()
        self._check_official_error(response_json)
        return response_json

    def _get(self, url, **kwargs):
        """
        使用 GET 方法向微信服务器发出请求
        :param url: 请求地址
        :param kwargs: 附加数据
        :return: 微信服务器响应的 json 数据
        :raise HTTPError: 微信api http 请求失败
        """
        return self._request(
            method="get",
            url=url,
            **kwargs
        )

    def _post(self, url, **kwargs):
        """
        使用 POST 方法向微信服务器发出请求
        :param url: 请求地址
        :param kwargs: 附加数据
        :return: 微信服务器响应的 json 数据
        :raise HTTPError: 微信api http 请求失败
        """
        return self._request(
            method="post",
            url=url,
            **kwargs
        )
