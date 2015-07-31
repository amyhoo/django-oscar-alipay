#######################################################################################
# 支付宝网关:
# 生成请求url，验证支付宝支付信息
#######################################################################################

import requests
import six
import time
from pytz import timezone
from hashlib import md5
from datetime import datetime
from xml.etree import ElementTree
from collections import OrderedDict
from .exceptions import MissingParameter
from .exceptions import ParameterValueError
from .exceptions import TokenAuthorizationError
from .conf import *
from django.http import HttpResponseRedirect, HttpResponse
import urllib
if six.PY3:
    from urllib.parse import parse_qs, urlparse, unquote
else:
    from urlparse import parse_qs, urlparse, unquote

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode


def encode_dict(params):
    return {k: six.u(v).encode('utf-8')
            if isinstance(v, str) else v.encode('utf-8')
            if isinstance(v, six.string_types) else v
            for k, v in six.iteritems(params)}


class Alipay(object):
    GATEWAY_URL = ALIPAY_GATEWAY
    NOTIFY_GATEWAY_URL = NOTIFY_GATEWAY_URL

    def __init__(self, **kwargs):
        #pid=ALIPAY_PARTNER, key=ALIPAY_KEY, seller_email=ALIPAY_SELL_EMAIL, seller_id=ALIPAY_SELL_ID
        names=['key','_input_charset','partner','payment_type','sign_type']
        self._check_params(kwargs,names)
        self.key = kwargs.pop('key')
        self.pid = kwargs.get('partner')
        self.default_params = kwargs
        self.params=self.default_params.copy()#调用接口参数
        #加密方式
        self.sign_tuple = ('sign_type', kwargs.get('sign_type'), kwargs.get('sign_type'))
        self.sign_key = False
        if not {'seller_id','seller_account_name','seller_email'} & set(kwargs):
            raise ParameterValueError("seller_id,seller_account_name,seller_email and  must have one.")

    def _generate_md5_sign(self, params):
        #md5加密生成签名
        src = '&'.join(['%s=%s' % (key, value) for key,
                        value in sorted(params.items())]) + self.key
        return md5(src.encode('utf-8')).hexdigest()

    def _check_params(self, params, names):
        #检查params是否包含names中所有属性字符串
        if not all(k in params for k in names):
            raise MissingParameter('missing parameters')
        return

    def _build_sign_params(self,**params):
        #对参数params进行编码
        try:
            if 'sign_type' in params:params.pop('sign_type')
            if 'sign' in params:params.pop('sign')
        except KeyError:
            pass
        signkey, signvalue, signdescription = self.sign_tuple
        signmethod = getattr(self, '_generate_%s_sign' %
                             signdescription.lower())
        if signmethod is None:
            raise NotImplementedError("This type '%s' of sign is not implemented yet." %
                                      signdescription)
        if self.sign_key:
            params.update({signkey: signvalue})
        params.update({signkey: signvalue,'sign': signmethod(params)})
        return params

    def _build_url(self):
        #对已经加密过的kwargs生成get的请求地址
        params_signed=self._build_sign_params(**self.params)
        return '%s?%s' % (self.GATEWAY_URL, urlencode(params_signed))

    def _check_create_direct_pay_by_user(self, **kwargs):
        '''即时到帐'''
        self._check_params(kwargs, ['service','out_trade_no', 'subject'])
        if not kwargs.get('total_fee') and \
           not (kwargs.get('price') and kwargs.get('quantity')):
            raise ParameterValueError('total_fee or (price && quantiry) must have one.')
        return True

    def _check_create_partner_trade_by_buyer(self, **kwargs):
        '''担保交易'''
        names = ['service','out_trade_no', 'subject', 'logistics_type',
                 'logistics_fee', 'logistics_payment', 'price', 'quantity']
        self._check_params(kwargs, names)
        if not {'notify_url','return_url'} & set(kwargs):
            raise ParameterValueError("notify_url,return_url must have one.")

        return True

    def _check_send_goods_confirm_by_platform(self,**kwargs):
        '''确认发货接口'''
        self._check_params(kwargs,['service','trade_no','logistics_name','transport_type',])
        return True

    def _check_trade_create_by_buyer(self, **kwargs):
        '''标准双接口'''
        names = ['service','out_trade_no', 'subject', 'logistics_type',
                 'logistics_fee', 'logistics_payment', 'price', 'quantity']
        self._check_params(kwargs, names)
        return True

    def _check_add_alipay_qrcode(self, **kwargs):
        '''二维码管理 - 添加'''
        self._check_params(kwargs, ['service','biz_data', 'biz_type'])

        utcnow = datetime.utcnow()
        shanghainow = timezone('Asia/Shanghai').fromutc(utcnow)

        kwargs['method'] = 'add'
        kwargs['timestamp'] = shanghainow.strftime('%Y-%m-%d %H:%M:%S')
        return True

    def add_alipay_qrcode(self, **kwargs):
        if self._check_add_alipay_qrcode(kwargs):
            return requests.get(self._build_url(**kwargs))

    def get_sign_method(self, **kwargs):
        signkey, signvalue, signdescription = self.sign_tuple
        signmethod = getattr(self, '_generate_%s_sign' %
                             signdescription.lower())
        if signmethod is None:
            raise NotImplementedError("This type '%s' of sign is not implemented yet." %
                                      signdescription)
        return signmethod

    def verify_notify(self, **kwargs):
        #kwargs是支付宝返回信息，需要再次验证
        sign = kwargs.pop('sign')
        try:
            kwargs.pop('sign_type')
        except KeyError:
            pass
        params={key:kwargs[key][0] for key in kwargs}
        if self._build_sign_params(**params).get('sign') == sign[0]:
            return self.check_notify_remotely(**params)
        else:
            return False

    def check_notify_remotely(self, **kwargs):
        remote_result = requests.get(self.NOTIFY_GATEWAY_URL % (self.pid, kwargs['notify_id']),
                                     headers={'connection': 'close'}).text
        return remote_result == 'true'

    def request_url(self,**kwargs):
        self.params.update(kwargs)
        service=self.params.get('service')
        if service!='alipay.mobile.qrcode.manage':
            check_method=getattr(self,'_check_'+service)
        else:
            check_method=self._check_add_alipay_qrcode
        if check_method!=None:
            check_method(**kwargs)
            return self._build_url()

    #根据参数请求不同的支付宝服务，在请求时候更新self.params,添加如 订单号，价格，物流等信息
    def request(self,**kwargs):
        self.params.update(kwargs)
        if self.request_method=='get':
            service=self.params.get('service')
            if service!='alipay.mobile.qrcode.manage':
                check_method=getattr(self,'_check_'+service)
            else:
                check_method=self._check_add_alipay_qrcode
            if check_method!=None:
                check_method(kwargs)
                return HttpResponseRedirect(self._build_url())
            else:
                raise NotImplementedError("This type '%s' of sign is not implemented yet." %service)
        else:#采用post方法
            service=kwargs.get('service')
            if service!='alipay.mobile.qrcode.manage':
                check_method=getattr(self,'_check_'+service)
            else:
                check_method=self._check_add_alipay_qrcode
            if check_method!=None:
                check_method(kwargs)
                data=urllib.request.urlopen(self.GATEWAY_URL,self._build_sign_params(self.params))
                return HttpResponse(data)
            else:
                raise NotImplementedError("This type '%s' of sign is not implemented yet." %service)

