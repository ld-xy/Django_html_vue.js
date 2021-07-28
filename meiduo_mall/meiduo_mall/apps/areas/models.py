from django.db import models


class Area(models.Model):
    """
    省区划 自关联的表 ,外键指向本身
    """
    name = models.CharField(max_length=20, verbose_name='名称')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, related_name='subs', null=True, blank=True,
                               verbose_name='上级行政区划')
    # 石家庄市.parent   河北省
    # 河北省.subs       河北省下面的所有市
    class Meta:
        db_table = 'tb_areas'
        verbose_name = '行政区划'
        verbose_name_plural = '行政区划'

    def __str__(self):
        return self.name
