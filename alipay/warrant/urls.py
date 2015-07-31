from django.conf.urls import *
from django.views.decorators.csrf import csrf_exempt
from . import views


urlpatterns = patterns('',
    # Views for normal flow that starts on the basket page
    url(r'^respond$', views.ResponseView.as_view(),
        name='taobao-warrant-answer'),#回调函数
    url(r'^cancel/(?P<basket_id>\d+)/$', views.CancelView.as_view(),
        name='taobao-cancel-response'),#
)
