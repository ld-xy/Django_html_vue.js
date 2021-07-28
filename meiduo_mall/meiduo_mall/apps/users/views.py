from django.shortcuts import render
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView, CreateAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import UpdateModelMixin
from django_redis import get_redis_connection
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.views import ObtainJSONWebToken
from datetime import datetime

from .serializers import CreateUserSerializer, UserDetailSerializer, EmailSerializer, UserAddressSerializer, \
    AddressTitleSerializer, UserBrowserHistorySerializer, SKUSerializer
from .models import User, Address
from goods.models import SKU
from carts.utils import merge_cart_cookie_to_redis


# Create your views here.


class UserView(CreateAPIView):
    """用户注册"""
    # 指定序列化器
    serializer_class = CreateUserSerializer


class UsernameCountView(APIView):
    """判断用户是否已注册"""

    def get(self, request, username):
        # 查询user表 filter查询username的数量
        count = User.objects.filter(username=username).count()

        # 包装响应数据
        data = {
            'username': username,
            'count': count
        }
        # 响应
        return Response(data)


class MobileCountView(APIView):
    """判断手机号是否已注册"""

    def get(self, request, mobile):
        # 查询数据库
        count = User.objects.filter(mobile=mobile).count()
        # 构造响应数据
        data = {
            'mobile': mobile,
            'count': count
        }
        # 响应
        return Response(data)


# GET /user/
class UserDetailView(RetrieveAPIView):
    """用户详细信息展示"""
    serializer_class = UserDetailSerializer
    # queryset = User.objects.all()
    permission_classes = [IsAuthenticated]  # 指定权限,只有通过认证的用户才能访问当前视图

    def get_object(self):
        """重写此方法返回 要展示的用户模型对象"""
        return self.request.user


# PUT /email/
class EmailView(UpdateAPIView):
    """更新用户邮箱"""
    """首先要登陆权限，如果未登陆则不可用"""
    permission_classes = [IsAuthenticated]
    """实例化对象"""
    serializer_class = EmailSerializer

    def get_object(self):
        return self.request.user


class EmailVerifyView(APIView):
    """激活用户邮箱"""

    def get(self, request):
        # 获取前端查询字符串中传入的token
        token = request.query_params.get('token')
        if not token:
            return Response({'message': '缺少token'}, status=status.HTTP_400_BAD_REQUEST)

        # 把token解密 并查询对应的user
        user = User.check_verify_email_token(token)
        # 修改当前user的email_active为True
        if user is None:
            return Response({'message': '激活失败'}, status=status.HTTP_400_BAD_REQUEST)
        user.email_active = True
        user.save()
        # 响应
        return Response({'message': 'ok'})


class AddressViewSet(UpdateModelMixin, GenericViewSet):
    """用户收货地址增删改查"""
    """首先设置权限，只有登陆用户，才能进行操作"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserAddressSerializer

    # queryset = ''
    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted=False)
        # return Address.objects.filter(is_deleted=False)

    def create(self, request):
        user = request.user
        # count = user.addresses.all().count()
        count = Address.objects.filter(user=user).count()
        # 用户收货地址数量有上限  最多只能有20
        if count >= 20:
            return Response({'message': '收货地址数量上限'}, status=status.HTTP_400_BAD_REQUEST)

        # 创建序列化器进行反序列化
        serializer = self.get_serializer(data=request.data)
        # 调用序列化器的is_valid()
        serializer.is_valid(raise_exception=True)
        # 调用序列化器的save()
        serializer.save()
        # 响应
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # GET /addresses/
    def list(self, request, *args, **kwargs):
        """
        用户地址列表数据
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        user = self.request.user
        return Response({
            'user_id': user.id,
            'default_address_id': user.default_address_id,
            'limit': 20,
            'addresses': serializer.data,
        })

    def destroy(self, request, *args, **kwargs):
        """
        处理删除
        """
        address = self.get_object()

        # 进行逻辑删除
        address.is_deleted = True
        address.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

        # put /addresses/pk/title/
        # 需要请求体参数 title

    @action(methods=['put'], detail=True)
    def title(self, request, pk=None):
        """
        修改标题
        """
        address = self.get_object()
        serializer = AddressTitleSerializer(instance=address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    # put /addresses/pk/status/
    @action(methods=['put'], detail=True)
    def status(self, request, pk=None):
        """
        设置默认地址
        """
        address = self.get_object()
        request.user.default_address = address
        request.user.save()
        return Response({'message': 'OK'}, status=status.HTTP_200_OK)


class UserBrowserHistoryView(CreateAPIView):
    """用户商品浏览记录"""
    # 指定序列化器
    serializer_class = UserBrowserHistorySerializer
    permission_classes = [IsAuthenticated]  # 指定权限

    def get(self, request):
        """查询商品浏览记录"""

        # 创建redis连接对象
        redis_conn = get_redis_connection('history')
        # 获取当前请求的用户
        user = request.user

        # 获取redis中当前用户的浏览记录列表数据
        sku_ids = redis_conn.lrange('history_%d' % user.id, 0, -1)

        # 把sku_id对应的sku模型查询 出来
        # SKU.objects.filter(id__in=sku_ids)  # 用此方式获取sku模型顺序就乱了
        sku_list = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            sku_list.append(sku)
        # 创建序列化器进行序列化器
        serializer = SKUSerializer(sku_list, many=True)

        # 响应
        return Response(serializer.data)


jwt_response_payload_handler = api_settings.JWT_RESPONSE_PAYLOAD_HANDLER


class UserAuthorizeView(ObtainJSONWebToken):
    """自定义账号密码登录视图,实现购物车登录合并"""

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            user = serializer.object.get('user') or request.user
            token = serializer.object.get('token')
            response_data = jwt_response_payload_handler(token, user, request)
            response = Response(response_data)
            if api_settings.JWT_AUTH_COOKIE:
                expiration = (datetime.utcnow() +
                              api_settings.JWT_EXPIRATION_DELTA)
                response.set_cookie(api_settings.JWT_AUTH_COOKIE,
                                    token,
                                    expires=expiration,
                                    httponly=True)
            # 账号登录时合并购物车
            merge_cart_cookie_to_redis(request, user, response)

            return response

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
