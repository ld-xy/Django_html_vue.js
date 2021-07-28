from django.shortcuts import render
from rest_framework.views import APIView
from random import randint
from django_redis import get_redis_connection
from rest_framework.response import Response
import logging
from rest_framework import status

from meiduo_mall.libs.yuntongxun.sms import CCP
from . import constants
from celery_tasks.sms.tasks import send_sms_code

logger = logging.getLogger('django')


# Create your views here.
class SMSCodeView(APIView):
    """短信验证码"""

    def get(self, request, mobile):
        # 1. 创建redis连接对象
        redis_conn = get_redis_connection('verify_codes')
        # 2.先从redis获取发送标记
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        # pl.get('send_flag_%s' % mobile)
        # send_flag = pl.execute()[0]  # 元组


        # 3.如果取到了标记,说明此手机号频繁发短信
        if send_flag:
            return Response({'message': '手机频繁发送短信'}, status=status.HTTP_400_BAD_REQUEST)

        # 4.生成验证码
        sms_code = '%06d' % randint(0, 999999)
        logger.info(sms_code)

        #  创建redis管道:(把多次redis操作装入管道中,将来一次性去执行,减少redis连接操作)
        pl = redis_conn.pipeline()
        # 5. 把验证码存储到redis数据库
        # redis_conn.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex('sms_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # 6. 存储一个标记,表示此手机号已发送过短信 标记有效期60s
        # redis_conn.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        pl.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)

        # 执行管道
        pl.execute()
        # import time
        # time.sleep(5)
        # 7. 利用容联云通讯发送短信验证码
        # CCP().send_template_sms(self, 手机号, [验证码, 5], 1):
        # CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60], 1)
        # 触发异步任务,将异步任务添加到celery任务队列
        # send_sms_code(mobile, sms_code)  # 调用普通函数而已
        send_sms_code.delay(mobile, sms_code)  # 触发异步任务

        # 8. 响应
        return Response({'message': 'ok'})
