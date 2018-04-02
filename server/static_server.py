#! /usr/bin/env python
# -*- coding:utf-8 -*-
import json
import xlrd
import urllib2
import time
import os
import codecs

start_time = time.time()
file_path = "../config/static_config.xlsx"

def Excel2Json(file_path):
    if get_data(file_path) is not None:
        book = get_data(file_path)
        # 抓取所有sheet页的名称
        sheet = book.sheet_by_name("compute")
        row_0 = sheet.row(0)  # 第一行是表单标题
        nrows = sheet.nrows  # 行号
        ncols = sheet.ncols  # 列号
        result = []
	# 遍历所有行，将excel转化为json对象
        for i in range(nrows):
            if i == 0:
                continue
            tmp = {}
            # 遍历当前行所有列
            for j in range(ncols):
                # 获取当前列中文标题
                title_de = str(row_0[j])
                title_cn = title_de.split("'")[1].strip()
                # 获取单元格的值
                tmp[title_cn] = sheet.row_values(i)[j]
            result.append(tmp)
        #json_data = json.dumps(result, indent=4, sort_keys=True)#.decode('unicode_escape')
        return result


def get_data(file_path):
    """获取excel数据源"""
    try:
        data = xlrd.open_workbook(file_path)
        return data
    except Exception, e:
        print u'excel表格读取失败：%s' % e
        return None

json_data = Excel2Json(file_path)

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
data = []
for  i in json_data:
	iplist = get_ip(i['ip_range'])	
	for ip in iplist:
		static_data = {'vendor':i['vendor'],'model':i['model'],'region':i['region']}
		json_str = json.dumps(static_data)
		record = {}
		record['metric'] = 'static'
		record['endpoint'] = ip
		record['timestamp'] = int(time.time())
		record['step'] = 3600
		record['value'] = json_str
		record['counterType'] = 'GAUGE'
		record['tags'] = 'ip=%s' % ip
		data.append(record)
if data:
    print json.dumps(data).replace('\\', '');
