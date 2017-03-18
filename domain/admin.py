#!/usr/bin/python
# -*- coding: utf8 -*-
"""
@version: 0.1
@author: lihai
@license: Apache Licence 
@contact: 13142283701 51347294@qq.com 
@software: PyCharm Community Edition
@file: admin.py
@time: 2016/12/13 17:05
"""

from django.contrib import admin
from domain.models import *
# Register your models here.
class domainAdmin(admin.ModelAdmin):
    list_display = ["id","name","url","create_time"]

class ip_addressAdmin(admin.ModelAdmin):
    list_display = ["id","ip","address","create_time"]

class proxyAdmin(admin.ModelAdmin):
    list_display = ["id","name", "ip", "port","create_time"]

class resultAdmin(admin.ModelAdmin):
    list_display = ["id","domainName","domainUrl","ip","address","proxyName","http_code","total_time","create_time"]
    list_filter = ['domain__name']
    ordering = ('-create_time',)
admin.site.register(domain,domainAdmin)
admin.site.register(ip_address,ip_addressAdmin)
admin.site.register(result,resultAdmin)
admin.site.register(proxy,proxyAdmin)