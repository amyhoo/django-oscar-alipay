#######################################################################################
# 重写 PaymentMethodView 提供多种支付方法的选择,
# 重写 PaymentDetailsView 支付细节在具体支付方法包(例如alipay)中实现
#######################################################################################
from oscar.apps.checkout.views import PaymentMethodView,PaymentDetailsView as OscarPaymentDetailsView
from alipay.warrant.views import AlipayHandle
from django.http import HttpResponseRedirect
from .mixins import RedirectSessionMixin
from oscar.core.loading import get_class, get_classes, get_model
OrderPlacementMixin = get_class('checkout.mixins', 'OrderPlacementMixin')

class MultiPaymentMethodView(PaymentMethodView):
    template_name = 'oscar/checkout/payment_method.html'
    def get(self, request, *args, **kwargs):
        # By default we redirect straight onto the payment details view. Shops
        # that require a choice of payment method may want to override this
        # method to implement their specific logic.
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

class MultiPaymentDetailsView(RedirectSessionMixin,OscarPaymentDetailsView):
    template_name = 'oscar/checkout/payment_details.html'
    template_name_preview = 'oscar/checkout/preview.html'
    paymentsource_name={
        'alipay_warrant':"支付宝担保",
        }
    paymentsource_method={
        'alipay_warrant':AlipayHandle
    }
    def get_context_data(self, **kwargs):
        context=super(PaymentDetailsView,self).get_context_data(**kwargs)
        context['paymethod']=self.paymentsource_name[self.get_paymethod()]
        return context

    def get(self, request, *args, **kwargs):
        if kwargs.get('paymethod'):
            self.save_paymethod(kwargs.get('paymethod'))
            return HttpResponseRedirect('/checkout/preview')
        return super(PaymentDetailsView,self).get(self,request, *args, **kwargs)
    def handle_payment(self, order_number, order_total, **kwargs):
        '''
        处理支付请求
        :param order_number:
        :param total_incl_tax:
        :param kwargs:
        :return:
        '''
        self.set_order_number(order_number)
        self.set_info()
        paymethod=self.paymentsource_method[self.get_paymethod()]
        paymethod(self,order_number, **kwargs)

from oscar.apps.checkout.views import *