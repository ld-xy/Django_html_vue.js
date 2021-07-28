from django.shortcuts import render
from rest_framework.views import APIView
from django_redis import get_redis_connection
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView

from goods.models import SKU
from .serializers import OrderSettlementSerializer, CommitOrderSerializer


# Create your views here.

class OrderSettlementView(APIView):
    """去结算"""

    permission_classes = [IsAuthenticated]  # 指定权限,必须是登录用户才能访问此视图中的接口

    def get(self, request):

        # 创建redis连接对象
        redis_conn = get_redis_connection('cart')
        # 获取user对象
        user = request.user

        # 获取redis中hash和set两个数据
        cart_dict_redis = redis_conn.hgetall('cart_%d' % user.id)
        selected_ids = redis_conn.smembers('selected_%d' % user.id)

        # 定义一个字典用来保存勾选的商品及count
        cart_dict = {}  # {1: 2, 16: 1}
        # 把hash中那些勾选商品的sku_id和count取出来包装到一个新字典中
        for sku_id_bytes in selected_ids:
            cart_dict[int(sku_id_bytes)] = int(cart_dict_redis[sku_id_bytes])

        # 把勾选商品的sku模型再获取出来
        skus = SKU.objects.filter(id__in=cart_dict.keys())

        # 遍历skus 查询集取出一个一个的sku模型
        for sku in skus:
            # 给每个sku模型多定义一个count属性
            sku.count = cart_dict[sku.id]

        # 定义一运费
        freight = Decimal('10.00')

        data_dict = {'freight': freight, 'skus': skus}  #  序列化时,可以对 单个模型/查询集/列表/字典 都可以进行序列化器()
        # 创建序列化器进行序列化
        serializer = OrderSettlementSerializer(data_dict)

        return Response(serializer.data)


class CommitOrderView(CreateAPIView):
    """保存订单"""

    serializer_class = CommitOrderSerializer

    # 指定权限
    permission_classes = [IsAuthenticated]
