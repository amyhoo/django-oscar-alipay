#######################################################################################
# 支付重定向:RedirectView
# 提交订单，向支付宝请求:ResponseView
# 支付宝回馈信息处理接口 ResponseView
# 取消订单 CancelView
# 该接口对应的支付源类型为:TaoBao_Warrant,需要在source_type里面添加该源类型
#######################################################################################
from django.views.generic import RedirectView, View,TemplateView
from alipay.conf import BASIC_PARAMS,BIZ_PARAMS,ALIPAY_KEY
from django.utils import six
import logging
from alipay.gatewayinfo import Alipay
from alipay.exceptions import AlipayException
import settings
from django.contrib.sites.models import Site
from django.http import HttpResponseRedirect,HttpResponse
from apps.checkout.mixins import RedirectSessionMixin
from oscar.core.loading import get_class, get_classes, get_model
PaymentDetailsView = get_class('checkout.views', 'PaymentDetailsView')
CheckoutSessionMixin = get_class('checkout.session', 'CheckoutSessionMixin')
OrderPlacementMixin = get_class('checkout.mixins', 'OrderPlacementMixin')
RedirectRequired, UnableToTakePayment, PaymentError \
    = get_classes('payment.exceptions', ['RedirectRequired',
                                         'UnableToTakePayment',
                                         'PaymentError'])
UnableToPlaceOrder = get_class('order.exceptions', 'UnableToPlaceOrder')
ShippingAddress = get_model('order', 'ShippingAddress')
Country = get_model('address', 'Country')
Basket = get_model('basket', 'Basket')
Repository = get_class('shipping.repository', 'Repository')
Applicator = get_class('offer.utils', 'Applicator')
Selector = get_class('partner.strategy', 'Selector')
Source = get_model('payment', 'Source')
SourceType = get_model('payment', 'SourceType')
logger = logging.getLogger('oscar.checkout')
from django.core.urlresolvers import reverse


class AlipaySessionMixin(RedirectSessionMixin):
    '''
    针对alipay_warrant支付方式的session管理控件，该控件对checkout_session进行管理，
    checkout_session是django-oscar的session管理控件，在支付完成后可以被自动清理。
    '''
    def set_aplaiy(self):
        params={key:BASIC_PARAMS[key] for key in BASIC_PARAMS if BASIC_PARAMS[key] !=None}
        alipay_gate=Alipay(**params)
        self.checkout_session._set('alipay','warrant',alipay_gate)
    def get_alipay(self):
        return self.checkout_session._get('alipay','warrant')

def AlipayHandle(paymentview,order_number, **kwargs):
    '''
    处理支付宝请求
    '''
        # 获取支付url
        # setting
    alipaymon=AlipaySessionMixin(paymentview.checkout_session)
    if settings.DEBUG:
            # Determine the localserver's hostname to use when
            # in testing mode8
            base_url = 'http://%s' % paymentview.request.META['HTTP_HOST']
    else:
            base_url = 'https://%s' % Site.objects.get_current().domain

    submission=alipaymon.get_info()
    gateway_info={
        'service':'create_partner_trade_by_buyer',
        'subject':submission['order_kwargs']['subject'],
        'price':submission.get('order_total').incl_tax-submission.get('shipping_charge').incl_tax,
        'quantity':1,#由于支付宝担保交易只支持单个商品,
        'logistics_fee':submission.get('shipping_charge').incl_tax,
        'logistics_type':'EXPRESS',#其他快递
        'logistics_payment':'BUYER_PAY',#买家承担
        'out_trade_no':order_number,
        'notify_url':"%s%s" % (base_url, reverse("taobao-warrant-answer")) ,
        'return_url':"%s%s" % (base_url, reverse("taobao-warrant-answer")) ,
         }
    gateway_info={key:gateway_info[key] for key in gateway_info if gateway_info[key]!=None}
    alipaymon.set_aplaiy()
    url=alipaymon.get_alipay().request_url(**gateway_info)
    raise RedirectRequired(url)

class ResponseView(AlipaySessionMixin,OrderPlacementMixin,View):
    '''
    收到支付宝信息处理，return_url,notify_url
    '''
    def paid_order_create(self,request,taobao_info, *args, **kwargs):
        order_number=self.get_order_number()
        info=self.get_info()
        info.pop('payment_kwargs')
        info.pop('order_kwargs')
        info['order_number']=order_number
        info['user']=self.request.user
        info['basket']=self.get_submitted_basket()

        #info['shipping_address']=taobao_info['receive_name']+','\
        #                         +taobao_info['receive_address']+','\
        #                         +taobao_info['receive_zip']

        # Assign strategy to basket instance
        if Selector:
            info['basket'].strategy = Selector().strategy(self.request)

        # Re-apply any offers
        #Applicator().apply(info['basket'],self.request.user,self.request )

        # Record payment source
        source_type, is_created = SourceType.objects.get_or_create(name='alipay_warrant')
        source = Source(source_type=source_type,
                        currency=info['order_total'].currency,
                        amount_allocated=info['order_total'].incl_tax,
                        amount_debited=info['order_total'].incl_tax)
        self.add_payment_source(source)
        self.add_payment_event('paid', info['order_total'].incl_tax,reference=taobao_info['trade_no'])

        #添加订单
        return self.handle_order_placement(**info)

    def get(self, request, *args, **kwargs):
        #获取淘宝交易信息,return_url
        alipay_gate=self.get_alipay()
        try:
            if alipay_gate.verify_notify(**request.GET):
                taobao_info=request.GET
                response=self.paid_order_create(request,taobao_info, *args, **kwargs)
                return response
            else:
                raise AlipayException
        except Exception as e:
            msg = six.text_type(e)
            self.restore_frozen_basket()
            return HttpResponseRedirect('/checkout/preview',kwargs={'error':msg})

    def post(self, request, *args, **kwargs):
        #获取淘宝交易信息,notify_url
        alipay_gate=self.get_alipay()
        try:
            if alipay_gate.verify_notify(**request.POST):
                taobao_info=request.GET
                self.paid_order_create(request,taobao_info, *args, **kwargs)
                return HttpResponse('success')
            else:
                raise AlipayException
        except Exception as e:
            return HttpResponse ("fail")


class CancelView(RedirectView):
    '''
    取消订单
    '''
    def get(self, request, *args, **kwargs):
        #增添购物车状态修改
        pass
    def get_redirect_url(self, **kwargs):
        #增添提示信息，取消支付
        pass