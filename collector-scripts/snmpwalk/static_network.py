#! /usr/bin/env python
# -*- coding:utf-8 -*-

import json
import xlrd
import urllib2
import time
import os
import codecs

start_time = time.time()
file_path = "./static_config.xlsx"

def Excel2Json(file_path):
    if get_data(file_path) is not None:
        book = get_data(file_path)
        # 抓取所有sheet页的名称
        sheet = book.sheet_by_name("network")
        row_0 = sheet.row(0)  # 第一行是表单标题
        nrows = sheet.nrows  # 行号
        ncols = sheet.ncols  # 列号

        result = {}  # 定义json对象
        result["title"] = file_path  # 表单标题
        result["rows"] = nrows  # 行号
        result["children"] = []  # 每一行作为数组的一项
        # 遍历所有行，将excel转化为json对象
        for i in range(nrows):
            if i == 0:
                continue
            tmp = {}
            # 遍历当前行所有列
            for j in range(ncols):
                # 获取当前列中文标题
                title_de = str(row_0[j]).decode('unicode_escape')
                title_cn = title_de.split("'")[1]
                # 获取单元格的值
                tmp[title_cn] = sheet.row_values(i)[j]
            result["children"].append(tmp)
        json_data = json.dumps(result, indent=4, sort_keys=True).decode('unicode_escape')

        return json_data


def get_data(file_path):
    """获取excel数据源"""
    try:
        data = xlrd.open_workbook(file_path)
        return data
    except Exception, e:
        print u'excel表格读取失败：%s' % e
        return None

json_data = Excel2Json(file_path)
print json_data
##ip rules
def ip2num(ip):
    ip=[int(x) for x in ip.split('.')]
    return ip[0] <<24 | ip[1]<<16 | ip[2]<<8 |ip[3]

def num2ip(num):
    return '%s.%s.%s.%s' %( (num & 0xff000000) >>24,
                            (num & 0x00ff0000) >>16,
                            (num & 0x0000ff00) >>8,
                            num & 0x000000ff )
def get_ip(ip):
    if "," in ip:
        ip_range = ip.split(',')
        iplist = []
        for i in ip_range:
            if '-' in i:
                start,end = [ip2num(x) for x in i.split('-') ]
                ipl =  [ num2ip(num) for num in range(start,end+1) if num & 0xff ]
                iplist += ipl
            else:
                ipl = [i]
                iplist += ipl
        return iplist
    elif '-' in ip and ',' not in ip:
        start,end = [ip2num(x) for x in ip.split('-') ]
        ipl =  [ num2ip(num) for num in range(start,end+1) if num & 0xff ]
        return ipl
    else:
        return [ip]

