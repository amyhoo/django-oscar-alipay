介绍
============
由于工作需要实现商城的支付部分，而django-oscar在支付部分给了框架，具体需要自己实现，看网上也没有现成的支付部分，所以花些时间实现了该接口

django-oscar-alipay 是django-oscar商城系统的支持多种支付方式的支付集成
实现了alipay担保交易，即时到帐和自动发货等接口。
详细实现了django-oscar的payment支付部分。

安装使用
---------
* 下载解压到本地目录下
* 修改settings 文件，在install_apps 添加'alipay',并
  将get_core_apps()部分修改为 get_core_apps(['apps.checkout'])替代原有的django-oscar的checkout模块
  由于django默认的SESSION_SERIALIZER为json方式，不能处理复杂对象，添加下面语句
  SESSION_SERIALIZER='django.contrib.sessions.serializers.PickleSerializer'

组成
----------
* alipay/: 包含了支付宝的即时到帐，担保交易和确认发货的接口
* apps/checkout：替代原有的django-oscar的checkout模块，实现对支付接口的选则以及支付流程。
* templates:修改了原有的django-oscar的checkout模块的模块的模板。
* media: 增添了支付宝的图标

接口描述 (alipay/alipay.py)
---------
支付宝接口《alipay》使用方法：
1.gatewayinfo实现了一个支付宝接口类 Alipay
2.传递基本参数，创建alipay对象：Alipay(**kwargs)，kwargs为支付宝所有接口都需要的基本参数
3.warrant/views中实现了请求与回调界面，
  支付宝请求:AlipayHandle,被PaymentDetailView所调用，生成一个请求，传递运行时的支付宝接口参数
  回调界面:ResponseView,实现return_url,notify_url所调用的回调界面。在其中实现支付验证以及支付
  完毕后订单的生成。

支付模块《apps/checkout》的使用方法
1.MultiPaymentMethodView中可以设置多种支付方法，在templates\oscar\checkout\payment_method.html
中添加支付方法。
2.MultiPaymentDetailsView，接收支付流程上环节MultiPaymentMethodView所输入的支付方法，在该界面
添加支付方法名称与具体实现函数之间的对应关系，根据该关系调用具体的支付接口中的函数完成支付请求，
以及生成订单。

