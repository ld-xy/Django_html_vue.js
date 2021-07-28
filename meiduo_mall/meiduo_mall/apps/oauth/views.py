from django.shortcuts import render
from rest_framework.views import APIView
from QQLoginTool.QQtool import OAuthQQ
from rest_framework.response import Response
from django.conf import settings
from rest_framework import status
from rest_framework_jwt.settings import api_settings

from .models import OAuthQQUser
from .utils import generate_save_user_token
from .serializers import QQAuthUserSerializer
import logging
from carts.utils import merge_cart_cookie_to_redis

logger = logging.getLogger('django')


# Create your views here.
class QQOauthURLView(APIView):
    """拼接好QQ登录网址"""

    def get(self, request):
        # 1.提取前端传入的next参数记录用户从那里去到login界面
        # next = request.query_params.get('next') or '/'
        # get(self, key, default=None):  获取指定key的值,如果获取的key不存在 可以返回default参数的值
        next = request.query_params.get('next', '/')
        # # QQ登录参数
        # QQ_CLIENT_ID = '101514053'
        # QQ_CLIENT_SECRET = '1075e75648566262ea35afa688073012'
        # QQ_REDIRECT_URI = 'http://www.meiduo.site:8080/oauth_callback.html'

        # 2.利用QQ登录SDK
        # oauth = OAuthQQ(client_id=appid, client_secret=appkey, redirect_uri=回调域名, state=记录来源)
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=next)
        #  创建QQ登录工具对象
        login_url = oauth.get_qq_url()
        #  调用它里面的方法 拼接好QQ登录网址
        return Response({'login_url': login_url})


class QQAuthUserView(APIView):
    """QQ登录成功后的回调处理"""

    def get(self, request):
        # 1.获取前端传入的code
        code = request.query_params.get('code')
        if not code:  # 如果没有获取到code
            return Response({'message': '缺少code'}, status=status.HTTP_400_BAD_REQUEST)

        # 2.创建QQ登录工具对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)
        try:
            # 3.调用它里面get_access_token(code) 用code向qq服务器获取access_token
            access_token = oauth.get_access_token(code)
            # 4. 调用它里面的get_open_id(access_token)  用access_token响应QQ服务器获取openid
            openid = oauth.get_open_id(access_token)
        except Exception as e:
            logger.info(e)
            return Response({'message': 'QQ服务器不可用'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


        try:
            # 5.查询数据库有没有这个openid
            authQQUserModel = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 6.如果openid 没有绑定用户,把openid 加密之后响应给前端 ,让前端先暂存一会 等待绑定时使用
            access_token_openid = generate_save_user_token(openid)
            return Response({'access_token': access_token_openid})

        else:
            # 7.如果openid已绑定美多用户 那么直接代表登录成功,给前端 返回JWT 状态保存信息
            user = authQQUserModel.user  # 获取到openid 关联的user
            jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER  # 引用jwt中的叫jwt_payload_handler函数(生成payload)
            jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER  # 函数引用 生成jwt
            payload = jwt_payload_handler(user)  # 根据user生成用户相关的载荷
            token = jwt_encode_handler(payload)  # 传入载荷生成完整的jwt

            # 创建响应对象
            response = Response({
                'token': token,
                'username': user.username,
                'user_id': user.id
            })
            # 在此调用合并购物车函数
            merge_cart_cookie_to_redis(request, user, response)


            return response

    def post(self, request):
        """openid绑定用户接口"""
        # 创建序列化器进行反序列化  使用自己定义的类
        serializer = QQAuthUserSerializer(data=request.data)
        # 调用is_valid方法进行校验  调用在自定义的序列化类中的vaild方法
        serializer.is_valid(raise_exception=True)
        # 调用序列化器的save方法  调用create()方法
        user = serializer.save()
        # 生成JWT 状态保存 token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER  # 引用jwt中的叫jwt_payload_handler函数(生成payload)
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER  # 函数引用 生成jwt

        payload = jwt_payload_handler(user)  # 根据user生成用户相关的载荷
        token = jwt_encode_handler(payload)  # 传入载荷生成完整的jwt

        response = Response({
            'token': token,
            'username': user.username,
            'user_id': user.id
        })
        # 在此调用合并购物车函数
        merge_cart_cookie_to_redis(request, user, response)

        # 响应
        return response


