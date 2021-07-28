from django.contrib import admin

from . import models
from celery_tasks.html.tasks import generate_static_list_search_html, generate_static_sku_detail_html


class GoodsCategoryAdmin(admin.ModelAdmin):
    """商品类别模型站点管理类"""
    def save_model(self, request, obj, form, change):
        """
        当点击admin中的保存按钮时会来调用此方法
        :param request: 保存时本次请求对象
        :param obj: 本次要保存的模型对象
        :param form: admin中表单
        :param change:  是否改为
        """

        obj.save()
        # 重新生成新的列表静态界面
        generate_static_list_search_html.delay()


    def delete_model(self, request, obj):
        """当点击admin中删除按钮时会来调用此方法"""
        obj.delete()
        # 重新生成新的列表静态界面
        generate_static_list_search_html.delay()


# @admin.register(models.SKU)
class SKUAdmin(admin.ModelAdmin):
    """商品模型站点管理类"""

    def save_model(self, request, obj, form, change):

        obj.save()  # 千万不要少了这一行,不然admin的保存就无效

        generate_static_sku_detail_html.delay(obj.id)


class SKUImageAdmin(admin.ModelAdmin):
    """商品图片模型站点管理类"""

    def save_model(self, request, obj, form, change):
        """

        :param request:
        :param obj: 图片模型对象
        :param form:
        :param change:
        :return:
        """
        obj.save()  # 千万不要少了这一行,不然admin的保存就无效

        sku = obj.sku  # 通过外键获取图片模型对象所关联的sku模型的id
        # 如果当前sku商品还没有默认图片,就给它设置一张默认图片
        if not sku.default_image_url:
            sku.default_image_url = obj.image.url

            generate_static_sku_detail_html.delay(sku.id)

    def delete_model(self, request, obj):
        obj.delete()
        sku = obj.sku  # 获取到图片模型对象关联的sku模型
        generate_static_sku_detail_html.delay(sku.id)




# Register your models here.
admin.site.register(models.GoodsCategory, GoodsCategoryAdmin)
admin.site.register(models.GoodsChannel)
admin.site.register(models.Goods)
admin.site.register(models.Brand)
admin.site.register(models.GoodsSpecification)
admin.site.register(models.SpecificationOption)
admin.site.register(models.SKU, SKUAdmin)
admin.site.register(models.SKUSpecification)
admin.site.register(models.SKUImage, SKUImageAdmin)