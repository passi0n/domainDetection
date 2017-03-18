#!/usr/bin/python
# -*- coding: utf8 -*-
"""
@version: 0.1
@author: lihai
@license: Apache Licence
@contact: 13142283701 51347294@qq.com
@software: PyCharm Community Edition
@file: views.py
@time: 2016/12/13 17:04
"""

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.gzip import gzip_page

from domain.models import domain as Domain, result as Result, responseTime as ResponseTime, \
    responseStatus as ResponseStatus
from datetime import datetime, timedelta
import json
from django.core.cache import cache
from monitor import settings
from django.db.models import Q


def index(request):
    # 首页
    try:
        params = {}
        return render_to_response('index.html', params, RequestContext(request))
    except Exception as e:
        print(e.args)
        raise Http404("")


@gzip_page
def getTopData(request, index=0, size=10):
    # 排行榜数据
    result = {}
    try:
        # 获取缓存数据
        cache_key = "domain_top_%s_%s" % (index, size)
        cache_data = cache.get(cache_key, None)
        if cache_data:
            result = cache_data
        else:
            size = int(size)
            max_count = Domain.objects.count()
            max_page = max_count // size

            index = max(int(index), 0)
            index = min(max_page, index)

            begin = index * size
            end = min((index + 1) * size, max_count)

            domains = Domain.objects.all()[begin:end]

            data = []
            # time_out = -1

            old_time = datetime.now()

            for domain in domains:
                item = topDomainData(domain)
                data.append(item)

            time_offset = datetime.now() - old_time
            print(time_offset.microseconds)
            print(time_offset.seconds)
            # print("run_time:" + str(time_offset.seconds))

            result = {"isOK": "1",
                      "time": time_offset.seconds,
                      "max_count": max_count,
                      "index": index,
                      "max_page": max_page,
                      "min_page": 0,
                      "data": data}
            cache.set(cache_key, result, settings.cache_time)
    except Exception as e:
        print(e.args)
        result = {"isOK": "0",
                  "info": str(e.args)}
    finally:
        try:
            str_result = json.dumps(result)
        except Exception as e:
            print(e.args)
        response = HttpResponse(status=200)
        response.write(str_result)
        return response


@gzip_page
def searchTopData(request, keywords):
    result = {}
    try:
        domains = Domain.objects.filter(Q(name__contains='%s' % keywords) | Q(url__contains='%s' % keywords)).all()

        data = []

        old_time = datetime.now()

        for domain in domains:
            item = topDomainData(domain)
            data.append(item)

        time_offset = datetime.now() - old_time
        print(time_offset.microseconds)
        print(time_offset.seconds)
        # print("run_time:" + str(time_offset.seconds))

        result = {"isOK": "1",
                  "time": time_offset.seconds,
                  "data": data}
    except Exception as e:
        print(e.args)
        result = {"isOK": "0",
                  "info": str(e.args)}
    finally:
        try:
            str_result = json.dumps(result)
        except Exception as e:
            print(e.args)
        response = HttpResponse(status=200)
        response.write(str_result)
        return response


def topDomainData(domain):
    # 单个域名排行数据
    id_domain = domain.id
    url_domain = domain.url
    name_domain = domain.name
    print("%3s %10s %50s" % (id_domain, name_domain, url_domain))

    time_start = datetime.now()
    # 最近1天平均时间
    today_lately = time_start - timedelta(days=1)
    # 最近1小时平均时间
    offset_hour = timedelta(hours=1)

    today_count = 0
    count_timeout_day = 0
    today_totalTime = 0

    hour_count = 0
    count_timeout_hour = 0
    hour_totalTime = 0

    count_httpCodeError_hour = 0
    count_httpCodeError_day = 0

    results_day = Result.objects.filter(domain=domain, create_time__gte=today_lately).order_by(
        "-create_time").values("total_time", "create_time", "http_code").all()

    time_start = datetime.now()

    for item in results_day:
        item_totalTime = item["total_time"]
        item_createTime = item["create_time"]
        item_httpCode = item["http_code"]
        if item_totalTime > 0:
            # 未超时
            if time_start - item_createTime <= offset_hour:
                # 一小时内
                hour_count += 1
                hour_totalTime += item_totalTime
                if int(item_httpCode) > 400:
                    # 状态异常
                    count_httpCodeError_hour += 1
                    count_httpCodeError_day += 1
            today_count += 1
            today_totalTime += item_totalTime
            if int(item_httpCode) > 400:
                # 状态异常
                count_httpCodeError_day += 1
        else:
            # 超时
            if time_start - item_createTime <= offset_hour:
                # 一小时内
                count_timeout_hour += 1
            count_timeout_day += 1

    try:
        lately = results_day[0]
        result_lately = lately["total_time"]
        if result_lately == -1:
            result_lately = "超时"
    except:
        result_lately = "异常"

    # 小时平均
    if hour_count > 0:
        aver_hour = "%.3f" % (hour_totalTime / hour_count)
    else:
        aver_hour = 0

    # 天平均
    if today_count > 0:
        aver_day = "%.3f" % (today_totalTime / today_count)
    else:
        aver_day = 0

    item = {"id": id_domain,
            "url": url_domain,
            "name": name_domain,
            "lately": result_lately,
            "hour": aver_hour,
            "count_timeout_hour": count_timeout_hour,
            "count_httpCodeError_hour": count_httpCodeError_hour,
            "day": aver_day,
            "count_timeout_day": count_timeout_day,
            "count_httpCodeError_day": count_httpCodeError_day}
    return item


@gzip_page
def getDomainDetail(request, id):
    # 域名详细页面
    try:
        domain = Domain.objects.get(id=id)
        # ips=Result.objects.filter(domain__id=id).values("ipaddr").distinct()
        # print(ips)
        params = {"domain": domain}
        return render_to_response('domainDetail.html', params, RequestContext(request))
    except Exception as e:
        print(e.args)
        raise Http404("")


from django.forms.models import model_to_dict


@gzip_page
def getDomainTimeData(request, id):
    # 域名响应时间
    try:
        # 获取缓存数据
        cache_key = "domain_time_%s" % id
        cache_data = cache.get(cache_key, None)
        if cache_data:
            param = cache_data
        else:

            domain = Domain.objects.get(id=id)
            # 最近2天时间
            totay_lately = datetime.now() - timedelta(days=2)
            responseTimes = ResponseTime.objects.filter(domain=domain, create_time__gte=totay_lately).order_by(
                "create_time").values("slowest_ip__address", "slowest_ip__ip", "fastest_ip__address", "fastest_ip__ip",
                                      "slowest_time", "fastest_time", "slowest_size", "fastest_size"
                                      , "slowest_speed", "fastest_speed", "slowest_redirect", "fastest_redirect",
                                      "create_time").all()

            list = []
            for item in responseTimes:
                create_time = item['create_time']
                item['create_time'] = create_time.strftime('%Y-%m-%d %H:%M:%S')
                item_json = json.dumps(item)
                list.append(item_json)

            param = {"json": list,
                     "isOk": 1}
            cache.set(cache_key, param, settings.cache_time)
    except Exception as e:
        print(e.args)
        param = {"error": e.args,
                 "isOk": 0}
    finally:
        json_str = json.dumps(param)
        response = HttpResponse(status=200)
        response.write(json_str)
        return response


@gzip_page
def getDomainStatusData(request, id):
    # 域名状态数据
    try:
        cache_key = "domain_status_%s" % id
        cache_data = cache.get(cache_key, None)
        if cache_data:
            param = cache_data
        else:
            domain = Domain.objects.get(id=id)
            # 最近2天时间
            totay_lately = datetime.now() - timedelta(days=2)
            responseStatuss = ResponseStatus.objects.filter(domain=domain, create_time__gte=totay_lately).order_by(
                "create_time").values("ipaddr__address", "ipaddr__ip", "http_code", "create_time").all()

            list = []
            for item in responseStatuss:
                create_time = item['create_time']
                item['create_time'] = create_time.strftime('%Y-%m-%d %H:%M:%S')
                item_json = json.dumps(item)
                list.append(item_json)

            param = {"json": list,
                     "isOk": 1}
            cache.set(cache_key, param, settings.cache_time)
    except Exception as e:
        print(e.args)
        param = {"error": e.args,
                 "isOk": 0}
    finally:
        json_str = json.dumps(param)
        response = HttpResponse(status=200)
        response.write(json_str)
        return response


def getIP(request):
    '''识别广电私有IP'''
    try:
        ip = request.META.get('REMOTE_ADDR', '对不起，获取不到你的IP')

        params = {"ip": ip}
        return render_to_response('ip.html', params, RequestContext(request))
    except Exception as e:
        print(e.message)
