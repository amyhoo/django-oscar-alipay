#######################################################################################
# 添加重定向的session组件，
# 该组件可以在view中使用，提供通用重定向支付方法中所需的session操作
# 该组件也可以单独被实例化，但需要提供checkout_session对象。
#######################################################################################
from .exceptions import NotInViewException
class RedirectSessionMixin(object):
    def __init__(self,checkout_session=None,**kwargs):
        if checkout_session:
            self.checkout_session=checkout_session
        super(RedirectSessionMixin,self).__init__(**kwargs)
    def save_paymethod(self,paymethod):
        self.checkout_session._set('payment','source',paymethod)
    def get_paymethod(self):
        return self.checkout_session._get('payment','source')
    def set_order_number(self,order_number):
        self.checkout_session._set('order','number',order_number)
    def get_order_number(self):
        return self.checkout_session._get('order','number')
    def set_info(self):
        '''
        在PaymentDetailView中被调用，保存回调中所需要的订单信息
        :return:
        '''
        try:
            submission=super(RedirectSessionMixin,self).build_submission()
            product_list= [item.product.title for item in self.request.basket.all_lines()]
            submission['order_kwargs']['subject']=','.join(product_list)
            submission.pop('basket')
            submission.pop('user')
            self.checkout_session._set('order','submission',submission)
        except :
            raise NotInViewException('current object assumed used in a view and with CheckoutSessionMixin')
    def get_info(self):
        return self.checkout_session._get('order','submission')
