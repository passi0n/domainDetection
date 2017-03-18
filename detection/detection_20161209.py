#!/usr/bin/python
# -*- coding: utf8 -*-
import json
import logging
import os
import pycurl
import re
import subprocess
import time
import urllib.parse
import urllib.request
from datetime import datetime
from multiprocessing import Pool
from logging.handlers import TimedRotatingFileHandler

import pymysql
from curl import Curl

address = ''
host = "127.0.0.1"
user = "root"
password = "123456"
database = "monitor"


def getProtol(url):
    '''获取域名'''
    # print("="*74+"getDomain\n")
    if url.find(r"://") == -1:
        url = r"http://%s" % url
    result = urllib.parse.urlparse(url)
    # print(result[1])
    return result[0]


def getDomain(url):
    '''获取域名'''
    # print("="*74+"getDomain\n")
    if url.find(r"://") == -1:
        url = r"http://%s" % url
    result = urllib.parse.urlparse(url)
    # print(result[1])
    return result[1]


def getPath(url):
    '''获取url路径目标'''
    # print("="*74+"getPath\n")
    if url.find(r"://") == -1:
        url = r"http://%s" % url
    result = urllib.parse.urlparse(url)
    # print(result)
    return result[2]


def getIpLoc(ipstr):
    '''
        获取ip归属地
        :param ipstr: ip地址
        :return: 归属地
    '''
    try:
        # 数据库查询 未查到taobao查询并入库
        address_id = address = ''
        db = pymysql.connect(host=host, user=user, password=password, database=database, use_unicode=True,
                             charset="utf8")
        cursor = db.cursor()
        sql = "select * from domain_ip_address where ip='%s'" % ipstr
        cursor.execute(sql)
        data = cursor.fetchone()
        # print(data)

        if data is None:
            url = 'http://ip.taobao.com/service/getIpInfo.php?ip=%s' % ipstr
            req = urllib.request.urlopen(url, timeout=15)
            content = req.read()
            # print("xxxxx",ipstr, content)
            content_json = json.loads(content.decode("gb2312"))
            # print("xxxxx",ipstr,content_json)
            if content_json['code'] == 1:
                error_msg_ip = '''
                        无法查询到IP归属
                        '''
                return error_msg_ip

            address = '%s %s %s %s' % (
                content_json['data']['country'],
                content_json['data']['region'],
                content_json['data']['city'],
                content_json['data']['isp']
            )

            sql = "insert into domain_ip_address (ip,address,create_time,status) values ('%s','%s','%s','1')" % (
                ipstr, str(address), datetime.now())
            ##print(sql)
            cursor.execute(sql)
            db.commit()
            sql = "select * from domain_ip_address where ip='%s'" % ipstr
            cursor.execute(sql)
            data = cursor.fetchone()
            # print(data)
            address_id = data[0]
        else:
            # 数据库存在记录即返回
            address_id = data[0]
            address = data[2]
    except Exception as e:
        logging.exception("def getIpLoc(%s) Exception %s" % (ipstr, e.args))
    finally:
        try:
            cursor.close()
            db.close()
        except:
            pass
        return address_id, address


def dig(url):
    '''
        dig命令
        返回ip地址
    '''
    domain = getDomain(url)

    # print("=" * 74 + "dig\n")
    script = "dig @100.127.111.1 %s +short" % domain
    # print("script:"+script)
    p = subprocess.Popen(script, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    lines = p.stdout.readlines()
    logging.info("%s dig result: %s" % (url, lines))

    a_list = []
    pattern = re.compile(r"\d+\.\d+\.\d+\.\d+")

    for line in lines:
        # str_line = line.decode('utf-8').replace('\r\n', '')
        str_line = line.replace('\r\n', '').strip()
        match = pattern.match(str_line)
        if match:
            a_list.append(str_line)
    # print(url,a_list)
    return a_list


def pycurl_detection(url, ip):
    '''
        探测程序
        :param url: 请求地址
        :param ip: dig ip
        :return: 状态码，响应时间
    '''
    try:
        domain = getDomain(url)
        # protol=getProtol(url)
        # path = getPath(url)

        # print("="*74+"pycurl_detect ion\n")
        new_url = url.replace(domain, ip)
        # print("url:"+url,"ip:"+ip)
        # print("domain:"+domain)
        # print("path:"+path)
        # print("new_url:"+new_url)

        header = [
            'GET %s HTTP/1.1' % path,
            'Host: %s' % domain,
            'Accept: */*',
            'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language: zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding: gzip, deflate',
            'Connection: keep-alive',
            'Cache-Control: no-cache',
            'User-Agent: Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
        ]
        if url.find("baidu.com") > 0:
            header.pop(len(header) - 1)
        c = Curl(fakeheaders=header)
        c.get(new_url)
        http_code = c.get_info(pycurl.HTTP_CODE)  # 返回的HTTP状态码
        # print("返回的HTTP状态码：%s"%http_code)

        size_download = c.get_info(pycurl.SIZE_DOWNLOAD)  # 下载数据包大小
        speed_download = c.get_info(pycurl.SPEED_DOWNLOAD)  # 平均下载速度
        file_time = c.get_info(pycurl.INFO_FILETIME)  # 检索文档的远程时间

        namelookup_time = c.get_info(pycurl.NAMELOOKUP_TIME)  # DNS解析所消耗的时间
        content_time = c.get_info(pycurl.CONNECT_TIME)  # 建立连接所消耗的时间
        pretransfer_time = c.get_info(pycurl.PRETRANSFER_TIME)  # 从建立连接到准备传输所消耗的时间
        starttransfer_time = c.get_info(pycurl.STARTTRANSFER_TIME)  # 从建立连接到传输开始消耗的时间
        total_time = c.get_info(pycurl.TOTAL_TIME)  # 传输结束所消耗的总时间
        redirect_time = c.get_info(pycurl.REDIRECT_TIME)  # 重定向所消耗的时间

        redirect_url = c.get_info(pycurl.REDIRECT_URL)  # 重定向url
        redirect_count = c.get_info(pycurl.REDIRECT_COUNT)  # 重定向次数

        primary_ip = ''  # c.get_info(pycurl.PRIMARY_IP)
        primary_port = ''  # c.get_info(pycurl.PRIMARY_PORT)
        local_ip = ''  # c.get_info(pycurl.LOCAL_IP)
        local_port = ''  # c.get_info(pycurl.LOCAL_PORT)

        info = c.info()

        header = c.header()
        str = '''
        url:%s,ip:%s,size_download:%s,speed_download:%s,file_time:%s,redirect_count:%s,
        namelookup_time:%s,content_time:%s,pretransfer_time:%s,starttransfer_time:%s,total_time:%s,redirect_time:%s
        redirect url:%s,count:%s
        primary ip:%s,port:%s
        local ip:%s,port:%s
        info:%s
        ''' % (url, ip, size_download, speed_download, file_time, redirect_count,
               namelookup_time, content_time, pretransfer_time, starttransfer_time, total_time, redirect_time,
               redirect_url, redirect_count,
               primary_ip, primary_port,
               local_ip, local_port,
               info)
        print(str)

        '''
        #print("传输结束所消耗的总时间：%s" % total_time)
        namelookup_time=c.get_info(pycurl.NAMELOOKUP_TIME)  # DNS解析所消耗的时间
        #print("DNS解析所消耗的时间：%s" % namelookup_time)
        content_time=c.get_info(pycurl.CONNECT_TIME)  # 建立连接所消耗的时间
        #print("建立连接所消耗的时间：%s" % content_time)
        pretransfer_time=c.get_info(pycurl.PRETRANSFER_TIME)  # 从建立连接到准备传输所消耗的时间
        #print("从建立连接到准备传输所消耗的时间：%s" % pretransfer_time)
        starttransfer_time=c.get_info(pycurl.STARTTRANSFER_TIME)  # 从建立连接到传输开始消耗的时间
        #print("从建立连接到传输开始消耗的时间：%s" % starttransfer_time)
        redirect_time=c.get_info(pycurl.REDIRECT_TIME)  # 重定向所消耗的时间
        #print("重定向所消耗的时间：%s" % redirect_time)
        size_upload=c.get_info(pycurl.SIZE_UPLOAD)  # 上传数据包大小
        size_download=c.get_info(pycurl.SIZE_DOWNLOAD)  # 下载数据包大小
        speed_download=c.get_info(pycurl.SPEED_DOWNLOAD)  # 平均下载速度
        speed_upload=c.get_info(pycurl.SPEED_UPLOAD)  # 平均上传速度
        header_size=c.get_info(pycurl.HEADER_SIZE)  # HTTP头部大小
        
        print(c.body())
        print('=' * 74 + '\n')
        print(c.header())
        print('=' * 74 + '\n')
        import pprint
        pprint.pprint(c.info())
        print(c.get_info(pycurl.OS_ERRNO))
        print(c.info()['os-errno'])
        '''

    except Exception as e:
        str = "def pycurl_detection(%s,%s) Exception %s" % (url, ip, e.args)
        print(str)
        logging.exception(str)
        return -1, -1, 0, 0, 0
    finally:
        c.close()
    return http_code, "%.3f" % total_time, size_download, speed_download, redirect_count


def processing(data):
    # 域名探测进程
    try:

        domain_id = data[0]
        org_url = data[1]
        logging.info("域名探测进程 id:%s,url:%s" % (domain_id, org_url))
        time.sleep(1)

        url = org_url.replace('https://', '').replace('http://', '')
        # dig ip列表
        ip_list = dig(url)
        time.sleep(1)
        # print(ip_list)

        # 数据库查询 未查到taobao查询并入库
        db = pymysql.connect(host=host, user=user, password=password, database=database, use_unicode=True,
                             charset="utf8")
        cursor = db.cursor()
        for ip in ip_list:
            # curl探测
            http_code, total_time, size_download, speed_download, redirect_count = pycurl_detection(url, ip)
            # ip归属地
            address_id, address = getIpLoc(ip)
            logging.info("%s %s result：http_code %s,total_time %s,address %s"
                         % (url, ip, http_code, total_time, address))
            # 记录入库
            sql = "insert into domain_result (ipaddr_id,domain_id,http_code,total_time,remark,create_time,status,size_download, speed_download, redirect_count) " \
                  "values ('%s','%s','%s','%s','','%s','1','%s','%s',%d)" \
                  % (address_id, domain_id, http_code, total_time, datetime.now(), size_download, speed_download,
                     redirect_count)
            # logging.info(sql)
            cursor.execute(sql)
            db.commit()
    except Exception as e:
        logging.exception("def processing(%s) Exception %s" % (data, e.args))
    finally:
        try:
            cursor.close()
            db.close()
        except:
            pass


dir = "log"
if not os.path.isdir(dir):
    os.mkdir(dir)

path = dir + "/log"
handler = TimedRotatingFileHandler(path,
                                   when="H",
                                   interval=1,
                                   backupCount=24)
# 设置后缀名称，跟strftime的格式一样
handler.suffix = "%Y%m%d-%H%M%S"
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    handlers=(handler,),
                    )

if __name__ == "__main__":
    try:
        total_time = 2 * 60
        while True:
            old_time = datetime.now()
            str_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logging.info("main do running,parent process pid is %s" % os.getpid())

            # 从库中获取数据
            db = pymysql.connect(host=host, user=user, password=password, database=database, use_unicode=True,
                                 charset="utf8")
            cursor = db.cursor()
            sql = "select id,url from domain_domain"
            cursor.execute(sql)
            data = cursor.fetchall()
            cursor.close()
            db.close()

            # 进程池
            p = Pool(len(data))
            new_data = []
            for item in data:
                p.apply_async(processing, args=(item,))
            logging.info('Waiting for all subprocesses done...')
            p.close()
            p.join()
            logging.info('All subprocesses done.')
            logging.info('\n' * 3)
            print("All subprocesses done.")

            offset_time = datetime.now() - old_time
            # print(offset_time.seconds)
            # print(type(offset_time.seconds))
            sleep_time = total_time - offset_time.seconds
            print(sleep_time)
            logging.info("休眠时间：%s" % sleep_time)
            if sleep_time > 0:
                # 5分钟时间间隔
                time.sleep(sleep_time)
    except Exception as e:
        logging.exception("main exception ", e.args)
        pass
