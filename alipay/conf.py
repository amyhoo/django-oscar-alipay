# -*- coding:utf-8 -*-
#######################################################################################
#淘宝接口参数意义
#######################################################################################
from django.conf import settings

# 合作者身份 ID，以 2088 开头的 16 位纯数字组成
ALIPAY_PARTNER = ''

# 支付宝网关
ALIPAY_GATEWAY = 'https://mapi.alipay.com/gateway.do'
ALIPAY_WAP_GATEWAY = 'http://wappaygw.alipay.com/service/rest.htm'
#通知网关
NOTIFY_GATEWAY_URL = 'https://mapi.alipay.com/gateway.do?service=notify_verify&partner=%s&notify_id=%s'

# COD Cash On Delivery 货到付款

#卖家信息
ALIPAY_SELL_EMAIL=None
ALIPAY_SELL_ID=''

#字符集
ALIPAY_INPUT_CHARSET = 'utf-8'
ALIPAY_SIGN_TYPE = 'MD5'

# 访问模式,根据自己的服务器是否支持ssl访问，若支持请选择https；若不支持请选择http
ALIPAY_TRANSPORT='https'

# 安全检验码，以数字和字母组成的32位字符
ALIPAY_KEY = ''

# 付完款后跳转的页面（同步通知） 要用 http://格式的完整路径，不允许加?id=123这类自定义参数
ALIPAY_RETURN_URL=''

# 交易过程中服务器异步通知的页面 要用 http://格式的完整路径，不允许加?id=123这类自定义参数
ALIPAY_NOTIFY_URL=''
ALIPAY_SHOW_URL=''

ALIPAY_DATE_FORMAT = ('%Y-%m-%d %H:%M:%S',)

#支付宝接口定义
SERVICE = (
        'create_direct_pay_by_user',    # 即时到帐
        'create_partner_trade_by_buyer',    # 担保交易
        'send_goods_confirm_by_platform',   # 确认发货
        'trade_create_by_buyer',            # 标准双接口
        'alipay.mobile.qrcode.manage', #二维码管理
        )

PAYMENT_TYPE = (
    ('商品购买','1'),    #商品购买
    ('服务购买','2'),    #服务购买
    ('网络拍卖','3'),    #网络拍卖
    ('捐赠','4'),    #捐赠
    ('邮费补偿','5'),    #邮费补偿
    ('奖金','6'),    #奖金
    ('基金购买','7'),       #基金购买
    ('机票购买','8'),    #机票购买
        )
PAYMETHOD = (
        'creditPay',    # 'credit payment'    # 需开通信用支付
        'directPay',    # 'direct payment'    # 余额支付，不能设置 defaultbank 参数
        'bankPay',      # 'bank payment directly'   # 需开通纯网关，需设置 defaultbank
        'cash',         # 'paid by cash'
        'cartoon',      # 'paid by bank card thourgh alipay gateway'
        )

LOGISTICS_TYPE = (
        'POST',     # 平邮
        'EXPRESS',  # 其他快递
        'EMS',      # EMS
        )
LOGISTICS_PAYMENT = (
        'BUYER_PAY',    # 物流买家承担运费
        'SELLER_PAY',   # 物流卖家承担运费
        'BUYER_PAY_AFTER_RECEIVE',  # 买家到货付款，运费显示但不计入总价
        )

#交易状态
TRADE_STATUS = (
        'WAIT_BUYER_PAY',           #等待买家付款
        'WAIT_SELLER_SEND_GOODS',   #买家已付款，等待卖家发货
        'WAIT_BUYER_CONFIRM_GOODS', #卖家已发货，等待买家收货
        'TRADE_FINISHED',           #买家已收货，交易完成
        'TRADE_CLOSED',             #交易中途关闭（已结束，未成功完成）
        'COD_WAIT_SELLER_SEND_GOODS',   # 等待卖家发货（货到付款）
        'COD_WAIT_BUYER_PAY',           # 等待买家签收付款（货到付款）
        'COD_WAIT_SYS_PAY_SELLER',      # 签收成功等待系统打款给卖家（货到付款）
        )

#基本参数,所有标记为None值在业务逻辑执行时赋值,或者被删除
BASIC_PARAMS={
        #基本参数
        '_input_charset': ALIPAY_INPUT_CHARSET,
        'partner': ALIPAY_PARTNER,
        'payment_type': dict(PAYMENT_TYPE)['商品购买'],
        'sign_type':ALIPAY_SIGN_TYPE, #加密方式
        'sign':None,

        #卖家参数，seller_id,seller_account_name,seller_email必须且只需要一个
        'seller_id':ALIPAY_SELL_ID,
        'seller_account_name':None,
        'seller_email':ALIPAY_SELL_EMAIL,
        #请求所需参数
        'key':ALIPAY_KEY,
}

#业务信息
BIZ_PARAMS={
        #接口类型
        'service':None,

        # 通知信息
        'notify_url':None,
        'return_url':None,
        'show_url':None,#商户网站网址

        #订单
        'out_trade_no':None,# 请与贵网站订单系统中的唯一订单号匹配
        'subject':None,# 订单名称，显示在支付宝收银台里的“商品名称”里，显示在支付宝的交易管理的“商品名称”的列表里。
        'body':None,# 订单描述、订单详细、订单备注，显示在支付宝收银台里的“商品描述”里
        'total_fee':None,# 订单总金额，显示在支付宝收银台里的“应付总额”里
        'quantity':None,# 数量
        'price':None,# 价格
        'discount':None,# 折扣

        #物流
        'logistics_type':'EXPRESS',#其他快递
        'logistics_payment':'BUYER_PAY',#买家承担
        'logistics_fee':None,

}
EXTEND_PARAMS={

    # 扩展功能参数——防钓鱼
    'anti_phishing_key':None,
    'exter_invoke_ip': None,
    # 扩展功能参数——自定义参数
    'buyer_email':None,
    'extra_common_param':None,
    # 扩展功能参数——分润
    'royalty_type':None,
    'royalty_parameters':None,
}

#即时到帐参数
INSTANT_PARAMS={
    #即时到帐特有参数
    'paymethod' : 'directPay',   # 默认支付方式，四个值可选：bankPay(网银); cartoon(卡通); directPay(余额); CASH(网点支付)
    'defaultbank' : None,          # 默认网银代号，代号列表见http://club.alipay.com/read.php?tid=8681379
}

#确认发货接口参数
LOG_PARAMS={
    #基本参数
    'service':'send_goods_confirm_by_platform',
    'partner':ALIPAY_PARTNER,
    'input_charset':ALIPAY_INPUT_CHARSET,
    'sign':None,
    'sign_type':ALIPAY_SIGN_TYPE,

    #业务参数
    'trade_no':None,
    'logistics_name':None,
    'transport_type':None,

}