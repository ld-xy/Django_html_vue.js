from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveAPIView
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework_extensions.cache.mixins import CacheResponseMixin

from .models import Area
from .serializers import AreaSerializer, SubsSerializer

# Create your views here.
# class AreaListView(APIView):
#     """查询所有省"""
#
#     def get(self, request):
#         # 1.获取指定的查询集
#         qs = Area.objects.filter(parent=None)
#         # qs = Area.objects.all()
#         # 2.创建序列化器进行序列化
#         serializer = AreaSerializer(qs, many=True)
#         # 3.响应
#         return Response(serializer.data)
#
#
# class AreaDetailView(APIView):
#     """查询单一省或市"""
#
#     def get(self, request, pk):
#         # 1. 根据pk查询出指定的省或市
#         try:
#             area = Area.objects.get(id=pk)
#         except Area.DoesNotExist:
#             return Response({'message': '无效pk'}, status=status.HTTP_400_BAD_REQUEST)
#         # 2. 创建序列化器进行序列化
#         serializer = SubsSerializer(area)
#         # 3. 响应
#         return Response(serializer.data)





# class AreaListView(ListModelMixin, GenericAPIView):
# class AreaListView(ListAPIView):
#     """查询所有省"""
#     # 指定序列化器
#     serializer_class = AreaSerializer
#     # 指定查询集
#     queryset = Area.objects.filter(parent=None)

#     def get(self, request):
#         # # 1.获取指定的查询集
#
#
# #         # # qs = Area.objects.filter(parent=None)
# #         # qs = self.get_queryset()
# #         # # qs = Area.objects.all()
# #         # # 2.创建序列化器进行序列化
# #         # # serializer = AreaSerializer(qs, many=True)
# #         # serializer = self.get_serializer(qs, many=True)
# #         # # 3.响应
# #         # return Response(serializer.data)
#         return self.list(request)


# class AreaDetailView(RetrieveAPIView):
#     """查询单一省或市"""
#     # 指定序列化器
#     serializer_class = SubsSerializer
#     # 指定查询集
#     queryset = Area.objects.all()
#     #
    # def get(self, request, pk):
    #     # 1. 根据pk查询出指定的省或市
    #     try:
    #         area = Area.objects.get(id=pk)
    #     except Area.DoesNotExist:
    #         return Response({'message': '无效pk'}, status=status.HTTP_400_BAD_REQUEST)
    #     # 2. 创建序列化器进行序列化
    #     serializer = SubsSerializer(area)
    #     # 3. 响应
    #     return Response(serializer.data)


class AreaViewSet(CacheResponseMixin, ReadOnlyModelViewSet):

    # queryset = Area.objects.all()

    pagination_class = None  # 禁用分页
    # 指定查询集
    def get_queryset(self):
        if self.action == 'list':
            return Area.objects.filter(parent=None)
        else:
            return Area.objects.all()

    # 指定序列化器
    # serializer_class =

    def get_serializer_class(self):
        if self.action == 'list':
            return AreaSerializer
        else:
            return SubsSerializer