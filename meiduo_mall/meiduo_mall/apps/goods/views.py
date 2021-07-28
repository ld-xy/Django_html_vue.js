from django.shortcuts import render
from drf_haystack.viewsets import HaystackViewSet
from rest_framework.generics import ListAPIView

from .models import SKU
from .serializers import SKUSerializer, SKUSearchSerializer
from rest_framework.filters import OrderingFilter


# Create your views here.
class SKUListView(ListAPIView):
    """商品列表数据查询"""

    filter_backends = [OrderingFilter]  # 指定过滤后端为排序过滤
    ordering_fields = ['create_time', 'price', 'sales']  # 指定排序字段 (查询所有数据接口 中查的是那个模型中的数据,里面就指定那个模型的字段)


    serializer_class = SKUSerializer
    # queryset = SKU.objects.filter()

    def get_queryset(self):
        """如果当前在视图中没有去定义get /post方法 那么就没法定义一个参数用来接收正则组提取出来的url路径参数, 可以利用视图对象的 args或kwargs属性去获取啊"""
        category_id = self.kwargs.get('category_id')
        return SKU.objects.filter(is_launched=True, category_id=category_id)


class SKUSearchViewSet(HaystackViewSet):
    """
    SKU搜索
    """
    index_models = [SKU]  # 指定查询集

    serializer_class = SKUSearchSerializer  # 指定序列化器