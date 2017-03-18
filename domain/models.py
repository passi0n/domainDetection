#!/usr/bin/python
# -*- coding: utf8 -*-
"""
@version: 0.1
@author: lihai
@license: Apache Licence
@contact: 13142283701 51347294@qq.com
@software: PyCharm Community Edition
@file: models.py
@time: 2016/12/13 17:03
"""

from django.db import models
import django.utils.timezone as timezone
from datetime import datetime
import json, time

# Create your models here.

status_choice = (("可用", "1"), ("不可用", "0"))


class domain(models.Model):
    """域名"""
    name = models.CharField(max_length=50, verbose_name="名称")
    url = models.CharField(max_length=500, verbose_name="域名链接")
    create_time = models.DateTimeField(auto_now=True, verbose_name="创建时间", editable=False)
    status = models.CharField(max_length=1, verbose_name="状态", choices=status_choice, editable=False, default="1")

    class Meta:
        verbose_name_plural = verbose_name = '域名'

    def __unicode__(self):
        return self.name


class proxy(models.Model):
    """代理"""
    name = models.CharField(max_length=20, verbose_name="名称")
    ip = models.CharField(max_length=20, verbose_name="ip地址")
    port = models.CharField(max_length=20, verbose_name="端口")
    create_time = models.DateTimeField(auto_now=True, verbose_name="创建时间", editable=False)
    status = models.CharField(max_length=1, verbose_name="状态", choices=status_choice, editable=False, default="1")

    class Meta:
        verbose_name_plural = verbose_name = '代理'

    def __unicode__(self):
        return self.name


class ip_address(models.Model):
    """ip归属地"""
    ip = models.CharField(max_length=20, verbose_name="ip地址")
    address = models.CharField(max_length=60, verbose_name="端口")
    create_time = models.DateTimeField(verbose_name="创建时间", editable=False, default=timezone.now())
    status = models.CharField(max_length=1, verbose_name="状态", choices=status_choice, editable=False, default="1")

    class Meta:
        verbose_name_plural = verbose_name = 'ip归属地'

    def __unicode__(self):
        return "%s:%s" % (self.address, self.ip)


class result(models.Model):
    """探测结果"""
    ipaddr = models.ForeignKey(to=ip_address, verbose_name="ip归属地", null=True, blank=True)
    proxy = models.ForeignKey(to=proxy, verbose_name="代理", null=True, blank=True)
    domain = models.ForeignKey(to=domain, verbose_name="域名", null=True, blank=True)
    http_code = models.CharField(max_length=5, verbose_name="http响应状态")
    total_time = models.CharField(max_length=10, verbose_name="响应时长(秒)", default="120")
    size_download = models.CharField(max_length=15, verbose_name="下载内容大小", default="0")
    speed_download = models.CharField(max_length=15, verbose_name="下载速度(字节/秒)", default="0")
    redirect_count = models.CharField(max_length=2, verbose_name="重定向次数", default="0")
    remark = models.TextField(verbose_name="备注", null=True, blank=True)
    create_time = models.DateTimeField(auto_now=True, verbose_name="创建时间", editable=False)
    status = models.CharField(max_length=1, verbose_name="状态", choices=status_choice, editable=False, default="1")

    def __unicode__(self):
        if self.domain is not None:
            return "%s:%s" % (self.domain.name, self.domain.url)
        return self.id

    class Meta:
        verbose_name_plural = verbose_name = '探测结果'

    def proxyName(self):
        if self.proxy is None:
            return "无"
        return "%s|%s:%s" % (self.proxy.name, self.proxy.ip, self.proxy.name)

    proxyName.allow_tags = True
    proxyName.short_description = "代理"

    def domainName(self):
        return self.domain.name

    domainName.allow_tags = True
    domainName.short_description = "名称"

    def domainUrl(self):
        return self.domain.url

    domainUrl.allow_tags = True
    domainUrl.short_description = "地址"

    def ip(self):
        return self.ipaddr.ip

    ip.allow_tags = True
    ip.short_description = "ip目标"

    def address(self):
        return self.ipaddr.address

    address.allow_tags = True
    address.short_description = "ip归属地"


class responseStatus(models.Model):
    """响应状态"""
    ipaddr = models.ForeignKey(to=ip_address, verbose_name="ip归属地", null=True, blank=True)
    proxy = models.ForeignKey(to=proxy, verbose_name="代理", null=True, blank=True)
    domain = models.ForeignKey(to=domain, verbose_name="域名", null=True, blank=True)
    http_code = models.CharField(max_length=5, verbose_name="http响应状态")
    total_time = models.CharField(max_length=10, verbose_name="响应时长(秒)", default="120")
    create_time = models.DateTimeField(auto_now=True, verbose_name="创建时间", editable=False)
    status = models.CharField(max_length=1, verbose_name="状态", choices=status_choice, editable=False, default="1")

    def __unicode__(self):
        if self.domain is not None:
            return "%s:%s" % (self.domain.name, self.domain.url)
        return self.id

    class Meta:
        verbose_name_plural = verbose_name = '响应状态'

    def toJSON(self):
        attrs = ["domain", "ipaddr", "http_code", "create_time"]
        params = {}
        for attr in attrs:
            if attr == "ipaddr":
                ip = self.ipaddr.ip
                params["ip"] = ip
                address = self.ipaddr.address
                params["ip_address"] = address
            elif attr == "domain":
                domain_name = self.domain.name
                params["domain_name"] = domain_name
                domain_url = self.domain.url
                params["domain_url"] = domain_url
            elif isinstance(getattr(self, attr), datetime):
                time = getattr(self, attr).strftime('%Y-%m-%d %H:%M:%S')
                params[attr] = time
            else:
                params[attr] = getattr(self, attr)
        return json.dumps(params)


class responseTime(models.Model):
    """响应时间"""
    slowest_ip = models.ForeignKey(to=ip_address, verbose_name="最慢ip", null=True, blank=True, related_name="slowest_ip")
    fastest_ip = models.ForeignKey(to=ip_address, verbose_name="最快ip", null=True, blank=True, related_name="fastest_ip")
    slowest_time = models.CharField(max_length=10, verbose_name="最慢响应时长(秒)", default="0")
    fastest_time = models.CharField(max_length=10, verbose_name="最快响应时长(秒)", default="0")
    slowest_size = models.CharField(max_length=15, verbose_name="最慢下载大小(字节)", default="0")
    fastest_size = models.CharField(max_length=15, verbose_name="最快下载大小(字节)", default="0")
    slowest_speed = models.CharField(max_length=15, verbose_name="最慢速度(字节/秒)", default="0")
    fastest_speed = models.CharField(max_length=15, verbose_name="最快速度(字节/秒)", default="0")
    slowest_redirect = models.CharField(max_length=15, verbose_name="最慢跳转次数", default="0")
    fastest_redirect = models.CharField(max_length=15, verbose_name="最快跳转次数", default="0")
    domain = models.ForeignKey(to=domain, verbose_name="域名", null=True, blank=True)
    create_time = models.DateTimeField(auto_now=True, verbose_name="创建时间", editable=False)
    status = models.CharField(max_length=1, verbose_name="状态", choices=status_choice, editable=False, default="1")

    def __unicode__(self):
        if self.domain is not None:
            return "%s:%s" % (self.domain.name, self.domain.url)
        return self.id

    class Meta:
        verbose_name_plural = verbose_name = '响应时间'

    def toJSON(self):
        attrs = ["slowest_ip", "fastest_ip", "slowest_time", "fastest_time", "slowest_size", "fastest_size"
            , "slowest_speed", "fastest_speed", "slowest_redirect", "fastest_redirect", "domain", "create_time"]
        params = {}
        for attr in attrs:
            if attr == "slowest_ip":
                ip = self.slowest_ip.ip
                params["slowest_ip"] = ip
                address = self.slowest_ip.address
                params["slowest_ip_address"] = address
            elif attr == "fastest_ip":
                ip = self.fastest_ip.ip
                params["fastest_ip"] = ip
                address = self.fastest_ip.address
                params["fastest_ip_address"] = address
            elif attr == "domain":
                domain_name = self.domain.name
                params["domain_name"] = domain_name
                domain_url = self.domain.url
                params["domain_url"] = domain_url
            elif isinstance(getattr(self, attr), datetime):
                time = getattr(self, attr).strftime('%Y-%m-%d %H:%M:%S')
                params[attr] = time
            else:
                params[attr] = getattr(self, attr)
        return json.dumps(params)
